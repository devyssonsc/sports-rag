# ADR-004: Discovery Strategy Pattern

- **Status:** Accepted
- **Date:** 2026-08
- **Decision Makers:** Sports RAG Project

---

# Context

The first versions of Sports RAG assumed that every news source exposed an RSS feed.

As the project expanded, it became clear that this assumption was incorrect.

Several news websites:

- do not provide RSS feeds;
- provide incomplete feeds;
- publish outdated RSS feeds;
- expose content only through their website.

The ingestion pipeline needed to support multiple article discovery mechanisms without changing the remaining RAG pipeline.

---

# Decision

Sports RAG introduces a dedicated **Discovery Layer** based on the Strategy Pattern.

Each discovery mechanism implements a common interface and produces the same output:

```text
list[SourceArticle]
```

Current implementation:

- RSSDiscovery

Planned implementations:

- CrawlDiscovery (Crawl4AI)
- API-based discovery
- Additional providers

The correct strategy is selected through a DiscoveryFactory according to the configured SourceType.

---

# Rationale

The discovery mechanism should be independent from the rest of the ingestion pipeline.

Regardless of how articles are discovered, the remaining stages remain unchanged:

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

Persistence

This separation allows the project to evolve without coupling ingestion to a specific provider.

---

# Alternatives Considered

## RSS Only

### Advantages

- Very simple implementation.
- Mature ecosystem.
- Minimal maintenance.

### Disadvantages

- Limited source coverage.
- Many websites do not provide RSS.
- Difficult to expand.

Decision:

Rejected because it limits the scope of the project.

---

## Crawl Everything

### Advantages

- Maximum flexibility.
- Works for almost any website.

### Disadvantages

- Higher computational cost.
- More complex extraction rules.
- Unnecessary for sources that already expose high-quality RSS feeds.

Decision:

Rejected as the only discovery strategy.

Crawling should complement RSS, not replace it.

---

## Provider-Specific Implementations

### Advantages

- Maximum control.
- Can optimize each source individually.

### Disadvantages

- High maintenance cost.
- Tight coupling between ingestion and providers.

Decision:

Rejected in favor of a common abstraction.

---

# Consequences

Positive:

- Discovery becomes extensible.
- New providers require minimal changes.
- The ingestion pipeline remains stable.
- Responsibilities are clearly separated.

Negative:

- Additional abstraction layer.
- Factory and strategy management introduce extra classes.

These trade-offs are acceptable because they improve maintainability and scalability while preserving the educational value of the project.

---

# Future Review

This decision should be revisited if:

- discovery mechanisms require fundamentally different outputs;
- a workflow cannot be represented by the current abstraction;
- asynchronous discovery pipelines become necessary.

Until then, the Strategy Pattern remains the official architecture for article discovery in Sports RAG.
