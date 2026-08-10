# ADR-002: Qdrant as Vector Database

- **Status:** Accepted
- **Date:** 2026-08
- **Decision Makers:** Sports RAG Project

---

# Context

A Retrieval-Augmented Generation (RAG) system requires efficient storage and retrieval of vector embeddings.

The project needed a vector database capable of:

- storing embeddings;
- performing semantic similarity search;
- associating vectors with metadata;
- integrating easily with Python.

The chosen solution also needed to support the educational goals of the project.

---

# Decision

Sports RAG adopts **Qdrant** as its vector database.

The application stores:

- structured data in PostgreSQL;
- vector embeddings in Qdrant.

Each vector contains a payload that references entities stored in PostgreSQL.

---

# Rationale

Qdrant was selected because it provides:

- native vector search;
- metadata (payload) support;
- simple Python client;
- Docker deployment;
- clear API;
- production-ready architecture.

Its concepts are easy to understand, making it an excellent choice for a learning-oriented project.

---

# Alternatives Considered

## FAISS

### Advantages

- Extremely fast.
- Widely used in research.

### Disadvantages

- Primarily a vector index, not a complete vector database.
- Additional work required for metadata and persistence.

Decision:

Not adopted because the project benefits from understanding a full vector database.

---

## pgvector

### Advantages

- Uses PostgreSQL.
- Simple infrastructure.

### Disadvantages

- Couples relational and vector workloads.
- Fewer vector-specific features.

Decision:

Not adopted to keep relational storage and vector storage conceptually separated.

---

## Pinecone

### Advantages

- Managed cloud service.
- Excellent scalability.

### Disadvantages

- External SaaS dependency.
- Less control over infrastructure.
- Paid tiers for larger usage.

Decision:

Not adopted because local infrastructure better supports experimentation.

---

# Consequences

Positive:

- Clear separation between relational and vector storage.
- Easy experimentation with similarity search.
- Metadata filtering support for future features.
- Straightforward local development using Docker.

Negative:

- Two persistence systems must be maintained.
- Additional synchronization between PostgreSQL and Qdrant.

These trade-offs are acceptable for the educational goals of the project.

---

# Future Review

This decision should be revisited only if:

- the project requires another vector engine for comparison;
- benchmarking becomes part of the learning objectives;
- infrastructure requirements change significantly.

Until then, Qdrant remains the official vector database for Sports RAG.
