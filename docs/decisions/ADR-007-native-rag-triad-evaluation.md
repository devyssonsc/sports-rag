# ADR-007: Native RAG Triad Evaluation (LLM-as-a-judge)

- **Status:** Accepted
- **Date:** 2026-08
- **Decision Makers:** Sports RAG Project

---

# Context

The RAG pipeline was complete (ingestion → chunking → embeddings → retrieval →
LLM) but there was no way to answer the question that matters most: *is it any
good, and does a change make it better or worse?* Without measurement, pipeline
tweaks (chunking, retrieval, prompting) are guided by "it looks better" rather
than evidence.

The DeepLearning.AI course *Building and Evaluating Advanced RAG* teaches the
**RAG Triad** — three complementary metrics that together detect hallucinations
and localize where a RAG fails:

- **Context Relevance** (question ↔ context): did retrieval bring relevant chunks?
- **Groundedness** (context ↔ answer): is the answer supported by the context?
- **Answer Relevance** (question ↔ answer): does the answer address the question?

The course computes them with **TruLens** feedback functions wired into
**LlamaIndex query engines**. This project's stack is different: retrieval is our
own `RetrievalService` over Qdrant + Postgres, generation is Together AI
(`gpt-oss-120b`), and there is no LlamaIndex query engine to instrument.

---

# Decision

Implement the RAG Triad **natively**, as an offline evaluation harness, using our
own `LLMService` as an **LLM-as-a-judge** — not TruLens, not LlamaIndex query
engines.

Concretely (`backend/evaluation/`):

- **Judge** (`judge.py`): three feedback functions, each a prompt asking the LLM
  to return a 0–1 score plus a chain-of-thought reason. Context Relevance scores
  each retrieved chunk and averages (the course's `np.mean`).
- **Harness** (`harness.py`): runs the *real* pipeline (retrieve → prompt →
  generate) per question, then judges the three metrics concurrently.
- **Frozen corpus** (`corpus.py`): snapshots the whole article set (ids + counts)
  so experiments stay comparable, and samples N random articles with full content
  for grounded question authoring.
- **Frozen question set** (`questions.txt`): a stable set of curated questions.
- **Leaderboard** (`leaderboard.py`): per-run detail + an appended comparison row.
- **CLI** (`run_eval.py`): `sample` / `run` / `board`.

The harness lives outside the API request path and reuses the production services
unchanged, so every experiment is measured on the real pipeline.

`LLMService.generate` gains an optional, backward-compatible `temperature`
parameter; the judge uses `temperature=0` for reproducibility while production
chat behaviour is unchanged.

## Judge model

For now the same model that generates answers (`gpt-oss-120b`) also judges them.
This is simpler and good enough to start; using a distinct judge model later
means passing a second `LLMService`, with no other change.

---

# Rationale

- **Stack fit.** TruLens' prebuilt recorders instrument LlamaIndex/LangChain
  objects we do not use. Adapting the *concepts* to our services is less coupling
  than bending our pipeline to fit an evaluation framework.
- **Learning goal.** Building the feedback functions by hand (the focus of the
  course's Lesson 2) is the point — understanding *how* LLM-as-a-judge works, not
  treating it as a black box.
- **Reuse.** The judge is our existing `LLMService`; no new provider, no new
  dependency.
- **Comparability.** A frozen corpus + frozen questions + a leaderboard turn
  "seems better" into a measured delta.

---

# Alternatives Considered

## TruLens + LlamaIndex query engines (the course's approach)

### Advantages
- Prebuilt RAG Triad feedback functions and a Streamlit dashboard.
- Battle-tested metric implementations.

### Disadvantages
- Assumes LlamaIndex/LangChain query engines; our retrieval and generation are
  custom services over Qdrant + Together.
- Adds a heavy dependency and an instrumentation layer to fit a shape we do not
  have.

Decision: Rejected — poor fit for this stack, and it hides the mechanism the
project is trying to learn.

## Ragas / other eval libraries

### Advantages
- Ready-made RAG metrics.

### Disadvantages
- Same coupling/opacity trade-off; another dependency to learn instead of the
  metrics themselves.

Decision: Rejected for the same reasons.

## Manual / human evaluation only

### Advantages
- No tooling; highest-fidelity judgement.

### Disadvantages
- Does not scale to repeated experiments across a fixed question set; slow
  feedback loop.

Decision: Rejected as the primary method (still useful for spot checks).

---

# Consequences

Positive:

- A repeatable measurement loop: build → evaluate → compare → improve.
- Experiments are isolated and comparable (frozen corpus + questions).
- No new dependency; the judge is the existing LLM.
- First results already actionable (see below).

Negative:

- **LLM-as-a-judge is noisy.** Scores can be strict about literal phrasing (an
  early run penalized "2026 UEFA Super Cup" vs the context's "European Super
  Cup"). Reasons (`with_cot_reasons`) mitigate this by making each score
  inspectable.
- **Same-model bias.** The generator judging itself can be lenient; a separate
  judge model is a future option.
- **Context Relevance is precision-oriented.** It is a per-chunk mean, so it is
  biased against larger `top_k` (more chunks dilute the average) and does not
  measure recall. Optimizing coverage would need a different metric (e.g.
  recall@k against ground-truth). This is a known limitation, not a bug.
- **Cost/latency.** Each run makes many judge calls (roughly
  questions × (2 + top_k)).

---

# Results (experiment log)

Corpus: 494 articles / 1281 chunks. Question set: 20 (14 single-article,
6 thematic). Retrieval top-5.

| Experiment    | Context Rel. | Groundedness | Answer Rel. | Outcome |
|---------------|:-----------:|:------------:|:-----------:|---------|
| baseline      | 0.393       | 0.929        | 0.905       | reference |
| e5-instruct   | 0.464       | 0.968        | 0.966       | **adopted** |
| top10 (k=10)  | 0.322       | 0.968        | 0.961       | rejected |
| rerank        | 0.484       | 0.989        | 0.961       | **adopted (production)** |
| rerank-window | 0.519       | 0.943        | 0.945       | rejected (trade-off) |
| hybrid-rerank | 0.455       | 0.990        | 0.942       | rejected (no gain) |

- **baseline** exposed retrieval as the bottleneck (low Context Relevance).
- **e5-instruct** (e5 instruction prefix on query embeddings) improved all three
  and recovered a full retrieval miss. Adopted.
- **top10** confirmed Context Relevance is precision-oriented: more chunks lowered
  the mean without improving answers. Rejected; `top_k` stays 5.
- **rerank** (local cross-encoder, retrieve-then-rerank) raised Context Relevance
  and Groundedness at no API cost. Adopted as the production retrieval default
  (see ADR-008).
- **rerank-window** (sentence-window ±1) raised Context Relevance but lowered
  Groundedness (0.99 → 0.94): widening chunks adds neighbour text that does not
  always support the answer. Not adopted — Groundedness is the anti-hallucination
  metric.
- **hybrid-rerank** (dense + BM25 fused with RRF) did not improve; Context
  Relevance dipped. The question set is semantic-heavy, where dense e5 already
  wins and BM25 adds lexical noise. Kept as an eval capability, not adopted.

---

# Future Review

Revisit if:

- a distinct, stronger judge model is warranted to reduce same-model bias;
- ground-truth answers are introduced, enabling recall/precision metrics beyond
  the LLM-judged triad;
- the harness needs to gate CI rather than run ad hoc.

Until then, the native RAG Triad harness is the official evaluation method for
Sports RAG.
