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
- `results/`, `corpus_snapshot.json`, `sample_articles.md` — generated, gitignored.
