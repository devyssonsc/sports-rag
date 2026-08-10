# ADR-003: LlamaIndex for Semantic Chunking

- **Status:** Accepted
- **Date:** 2026-08
- **Decision Makers:** Sports RAG Project

---

# Context

Chunking is one of the most important stages of a Retrieval-Augmented Generation (RAG) pipeline.

Initially, Sports RAG implemented a custom chunking algorithm to understand:

- chunk size;
- overlap;
- sentence boundaries;
- context preservation;
- the impact of chunking on retrieval quality.

After the underlying concepts were understood, the project evaluated whether maintaining a custom implementation continued to provide educational value.

---

# Decision

Sports RAG adopts **LlamaIndex SentenceSplitter** as the official chunking strategy.

The current implementation uses semantic sentence-aware chunking with configurable:

- chunk size;
- chunk overlap.

The chunking implementation remains isolated behind the project's own service layer.

---

# Rationale

The custom implementation achieved its educational objective.

However, maintaining it would require solving problems that are already well handled by mature libraries.

LlamaIndex provides:

- sentence-aware splitting;
- semantic chunk boundaries;
- configurable overlap;
- token-aware sizing;
- predictable behaviour;
- active maintenance.

Using the framework allows the project to focus on higher-value RAG concepts while still understanding what the framework abstracts.

---

# Alternatives Considered

## Custom Chunking

### Advantages

- Full control.
- Excellent educational value.
- Complete understanding of the implementation.

### Disadvantages

- Reinvents existing solutions.
- Harder to maintain.
- Easier to introduce subtle retrieval issues.

Decision:

Used during the learning phase, but not retained as the production implementation.

---

## LangChain Text Splitters

### Advantages

- Popular ecosystem.
- Multiple splitting strategies.

### Disadvantages

- Larger dependency footprint.
- At the time of the decision, LlamaIndex offered a cleaner abstraction focused on document processing.

Decision:

Not adopted.

---

## Token-Based Splitting Only

### Advantages

- Simple.
- Predictable token limits.

### Disadvantages

- Frequently breaks semantic boundaries.
- Can reduce retrieval quality.

Decision:

Not adopted because preserving semantic meaning was considered more important.

---

# Consequences

Positive:

- Better semantic chunks.
- More reliable retrieval.
- Less maintenance.
- Easy configuration.

Negative:

- Part of the implementation is delegated to an external framework.
- Behaviour depends on upstream library updates.

These trade-offs are acceptable because the project already achieved its learning objective before introducing the framework.

---

# Future Review

This decision should be revisited if:

- another chunking strategy consistently improves retrieval quality;
- hierarchical chunking is introduced;
- document-specific chunking strategies become necessary.

Until then, LlamaIndex SentenceSplitter remains the official chunking implementation for Sports RAG.
