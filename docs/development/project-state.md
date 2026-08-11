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

- Semantic search
- Chunk recovery
- Metadata recovery
- Ranked context

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
