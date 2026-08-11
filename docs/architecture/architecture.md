
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

Current implementation:

- RSSDiscovery

Current functional source types:

- RSS

Known but not yet functional source types:

- CRAWL

SourceType currently defines RSS and CRAWL. RSS is the only functional strategy. CRAWL exists as architectural preparation for a future CrawlDiscovery; until that strategy exists, creating a NewsSource with SourceType.CRAWL is rejected at creation time.

Planned implementations:

- CrawlDiscovery
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

1. Generate embedding for the question.
2. Search similar vectors in Qdrant.
3. Recover chunk metadata from PostgreSQL.
4. Return ranked context.

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

---

# Future Evolution

The architecture has been designed to support:

- additional discovery strategies;
- alternative embedding models;
- different LLM providers;
- hybrid retrieval;
- reranking;
- metadata filtering;
- evaluation pipelines.

These features should be added by extending existing abstractions whenever possible rather than modifying stable components.
