# ADR-008: Local Cross-Encoder Reranking

- **Status:** Accepted
- **Date:** 2026-08
- **Decision Makers:** Sports RAG Project

---

# Context

The RAG Triad harness (ADR-007) identified retrieval precision (Context
Relevance) as the pipeline's bottleneck. Dense embedding search (a bi-encoder)
scores query and chunk independently, which is fast but approximate: in the
top-5, often only 1–2 chunks were truly relevant.

A cross-encoder reranker reads the (query, chunk) pair together and judges
relevance far more accurately. The standard pattern is retrieve-then-rerank:
fetch a larger candidate pool by embeddings (recall), then rerank down to the
final top-k (precision). The reranker cannot be precomputed, so it runs only over
the candidate pool at query time.

---

# Decision

Add reranking and adopt it as the **production retrieval default**, using a
**local cross-encoder via fastembed** (ONNX, no torch): `retrieve_context` fetches
a candidate pool (default 20) then reranks to top-k (default 5).

- Model: `Xenova/ms-marco-MiniLM-L-6-v2` (English, ~80MB), override via
  `RERANK_MODEL`. The corpus is English.
- Enabled by the presence of a `rerank_service` on `RetrievalService`. Production
  wires one in (singleton via `lru_cache`, model loaded once); the eval harness
  toggles it by constructing the service or not.
- Model weights are cached in a mounted volume (`FASTEMBED_CACHE_PATH`) so they
  download once (see docker-compose).

Measured impact (e5-instruct → rerank): Context Relevance 0.464 → 0.484,
Groundedness 0.968 → 0.989, Answer Relevance ~0.96, latency unchanged (local).

---

# Alternatives Considered

## Together dedicated rerank endpoint

Together's rerank models (`Salesforce/Llama-Rank-V1`,
`mixedbread-ai/mxbai-rerank-large-v2`) are **not serverless** — each needs a
provisioned dedicated endpoint, which requires contacting Together and is billed
per hour while running.

Decision: Rejected. Operational friction and ongoing cost for a learning project,
versus a local model that is free at runtime and good enough.

## LLM-as-a-reranker (reuse the generation LLM)

Prompt the LLM to score candidates. No new dependency, but it would confound the
evaluation: the judge is the same model, so Context Relevance would partly measure
the model agreeing with its own ranking. Also slower (LLM latency per query).

Decision: Rejected — measurement bias and latency.

## Local cross-encoder via sentence-transformers (torch)

Works, but pulls torch/transformers (~1–2GB), a heavy addition to a lean image.

Decision: Rejected in favour of fastembed (ONNX, from the Qdrant ecosystem already
in use), which is far lighter and installs on Python 3.14.

---

# Consequences

Positive:

- Best-measured retrieval config; adopted in production with no API cost and
  unchanged latency.
- Reranking is independent of the judge model, so eval scores stay honest.
- The dependency (fastembed) also powers the BM25 sparse embedder used by the
  hybrid experiment.

Negative:

- New dependency (`fastembed` + `onnxruntime`) and a model download on first use;
  mitigated by the cache volume.
- The candidate pool (20) means more work per query than a plain top-5 fetch
  (negligible for Qdrant at this scale).
- CPU cost of the cross-encoder per request; offloaded via `asyncio.to_thread`
  so it does not block the event loop.

---

# Future Review

Revisit if a stronger/multilingual reranker is needed (e.g. `bge-reranker-v2-m3`),
if candidate-pool size needs tuning, or if a managed reranker becomes serverless
and cheaper than running one locally.
