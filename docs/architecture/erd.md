# Sports RAG - Entity Relationship Diagram (ERD)

## Overview

The Sports RAG platform is composed of three core domain entities:

- Feed
- Article
- Chunk

Each entity has a single responsibility:

- **Feed** represents an RSS source.
- **Article** represents a news article retrieved from a feed.
- **Chunk** represents a semantic fragment of an article that can be embedded and indexed in the vector database.

The PostgreSQL database stores the application state, while Qdrant stores vector embeddings.

---

# Entity Relationship Diagram

```text
                    ┌──────────────────────────┐
                    │          Feed            │
                    ├──────────────────────────┤
                    │ PK id                    │
                    │ name                     │
                    │ url                      │
                    │ language                 │
                    │ country                  │
                    │ sport                    │
                    │ provider                 │
                    │ is_active                │
                    │ last_fetch_at            │
                    │ created_at               │
                    │ updated_at               │
                    └────────────┬─────────────┘
                                 │
                                 │ 1 : N
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │         Article          │
                    ├──────────────────────────┤
                    │ PK id                    │
                    │ FK feed_id              │
                    │ title                   │
                    │ url (unique)            │
                    │ author                  │
                    │ language                │
                    │ summary                 │
                    │ content                 │
                    │ hash                    │
                    │ status                  │
                    │ published_at            │
                    │ updated_at              │
                    │ created_at              │
                    └────────────┬─────────────┘
                                 │
                                 │ 1 : N
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │          Chunk           │
                    ├──────────────────────────┤
                    │ PK id                    │
                    │ FK article_id           │
                    │ chunk_index             │
                    │ content                 │
                    │ token_count             │
                    │ embedding_model         │
                    │ embedding_status        │
                    │ created_at              │
                    └────────────┬─────────────┘
                                 │
                                 │
                                 │ Indexed into
                                 ▼
                     ┌─────────────────────────┐
                     │        Qdrant           │
                     ├─────────────────────────┤
                     │ Vector                  │
                     │ Metadata                │
                     └─────────────────────────┘
```

---

# Relationships

## Feed → Article

A feed can publish many articles.

Each article belongs to exactly one feed.

Relationship:

```
Feed (1) ------ (N) Article
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

Instead, PostgreSQL stores only the chunk and its indexing status.

Qdrant becomes the source of truth for vector search.

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
RSS Feed
    │
    ▼
Feed
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
