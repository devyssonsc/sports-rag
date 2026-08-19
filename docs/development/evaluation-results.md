# Evaluation & Benchmark Results

Consolidated record of the RAG evaluation work: the setup, every experiment run,
the results, and the conclusions. Decisions live in the ADRs (007–010); this is
the results log. How to run the harness: `backend/evaluation/README.md`.

---

## Setup

- **Corpus (frozen):** 494 articles / 1281 chunks (chunk size 350, overlap 50).
- **Questions (frozen):** 20 — 14 single-article factual, 6 thematic (multi-source).
  See `backend/evaluation/questions.txt`.
- **Harness:** native RAG Triad (LLM-as-a-judge) + recall@k, `backend/evaluation/`.
  Offline; reuses the production services, so every experiment is measured on the
  real pipeline (ADR-007).
- **Production pipeline (retrieval):** query embedded with the e5 instruction
  prefix → dense cosine search (top-20 candidate pool) → local cross-encoder
  rerank → top-5 (ADR-008).

## Metrics

RAG Triad (0–1, LLM-judged, each with a chain-of-thought reason):

- **Context Relevance** — question ↔ each retrieved chunk (mean). Retrieval
  *precision*. A per-chunk mean, so biased against larger `top_k`; not recall.
- **Groundedness** — context ↔ answer. Anti-hallucination (is the answer supported?).
- **Answer Relevance** — question ↔ answer. Does the answer address the question?

**recall@k** — deterministic (no LLM): fraction of the ground-truth articles for a
question that appear among the retrieved ones. Measures *coverage*. Ground-truth is
`backend/evaluation/ground_truth.json` (authored source articles — conservative, so
true recall ≥ measured). Article ids are stable across reindexes; chunk ids are not.

> **Judge caveat:** absolute triad values depend on the judge model, so **only
> comparisons made with the same judge are valid**. Each leaderboard row records
> its judge. Rows below labeled "gpt-oss (self)" used the generator as judge; the
> judge was later made independent (ADR-010).

---

## Experiment log — retrieval (judge: gpt-oss-120b, == generator)

| Experiment    | Context | Grounded | Answer | Verdict |
|---------------|:------:|:-------:|:-----:|---------|
| baseline      | 0.393  | 0.929   | 0.905 | reference |
| **e5-instruct** | 0.464 | 0.968 | 0.966 | **adopted** — instruction prefix on the query only |
| top10 (k=10)  | 0.322  | 0.968   | 0.961 | rejected — more chunks dilute the precision mean |
| **rerank**    | 0.484  | 0.989   | 0.961 | **adopted (production)** — retrieve-then-rerank (ADR-008) |
| rerank-window | 0.519  | 0.943   | 0.945 | rejected — sentence-window raised context but lowered groundedness |
| hybrid-rerank | 0.455  | 0.990   | 0.942 | rejected — dense+BM25 (RRF) added lexical noise |
| jina-350      | 0.439  | 0.975   | 0.955 | rejected — local long-context model, weaker (ADR-009) |
| jina-1024     | 0.430  | 0.931   | 0.958 | rejected — larger chunks did not help; groundedness down |

**Takeaway:** only e5-instruct and rerank improved. Everything aimed at "more/larger
context" (top10, sentence-window, hybrid, long-context chunks) was neutral or worse,
and tended to hurt groundedness. This corpus + question set reward **precise,
focused retrieval**.

## Recall diagnostics (judge-independent; retrieval-only)

| Config                         | recall |
|--------------------------------|:------:|
| dense pool@20                  | 0.867  |
| dense top-5                    | 0.771  |
| rerank top-5 (production)      | 0.758  |
| hybrid top-5 / pool@20         | 0.767 / 0.883 |
| HyDE top-5 / pool@20           | 0.742 / 0.833 |
| multi-query top-5 / pool@20    | 0.758 / 0.879 |

