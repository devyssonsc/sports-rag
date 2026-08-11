# Sports RAG - Entity Relationship Diagram (ERD)

## Overview

The Sports RAG platform is composed of three core domain entities:

- NewsSource
- Article
- Chunk

Each entity has a single responsibility:

- **NewsSource** represents a source of news articles (currently RSS).
- **Article** represents a news article discovered from a NewsSource.
- **Chunk** represents a semantic fragment of an article that can be embedded and indexed in the vector database.

The PostgreSQL database stores the application state, while Qdrant stores vector embeddings.

---

# Entity Relationship Diagram

```text
                    ┌──────────────────────────┐
                    │        NewsSource        │
                    │       (news_sources)     │
                    ├──────────────────────────┤
                    │ PK id                    │
                    │ name                     │
                    │ url (unique)             │
                    │ type (source_type enum)  │
                    │ article_url_pattern      │
                    │ last_fetched_at (null)   │
                    │ created_at               │
                    └────────────┬─────────────┘
                                 │
                                 │ 1 : N
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │         Article          │
                    │        (articles)        │
                    ├──────────────────────────┤
                    │ PK id                    │
                    │ FK news_source_id (null) │
                    │ title                    │
                    │ summary (null)           │
                    │ content (null)           │
                    │ url (unique)             │
                    │ source                   │
                    │ published_at (null)      │
                    │ created_at               │
                    └────────────┬─────────────┘
                                 │
                                 │ 1 : N
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │          Chunk           │
                    │         (chunks)         │
                    ├──────────────────────────┤
                    │ PK id                    │
                    │ FK article_id            │
                    │ chunk_index              │
                    │ content                  │
                    │ created_at               │
                    └────────────┬─────────────┘
                                 │
                                 │ Indexed into
                                 ▼
                     ┌─────────────────────────┐
                     │        Qdrant           │
                     ├─────────────────────────┤
                     │ Vector                  │
                     │ Payload (chunk_id,      │
                     │          article_id)    │
                     └─────────────────────────┘
```

The `source_type` enum currently accepts `RSS`, `CRAWL` and `SITEMAP`, all functional. `CRAWL` sources set `article_url_pattern` (a regex, required at creation) to select article links from a server-rendered HTML listing page. `SITEMAP` sources read an XML sitemap (`article_url_pattern` optional). JavaScript-rendered sites are deferred to a future browser-based source type.

---

# Relationships

## NewsSource → Article

A news source can produce many articles.

Each article optionally references the news source it came from (`news_source_id` is nullable).

Relationship:

```
NewsSource (1) ------ (N) Article
```

---

## Article → Chunk

Each article is split into multiple chunks.

Each chunk belongs to exactly one article.

Relationship:

```
Article (1) ------ (N) Chunk
```

---

## Chunk → Qdrant

Each chunk may be indexed into Qdrant.

The embedding vector itself is **not stored in PostgreSQL**.

Instead, PostgreSQL stores only the chunk and its content.

The Qdrant payload references the persisted `chunk_id` and `article_id`, and Qdrant becomes the source of truth for vector search.

---

# Design Decisions

## Why keep chunks in PostgreSQL?

Many RAG tutorials only store chunks in the vector database.

This project intentionally stores chunks in PostgreSQL because it provides:

- traceability
- auditability
- easier debugging
- re-embedding without re-chunking
- easier migration between embedding models

---

## Why not store embeddings in PostgreSQL?

Embedding vectors can contain hundreds or thousands of floating point values.

Vector databases are optimized for:

- storage
- indexing
- ANN search
- similarity queries

Duplicating vectors in PostgreSQL would increase storage without adding value.

---

## Processing Pipeline

```
NewsSource
    │
    ▼
Discovery (RSS)
    │
    ▼
Article
    │
    ▼
Download Full Content
    │
    ▼
Chunking
    │
    ▼
Chunk
    │
    ▼
Embedding Generation
    │
    ▼
Qdrant
```

---

## Future Extensions

The model was intentionally designed to support future entities such as:

- SearchSession
- User
- Query
- RetrievedChunk
- GeneratedAnswer

without requiring changes to the current relationships.
