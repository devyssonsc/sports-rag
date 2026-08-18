# Project State

## Purpose

This document represents the current implementation status of the Sports RAG project.

Unlike the Project History, this document does not explain how the project evolved.
Unlike the Roadmap, this document does not describe future goals.

Its purpose is to provide an accurate snapshot of the current state of the project.

This document should be updated whenever a significant feature is completed.

---

# Project Summary

**Project:** Sports RAG

**Primary Goal**

Learn how modern Retrieval-Augmented Generation (RAG) systems are designed, implemented and evolved.

**Architecture**

Layered Architecture

Current layers:

- api
- services
- repositories
- models
- schemas
- dto

---

# Current Functionalities

## News Sources

Status: ðŸŸ¡ In Progress

The Feed domain has been fully replaced by NewsSource across all layers
(models, schemas, repositories, services, routers, dependencies and the
database migration). This transition was concluded in commit c80a6e3.

The multi-source discovery architecture is prepared to receive new
strategies without changing the rest of the pipeline.

Implemented

- Feed fully replaced by NewsSource across all layers
- NewsSource registration
- NewsSource listing
- NewsSource fetching
- SourceType with RSS, CRAWL and SITEMAP values (all functional)
- DiscoveryFactory selects the discovery strategy based on SourceType
- RSSDiscovery implements RSS discovery
- HtmlDiscovery implements CRAWL discovery for server-rendered HTML pages,
  selecting article links via a per-source regex (article_url_pattern)
- SitemapDiscovery implements SITEMAP discovery (XML / Google News sitemaps),
  filling published_at from the sitemap when available
- SourceArticle as the common DTO produced by every discovery strategy
- IngestionService independent from the discovery origin (consumes SourceArticle)
- CRAWL sources require a valid article_url_pattern, validated at creation
- Fetch triggers background ingestion (202 Accepted), then records
  last_fetched_at and logs the IngestionResult
- Article chunks are embedded in batched requests (one call per article)

Pending

- Crawl4AI (browser-based) discovery for JavaScript-rendered sites
  (planned as a separate CRAWL4AI source type)
- Additional discovery strategies
- Date normalization
- Metadata normalization

---

## Content Extraction

Status: ðŸŸ¢ Completed

Implemented

- Full article extraction
- Trafilatura integration

Pending

- Source-specific extraction improvements when necessary

---

## Text Cleaning

Status: ðŸŸ¢ Completed

Implemented

- Text normalization
- Whitespace cleanup
- Newline normalization

---

## Chunking

Status: ðŸŸ¢ Completed

Implemented

- Semantic chunking
- LlamaIndex SentenceSplitter
- Chunk persistence
- Configurable chunk size
- Configurable overlap

---

## Embeddings

Status: ðŸŸ¢ Completed

Implemented

- Document embeddings
- Query embeddings
- Together AI integration
- Asymmetric e5 usage: passages embedded as raw text, queries prefixed with the
  e5 instruction (`Instruct: {task}\nQuery: {text}`). This alignment was
  validated by the evaluation harness (see Evaluation) and improved retrieval.

---

## Vector Database

Status: ðŸŸ¢ Completed

Implemented

- Qdrant integration
- Automatic collection creation
- Vector insertion
- Similarity search

---

## Retrieval

Status: ðŸŸ¢ Completed

Implemented

- Semantic search (cosine similarity over Qdrant)
- Query embedded via `embed_query` (e5 instruction prefix), documents as raw text
- Cross-encoder reranking in production: retrieve-then-rerank (pool of 20 →
  top-5) via a local fastembed model (ADR-008)
- Chunk recovery
- Metadata recovery
- Ranked context (top-5)

Available as eval-only capabilities (not in the production path): sentence-window
neighbour expansion and hybrid dense + BM25 retrieval (RRF fusion).

---

## Prompt Generation

Status: ðŸŸ¢ Completed

Implemented

- PromptBuilderService
- Context injection

---

## LLM

