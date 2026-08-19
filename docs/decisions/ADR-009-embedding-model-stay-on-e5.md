# ADR-009: Embedding Model — Stay on e5-large-instruct (long-context embeddings evaluated and rejected)

- **Status:** Accepted
- **Date:** 2026-08
- **Decision Makers:** Sports RAG Project

---

# Context

While planning a chunking sweep (varying `chunk_size`/`overlap` to see the effect
on retrieval quality), we hit a hard limit: the production embedding model
`intfloat/multilingual-e5-large-instruct` has a **512-token maximum**. The
Together API does not truncate above it — it **rejects the request with HTTP 400**
(verified empirically: a ~1300-token input returned *"This model's maximum context
length is 512 tokens"*). So chunks cannot grow beyond ~512 tokens with this model.

Two further facts shaped the decision:

- **Together offers no long-context embedding model** — the only embedding models
  available on the account are `multilingual-e5-large-instruct` (512) and
  `BAAI/bge-base-en-v1.5` (512).
- To use larger chunks we would need a **long-context embedding model**, which on
  this stack means a **local** model via fastembed (already used for reranking and
  BM25). The candidate was `jinaai/jina-embeddings-v2-base-en` (8192-token context,
  768-dim, English, symmetric, runs on CPU, no API cost).

---

# Decision

**Keep `intfloat/multilingual-e5-large-instruct` (via Together) with the e5
instruction prefix on queries.** Do **not** switch to a local long-context
embedding model. Chunk size stays effectively capped at ~512 tokens (the 350/50
production default is comfortably within it).

---

# Evaluation

The switch was implemented and measured with the RAG Triad harness (20 questions,
top-5, same reranker), against the adopted e5 + rerank baseline:

| Config (retrieval)         | Context | Groundedness | Answer |
|----------------------------|:------:|:-----------:|:-----:|
| **e5 + rerank (350/50)**   | **0.484** | **0.989** | **0.961** |
| jina-350 (same chunk size) | 0.439  | 0.975       | 0.955  |
| jina-1024 (larger chunks)  | 0.430  | 0.931       | 0.958  |

- **jina is a weaker base model.** At the same chunk size, jina-350 lost on all
  three metrics — jina-v2-base (~137M params) is smaller than e5-large-instruct
  (~560M), and the switch also drops the e5 instruction-prefix gain (jina is
  symmetric).
- **Larger chunks did not help.** jina-1024 was no better than jina-350 on context
  relevance and **lower on groundedness** (0.975 → 0.931): bigger chunks put more
  text per chunk, some of it not supporting the answer.
- This is consistent with every earlier "more context" experiment (top_k=10,
  sentence-window, hybrid): this corpus and question set reward **precise, focused
  retrieval**, not larger context.

---

# Rationale

- The long-context direction did not deliver its goal (larger chunks helping) and
  regressed quality across the board.
- Groundedness (the anti-hallucination metric) is a priority for a RAG; jina
  lowered it.
- The embedding cost on Together for this corpus is negligible, so the "local /
  free embeddings" upside of jina does not outweigh the quality loss.

---

# Alternatives Considered

- **jina-embeddings-v2-base-en (local, 8192)** — evaluated (above). Rejected:
  weaker retrieval; larger chunks didn't help.
- **nomic-embed-text-v1.5 / jina-embeddings-v3 (local, 8192)** — v3 is heavier
  (~2.29 GB, slower on CPU, matters for per-query latency); not pursued after the
  v2 result showed the long-context direction itself did not pay off.
- **A different embedding provider with long context** (e.g. OpenAI
  text-embedding-3) — adds a new provider/key and dependency; out of scope given
  the negative result.

---

# Consequences

Positive:

- Production keeps the best-measured retrieval (e5 + instruction-prefixed queries
  + local cross-encoder rerank).
- No new heavy local model loaded per query; `/chat` latency unchanged.

Negative / constraints:

- **Chunk size is effectively capped at ~512 tokens** by the embedding model. To
  genuinely explore large chunks in the future, a long-context embedding model
  would be required — a separate, larger change (re-embed everything, likely a new
  vector dimension), justified only if a use case needs it.
- Embeddings remain a paid Together call (negligible at this scale).

The `reindex` command built for this work is kept — it is the base tool for any
future chunking or embedding-model experiment.

---

# Future Review

Revisit if a use case needs chunks well beyond 512 tokens, if a stronger
long-context embedding model becomes available (ideally serverless on Together, or
a local model that beats e5 on this eval), or if embedding API cost becomes
material at larger corpus scale.
