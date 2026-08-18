# Data Flow

## Purpose

This document describes how data flows through the Sports RAG system.

It complements `architecture.md` by focusing on execution flow rather than component responsibilities.

---

# Overview

Sports RAG has two primary pipelines:

1. News Ingestion Pipeline
2. Question Answering Pipeline (RAG)

Both pipelines are independent but connected through the persisted data.

---

# News Ingestion Pipeline

## High-Level Flow

```text
NewsSource
      │
      ▼
SourceType
      â”‚
      â–¼
DiscoveryFactory
      │
      ▼
DiscoveryStrategy
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
      ├────────────► PostgreSQL
      └────────────► Qdrant
```

## Execution

`POST /news-sources/{id}/fetch` validates the source and then runs the pipeline
below as a **background task**, returning `202 Accepted` immediately. When the
task finishes it updates the source's `last_fetched_at` and logs an
`IngestionResult` (`processed` / `inserted` / `ignored` / `skipped`).

The background task runs in-process (FastAPI `BackgroundTasks`): simple and
infra-free, but with no retries and lost on a restart. A dedicated task
queue / worker (and periodic scheduling) is future work.

## Step-by-Step

### 1. Discovery

The selected `DiscoveryStrategy` discovers available articles from a `NewsSource`.

`SourceType.RSS`, `SourceType.CRAWL` and `SourceType.SITEMAP` are functional. RSS uses `RSSDiscovery` (feedparser); CRAWL uses `HtmlDiscovery`, which fetches a server-rendered listing page over plain HTTP and selects article links via a per-source regex (`article_url_pattern`); SITEMAP uses `SitemapDiscovery`, which reads an XML sitemap (including Google News sitemaps, from which it also fills `published_at`). JavaScript-rendered sites are deferred to a future browser-based strategy.

Each strategy normalizes `published_at` to a timezone-aware UTC datetime (via `app.core.dates`), regardless of the source's original date format or timezone, so the field is stored consistently across providers.

`article_url_pattern` is an include filter by default (keep URLs matching the regex); prefix it with `!` to exclude instead (keep URLs that do not match), e.g. `!/betting/`.

If the source cannot be fetched or parsed (network error, HTTP error, malformed
document), discovery raises a domain error that the API surfaces as HTTP 502.

Output:

```text
list[SourceArticle]
```

---

### 2. Content Extraction

For every discovered article:

- download the page;
- extract the main content;
- return plain text.

Before extraction, an article whose URL already exists in the database is
**ignored** (not re-fetched and not updated). Article URLs are globally unique,
so this covers both articles already ingested by an earlier fetch of any source
and duplicates within the same batch — for example an RSS feed that lists the
same item twice.

Articles whose extracted content is empty or too short (e.g. cookie-consent
walls or JavaScript-only pages that the plain-HTTP extractor cannot read) are
**skipped** and not persisted. A per-source `article_url_pattern` can filter
such URLs earlier, before extraction.

The ingestion run reports these outcomes as an `IngestionResult`
(`processed` = `inserted` + `ignored` + `skipped`), logged when the background
task finishes (see Execution above).

---

### 3. Text Cleaning

Normalize extracted content.

Typical operations include:

- whitespace normalization;
- newline cleanup;
- removal of extraction artifacts.

---

### 4. Chunking

The cleaned article is divided into semantic chunks using the configured chunking strategy.

Each chunk is stored in PostgreSQL.

---

### 5. Embedding Generation

An embedding is generated for every chunk. All chunks of an article are embedded
in a single batched request to the embeddings API (split into groups when the
count is large), rather than one request per chunk.

---

### 6. Vector Storage

Embeddings are stored in Qdrant.

Each vector references its corresponding chunk through metadata.

---

# Question Answering Pipeline

## High-Level Flow

```text
User Question
      │
      ▼
EmbeddingService (embed_query, e5 instruction prefix)
      │
      ▼
Qdrant Similarity Search (cosine) ── candidate pool (top-20)
      │
      ▼
RerankService (cross-encoder) ── best top-5
      │
      ▼
Chunk IDs
      │
      ▼
ChunkRepository
      │
      ▼
Retrieved Context
      │
      ▼
PromptBuilderService
      │
      ▼
LLMService
      │
      ▼
Generated Answer
```

## Step-by-Step

### 1. User Question

The API receives a natural language question.

---

### 2. Query Embedding

The question is embedded with `embed_query`, which prefixes the e5 instruction
(`Instruct: {task}\nQuery: {question}`). Documents are embedded as raw text, so
the query lands in the "query space" the e5 model was trained on (see ADR-007).

---

### 3. Similarity Search + Reranking

Qdrant returns a candidate pool of the most cosine-similar chunks (top-20). A
local cross-encoder (`RerankService`) then scores each (question, chunk) pair and
keeps the best top-5 — retrieve-then-rerank: embeddings for recall, cross-encoder
for precision (see ADR-008).

The evaluation harness can also run this step as hybrid retrieval (dense + BM25
fused with RRF) or widen the final chunks with sentence-window neighbours; neither
is enabled in production.

---

### 4. Context Recovery

Chunk metadata and contents are loaded from PostgreSQL.

---

### 5. Prompt Construction

The retrieved context is combined with instructions to produce the final prompt.

---

### 6. Response Generation

The prompt is sent to the configured LLM.

The generated answer and supporting sources are returned to the user.

---

# Persistence Flow

## PostgreSQL

Stores:

- sources
- articles
- chunks
- metadata

## Qdrant

Stores:

- embeddings
- vector payloads referencing PostgreSQL entities

---

# Design Principles

The two pipelines communicate only through persisted data.

This separation allows improvements to:

- discovery;
- extraction;
- chunking;
- embeddings;
- retrieval;
- generation

without requiring the entire pipeline to be redesigned.

---

# Future Extensions

Reranking and the evaluation pipeline are now implemented; hybrid retrieval and
sentence-window exist as eval-only capabilities. The current flow is still
designed to support:

- additional discovery strategies;
- alternative extraction engines;
- metadata filtering;
- conversational memory.

These capabilities should extend the existing flow rather than replace it whenever possible.