**Takeaway:** top-5 recall is stuck ~0.76 across every technique; ~13% of
ground-truth articles are missing even from the top-20 pool. The reranker trades a
little recall for precision (0.771 → 0.758). The recall gap is **structural**
(thematic questions need >5 sources; some articles simply don't match semantically),
not fixed by hybrid or query rewriting.

### Query strategies (ADR context, not adopted)

- **HyDE** (embed a hypothetical LLM answer): **worse** — the model does not know
  the recent, specific facts, so it fabricates a misleading hypothetical (e.g. for
  "which club did Tielemans join?" it invented Royal Antwerp / €15M / Leicester vs
  the real Man Utd / £35M / Aston Villa).
- **Multi-query** (rephrase into variants, fuse): robust (unlike HyDE) but marginal
  (+1.2pp pool recall, flat at top-5).

## Judge comparison (ADR-010) — same config (e5 + rerank)

The judge-independent recall stayed **0.758** across all three, confirming only the
judge changed:

| Judge                              | Context | Grounded | Answer |
|------------------------------------|:------:|:-------:|:-----:|
| gpt-oss-120b (== generator)        | 0.484  | 0.989   | 0.961  |
| Qwen3.5-9B (independent, small)    | 0.524  | 1.000   | 1.000  |
| **Llama-3.3-70B (independent)**    | 0.531  | 0.9925  | 1.000  |

- Same-model was **not** inflation — gpt-oss was slightly harder on itself.
- Qwen3.5-9B **rubber-stamped** (flat 1.0) — too small to discriminate.
- Llama-3.3-70B discriminates (groundedness < 1.0; caught an unsupported claim) —
  **adopted** as the judge. No serverless reasoning judge is available on the
  account.

## Coherent leaderboard (judge: Llama-3.3-70B)

Key configs re-baselined under the independent judge (all with e5-instruct on):

| Config (e5-instruct on) | Context | Grounded | Answer | Recall |
|-------------------------|:------:|:-------:|:-----:|:-----:|
| dense (no rerank)       | 0.541  | 0.930   | 1.000 | 0.771 |
| **rerank (production)** | 0.532  | 0.980   | 1.000 | 0.758 |
| rerank + window         | 0.550  | 0.983   | 1.000 | 0.758 |
| rerank + hybrid         | 0.513  | 0.978   | 1.000 | 0.729 |

Two findings the stronger judge revealed:

1. **Rerank's value is groundedness, not precision.** Under Llama, rerank's context
   relevance is level with dense (0.532 vs 0.541) but groundedness jumps 0.930 →
   0.980. The reranker fronts the supporting chunks, so the answer is better grounded
   — that (not context relevance) is why it is kept in production.
2. **A verdict changed: sentence-window.** Under the gpt-oss judge, window *lowered*
   groundedness (0.989 → 0.943) and was rejected. Under Llama it does **not** — it is
   marginally better on both (context 0.550, groundedness 0.983). The earlier penalty
   was partly a weak-judge artifact. Window is now a neutral, viable option (no longer
   harmful), though it adds latency; production stays on plain rerank for simplicity.

Hybrid remains the weakest (lowest context and recall) — consistent across judges.

---

## Conclusions

1. **The pipeline is well-optimized.** e5-instruct + rerank is the best config; the
   answers are strong (high groundedness and answer relevance).
2. **Retrieval is near a structural ceiling** for this corpus/questions — eight
   techniques, only two helped. Further retrieval gains have diminishing returns.
3. **Two lenses are needed.** Context Relevance (precision) alone hid a recall gap;
   recall@k (coverage) revealed it and re-judged hybrid honestly.
4. **The judge is part of the measurement.** Absolute scores depend on it; only
   same-judge comparisons are valid, and a capable judge matters as much as an
   independent one.

## Decision records

- ADR-007 — native RAG Triad evaluation (LLM-as-a-judge)
- ADR-008 — local cross-encoder reranking (adopted)
- ADR-009 — embedding model: stay on e5 (long-context evaluated and rejected)
- ADR-010 — independent judge model