Status: ðŸŸ¢ Completed

Implemented

- Together AI integration
- GPT-OSS model support

---

## Chat

Status: ðŸŸ¢ Completed

Implemented

- Complete RAG pipeline
- Answer generation
- Source attribution

---

## Evaluation (RAG Triad)

Status: ðŸŸ¡ In Progress

The RAG Triad (Context Relevance, Groundedness, Answer Relevance) is implemented
natively as an offline LLM-as-a-judge harness (`backend/evaluation/`), not via
TruLens. See ADR-007. It reuses the production services, so experiments are
measured on the real pipeline.

Implemented

- LLM-as-a-judge feedback functions for the three metrics, each with a
  chain-of-thought reason
- Runner over a frozen question set; three metrics judged concurrently, with
  retry/backoff on transient provider errors
- Frozen corpus snapshot (drift detection) + random article sampling for
  question authoring
- Leaderboard comparing experiments; CLI (`sample` / `run` / `index-sparse` /
  `board`), with `--rerank`, `--window` and `--hybrid` toggles
- `LLMService.generate` accepts an optional `temperature` (judge uses 0;
  production chat unchanged)

Experiments run (494 articles / 1281 chunks, top-5). Leaderboard
(Context / Groundedness / Answer):

- baseline 0.39 / 0.93 / 0.91
- e5-instruct 0.46 / 0.97 / 0.97 — **adopted**
- top10 0.32 / 0.97 / 0.96 — rejected (precision metric diluted)
- rerank 0.48 / 0.99 / 0.96 — **adopted in production** (ADR-008)
- rerank-window 0.52 / 0.94 / 0.95 — rejected (Groundedness trade-off)
- hybrid-rerank 0.46 / 0.99 / 0.94 — rejected (no gain on semantic questions)

Pending

- Chunking sweep; query rewriting / HyDE; prompt-engineering experiments
- Recall@k with ground-truth answers (the current metric measures precision only)
- Optional distinct judge model; parallelize Context Relevance judging

---

# Execution Model

Status: Completed (async foundation)

Implemented

- Async FastAPI endpoints
- Async SQLAlchemy (`AsyncSession` over psycopg 3)
- `AsyncQdrantClient`
- Async Together AI client (embeddings and generation)
- Blocking libraries (Trafilatura, feedparser) offloaded via `asyncio.to_thread`
- Alembic remains synchronous

See ADR-006 for the decision and rationale.

---

# External Technologies

- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Qdrant
- Together AI
- LlamaIndex
- fastembed (cross-encoder reranking + BM25 sparse, local ONNX)
- Trafilatura
- httpx
- lxml

---

# Current Technical Debt

- Publication dates are normalized to UTC for RSS and SITEMAP sources (via
  `app.core.dates`). CRAWL (HtmlDiscovery) leaves `published_at` null because a
  listing page carries no per-article date.
- Metadata normalization between different providers has not yet been implemented.
- Crawl4AI (browser-based discovery for JavaScript-rendered sites) is not yet
  implemented; HtmlDiscovery only handles server-rendered HTML.
- Deleting an article removes its PostgreSQL rows but not its Qdrant vectors,
  which can leave orphaned points.
- Background ingestion runs in-process (FastAPI BackgroundTasks): no retries and
  lost on restart. A task queue / worker and periodic scheduling are future work.
- The evaluation Context Relevance metric is a per-chunk mean, i.e. precision-
  oriented; it is biased against larger `top_k` and does not measure recall.
  Measuring coverage would need a different metric (e.g. recall@k with
  ground-truth answers). The judge is currently the same model that generates
  answers (possible same-model bias). See ADR-007.

---

# Next Milestones

1. Integrate Crawl4AI as a browser-based discovery strategy for
   JavaScript-rendered sites (new CRAWL4AI source type).
2. Add more news sources.
3. Normalize metadata from different providers.

---

# Notes

This document must always describe the current state of the repository.

Completed features should be moved from "Pending" to "Implemented" as development progresses.
