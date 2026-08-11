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

## Step-by-Step

### 1. Discovery

The selected `DiscoveryStrategy` discovers available articles from a `NewsSource`.

`SourceType.RSS`, `SourceType.CRAWL` and `SourceType.SITEMAP` are functional. RSS uses `RSSDiscovery` (feedparser); CRAWL uses `HtmlDiscovery`, which fetches a server-rendered listing page over plain HTTP and selects article links via a per-source regex (`article_url_pattern`); SITEMAP uses `SitemapDiscovery`, which reads an XML sitemap (including Google News sitemaps, from which it also fills `published_at`). JavaScript-rendered sites are deferred to a future browser-based strategy.

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

Articles whose extracted content is empty or too short (e.g. cookie-consent
walls or JavaScript-only pages that the plain-HTTP extractor cannot read) are
skipped and not persisted. A per-source `article_url_pattern` can filter such
URLs earlier, before extraction.

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

An embedding is generated for every chunk.

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
EmbeddingService
      │
      ▼
Qdrant Similarity Search
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

The question is converted into a vector representation.

---

### 3. Similarity Search

Qdrant returns the most semantically similar chunks.

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

The current flow is designed to support:

- additional discovery strategies;
- alternative extraction engines;
- hybrid retrieval;
- reranking;
- metadata filtering;
- conversational memory;
- evaluation pipelines.

These capabilities should extend the existing flow rather than replace it whenever possible.
