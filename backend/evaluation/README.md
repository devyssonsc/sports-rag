# Evaluation harness (RAG Triad)

Offline evaluation for the RAG pipeline, implemented natively (LLM-as-a-judge via
`LLMService`) — not TruLens. Design and rationale: `docs/decisions/ADR-007`.

Run everything **inside the backend container** (the `.env` hostnames `postgres`
/ `qdrant` only resolve there).

## The three metrics (RAG Triad)

Each is scored 0–1 by the LLM, with a chain-of-thought reason:

- **Context Relevance** — question ↔ each retrieved chunk (mean). Measures
  retrieval *precision*. NOTE: as a per-chunk mean it is biased against larger
  `top_k` and does **not** measure recall.
- **Groundedness** — context ↔ answer. Is the answer supported by the context, or
  hallucinated? The anti-hallucination metric.
- **Answer Relevance** — question ↔ answer. Does the answer address the question?

`None`/`NaN` for a metric means it could not be computed (e.g. no context
retrieved) — informative, not an error.

### Two more metrics for prompt work (ADR-011)

The RAG Triad is saturated for prompt engineering (Answer Relevance sits at 1.0 and
Context Relevance is retrieval-only), so two prompt-sensitive metrics were added:

- **Answer Quality** — LLM judge (independent, temp 0): a single 0..1 over
  conciseness, clarity, attribution and appropriate abstention. The primary signal
  when iterating on the prompt.
- **Citation** — deterministic (no LLM): the prompt numbers the sources and the
  answer must cite `[n]`. Scores valid / total markers and flags any marker that
  points to no real source (a fabricated citation). `None` when there is nothing to
  cite (a correct abstention).

Evaluation generation runs at **temperature 0** so a prompt change is the only thing
that moves the answer (production `/chat` is unaffected).

## Workflow

```bash
# 1. Freeze the corpus + sample N random articles to author questions from.
docker compose exec backend python -m evaluation.run_eval sample -n 20
#    -> writes corpus_snapshot.json (frozen full corpus) and sample_articles.md.
#    Then write questions in questions.txt (kept stable across experiments).

# 2. (Only for --hybrid) build the BM25 sparse index once.
docker compose exec backend python -m evaluation.run_eval index-sparse

# 3. Run an experiment (name it; results append to the leaderboard).
docker compose exec backend python -m evaluation.run_eval run -e baseline
docker compose exec backend python -m evaluation.run_eval run -e rerank --rerank

# 4. Compare all experiments.
docker compose exec backend python -m evaluation.run_eval board
```

## `run` flags (retrieval variations)

| Flag | Effect |
|------|--------|
| `-k, --limit N` | Final chunk count / retrieval top-k (default 5). |
| `--rerank` | Retrieve `--candidates` then cross-encoder rerank to top-k. |
| `--candidates N` | Candidate pool before reranking (default 20). |
| `--window N` | Sentence-window: widen each final chunk with ±N neighbours. |
| `--hybrid` | Fuse dense + BM25 (RRF). Requires `index-sparse` first. |
| `--hard` | Use the adversarial set (`questions_hard.json`: unanswerable, ambiguous, hard thematic) instead of the frozen 20. Its own baseline. |

Reranking, sentence-window and hybrid are toggled here for experiments;
production wires only reranking (via `dependencies.py`).

## Files

- `judge.py` — the three feedback functions (LLM-as-a-judge).
- `harness.py` — runs the real pipeline per question, judges concurrently.
- `corpus.py` — freeze corpus + sample articles.
- `leaderboard.py` — persist per-run detail + append the leaderboard row.
- `run_eval.py` — CLI.
- `_retry.py` — retry transient provider errors.
- `questions.txt` — the frozen question set (committed).
- `questions_hard.json` — the adversarial set (`--hard`): each entry has `text`,
  `answerable`, `kind` (committed).
- `results/`, `corpus_snapshot.json`, `sample_articles.md` — generated, gitignored.
