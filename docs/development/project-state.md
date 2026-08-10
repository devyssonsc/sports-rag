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

Implemented

- NewsSource registration
- NewsSource listing
- NewsSource fetching
- SourceType support
- DiscoveryFactory
- RSSDiscovery
- Rejection of CRAWL sources until CrawlDiscovery exists

Pending

- CrawlDiscovery
- Additional discovery strategies

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

# External Technologies

- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Qdrant
- Together AI
- LlamaIndex
- Trafilatura

---

# Current Technical Debt

- Date normalization has not yet been implemented.
- Metadata normalization between different providers has not yet been implemented.
- CrawlDiscovery is not yet available.

---

# Next Milestones

1. Implement CrawlDiscovery.
2. Integrate Crawl4AI.
3. Normalize publication dates.
4. Normalize metadata from different providers.

---

# Notes

This document must always describe the current state of the repository.

Completed features should be moved from "Pending" to "Implemented" as development progresses.
