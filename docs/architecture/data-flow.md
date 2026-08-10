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
News Source
      │
      ▼
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

The selected `DiscoveryStrategy` discovers available articles from a news source.

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
