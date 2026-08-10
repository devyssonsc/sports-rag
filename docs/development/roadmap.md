# Roadmap

## Purpose

This document defines the long-term direction of the Sports RAG project.

Unlike the Project History, it does not describe past decisions.

Unlike the Project State, it does not describe what has already been implemented.

Its purpose is to define the learning journey and the major milestones that the project aims to achieve.

---

# Vision

Sports RAG is a long-term learning project.

The objective is to progressively build a modern Retrieval-Augmented Generation system while understanding every important architectural decision behind it.

Progress is measured by acquired knowledge rather than by the number of implemented features.

---

# Guiding Principles

Every milestone should contribute to understanding one or more RAG concepts.

Whenever possible:

- understand first;
- implement;
- validate;
- document;
- only then move to the next milestone.

Large features should be divided into small incremental steps.

---

# Learning Roadmap

## Phase 1 — News Ingestion

### Goal

Build a reliable ingestion pipeline.

### Topics

- News discovery
- Content extraction
- Text cleaning
- Persistence
- Duplicate detection

### Status

Completed

---

## Phase 2 — Semantic Retrieval

### Goal

Understand semantic search.

### Topics

- Semantic chunking
- Embeddings
- Vector databases
- Similarity search
- Retrieval pipeline

### Status

Completed

---

## Phase 3 — Multi-source Discovery

### Goal

Support different article discovery mechanisms.

### Planned Topics

- Crawl4AI integration
- Multiple discovery strategies
- Metadata normalization
- Date normalization
- Source-specific improvements

### Status

In Progress

---

## Phase 4 — Retrieval Quality

### Goal

Improve retrieval precision.

### Planned Topics

- Metadata filters
- Hybrid Search
- BM25
- Dense + Sparse Retrieval
- Reranking
- Context selection

### Status

Planned

---

## Phase 5 — Generation Quality

### Goal

Improve answer quality.

### Planned Topics

- Prompt engineering
- Context compression
- Source citation
- Hallucination reduction
- Conversation memory

### Status

Planned

---

## Phase 6 — Evaluation

### Goal

Measure system quality.

### Planned Topics

- Retrieval evaluation
- Generation evaluation
- Precision metrics
- Recall metrics
- Benchmark datasets

### Status

Planned

---

## Phase 7 — Production Concerns

### Goal

Study production-ready RAG systems.

### Planned Topics

- Background workers
- Scheduling
- Monitoring
- Observability
- Caching
- Rate limiting
- Scaling

### Status

Planned

---

# Future Ideas

Potential future studies:

- Knowledge Graph RAG
- Agentic RAG
- Multi-modal RAG
- GraphRAG
- Long-context retrieval
- Multi-vector retrieval
- Query rewriting
- Self-reflection
- Document versioning

These topics are intentionally not prioritized.

---

# Out of Scope

Sports RAG is not intended to become a production SaaS.

Features that do not contribute to learning modern RAG systems should have lower priority than educational objectives.

---

# Maintenance

This roadmap should only change when the long-term direction of the project changes.

Implementation details and daily work belong in the Development Progress logs, not in this document.
