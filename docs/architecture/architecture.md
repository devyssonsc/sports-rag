
# Architecture

## Purpose

This document describes the **current architecture** of the Sports RAG project.

Unlike the Project History, which explains how the project evolved, this document represents the current state of the system and the responsibilities of each layer and component.

Whenever the architecture changes, this document must be updated.

---

# Architectural Principles

The project follows a layered architecture.

The main design principles are:

- Single Responsibility Principle.
- Separation of concerns.
- Low coupling between services.
- Explicit data flow.
- Components communicate through well-defined interfaces.
- New features should extend the architecture instead of modifying existing pipelines whenever possible.

---

# Execution Model

The application runs on a fully asynchronous stack (see ADR-006):

- FastAPI endpoints are asynchronous.
- Database access uses SQLAlchemy `AsyncSession` over psycopg 3 (async).
- Qdrant access uses `AsyncQdrantClient`.
- Together AI (embeddings and generation) uses the async client.
- Blocking libraries without an async API (Trafilatura, feedparser) are
  offloaded with `asyncio.to_thread`.
- Alembic migrations remain synchronous.

---

# High-Level Pipeline

## News ingestion

```text
NewsSource
      │
      ▼
SourceType
      â”‚
      â–¼
Discovery Strategy
      │
      ▼
SourceArticle[]
      │
      ▼
ContentExtractionService
      │
      ▼
TextCleaningService
      │
      ▼
ChunkService
      │
      ▼
EmbeddingService
      │
      ├──────────────► PostgreSQL
      │                    │
      └──────────────► Qdrant
```

## Question answering

```text
Question
    │
    ▼
EmbeddingService
    │
    ▼
Qdrant
    │
    ▼
Relevant Chunk IDs
    │
    ▼
PostgreSQL
    │
    ▼
PromptBuilderService
    │
    ▼
LLMService
    │
    ▼
Answer
```

---

# Layer Responsibilities

## api

Exposes HTTP endpoints.

Responsibilities:

- Request validation.
- Dependency injection.
- Response serialization.

Business rules must not be implemented here.

---

## schemas

Defines request and response models used by the API.

Responsibilities:

- Input validation.
- Output serialization.

---

## dto

Represents objects exchanged internally between services.

DTOs are independent from persistence models.

Example:

- SourceArticle

---

## models

Represents the persistence layer.

Responsibilities:

- SQLAlchemy models.
- Database mapping.

---

## repositories

Repositories encapsulate all database access.

Responsibilities:

- Read data.
- Persist data.
- Hide ORM details from services.

Repositories must not contain business logic.

---

## services

Services implement all business logic.

Services coordinate repositories and external integrations.

They are the core of the application.

---

# Main Components

## Discovery Layer

Purpose:

Discover new articles from a source.

Current implementations:

- RSSDiscovery (feedparser)
- HtmlDiscovery (plain HTTP + HTML parsing)
- SitemapDiscovery (XML sitemaps, including Google News sitemaps)

Current functional source types:

- RSS
- CRAWL (server-rendered HTML pages)
- SITEMAP (XML sitemaps)

SourceType currently defines RSS, CRAWL and SITEMAP, all functional. A CRAWL source fetches a listing page with a plain HTTP GET (no browser) and keeps the links matching a per-source regex (`article_url_pattern`), validated at creation. A SITEMAP source reads an XML sitemap and builds one article per `<loc>`; for Google News sitemaps it also fills the title and `published_at` from the `news:` fields. JavaScript-rendered sites are out of scope for HtmlDiscovery and will be served by a future browser-based strategy under a separate source type (e.g. CRAWL4AI).

Planned implementations:

- Crawl4AI-based discovery (browser, for JavaScript-rendered sites)
- API-based discovery
- Other discovery strategies

Selection is performed by DiscoveryFactory using the NewsSource type.

The output of every discovery strategy is:

```text
list[SourceArticle]
```

The remainder of the pipeline is independent from the discovery mechanism.

---

## ContentExtractionService

Purpose:

Extract the full article text from a URL.

Current implementation:

- Trafilatura

The extraction mechanism should be replaceable without affecting the remaining pipeline.

---

## TextCleaningService

Purpose:

Normalize extracted text before chunking.

Responsibilities include:

- whitespace normalization;
- newline cleanup;
- removal of extraction artifacts.

---

## ChunkService

Purpose:

Transform articles into semantic chunks.

Current implementation:

- LlamaIndex SentenceSplitter.

Responsibilities:

- chunk generation;
- overlap management;
- chunk persistence.

---

## EmbeddingService

Purpose:

Generate vector embeddings for:

- document chunks;
- user queries.

The embedding model should remain configurable.

---

## Vector Repository

Purpose:

Store and retrieve embeddings from Qdrant.

Responsibilities:

- collection management;
- vector insertion;
- similarity search.

---

## RetrievalService

Purpose:

Retrieve the most relevant chunks for a user question.

Flow:

1. Embed the question with the e5 instruction prefix (`embed_query`).
2. Search similar vectors in Qdrant (cosine) for a candidate pool.
3. Rerank the pool with a cross-encoder and keep the best top-k (see
   RerankService); documents stay in embedding order when reranking is off.
4. Recover chunk metadata from PostgreSQL.
5. Return ranked context.

Two optional stages are wired only in the evaluation harness, not in the
production path: sentence-window neighbour expansion and hybrid dense + BM25
retrieval (RRF fusion via a sparse Qdrant collection). See ADR-007 / ADR-008.

---

## RerankService

Purpose:

Reorder retrieved candidates by true (query, chunk) relevance, using a local
cross-encoder (fastembed, ONNX). Enabled in production; the model is loaded once
(singleton) and cached in a volume. See ADR-008.

---

## PromptBuilderService

Purpose:

Construct prompts for the language model.

Responsibilities:

- inject retrieved context;
- define response instructions.

---

## LLMService

Purpose:

Interact with the language model provider.

Current provider:

- Together AI

The provider should remain replaceable.

---

## ChatService

Purpose:

Coordinate the complete RAG pipeline.

Responsibilities:

1. Receive the user question.
2. Retrieve relevant context.
3. Build the prompt.
4. Generate the answer.
5. Return sources.

---

# Persistence

## PostgreSQL

Stores structured data.

Current entities include:

- news_sources
- articles
- chunks

---

## Qdrant

Stores vector embeddings.

Payloads reference persisted entities stored in PostgreSQL.

---

# Current Discovery Architecture

The project intentionally separates:

Discovery

↓

Content Extraction

↓

Cleaning

↓

Chunking

↓

Embeddings

↓

Retrieval

↓

Generation

This separation allows new discovery mechanisms to be added without changing the remainder of the pipeline.

---

# Current External Technologies

- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Qdrant
- Together AI
- Trafilatura
- LlamaIndex
- fastembed (cross-encoder reranking + BM25 sparse, local ONNX)

---

# Future Evolution

Implemented since the original design: reranking (ADR-008) and an evaluation
harness (ADR-007). Hybrid retrieval and sentence-window are implemented but kept
as eval-only capabilities.

The architecture still supports, as future work:

- additional discovery strategies;
- alternative embedding models;
- different LLM providers;
- metadata filtering;
- conversational memory.

These features should be added by extending existing abstractions whenever possible rather than modifying stable components.
