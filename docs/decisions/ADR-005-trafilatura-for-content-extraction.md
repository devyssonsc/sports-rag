# ADR-005: Trafilatura for Content Extraction

- **Status:** Accepted
- **Date:** 2026-08
- **Decision Makers:** Sports RAG Project

---

# Context

After discovering an article, the system needs to extract its full textual content before any downstream processing.

The extraction component should:

- retrieve the main article body;
- remove navigation menus and page chrome;
- ignore advertisements and unrelated content;
- produce clean text suitable for chunking.

The project required a solution that worked across different news websites while remaining easy to integrate into the ingestion pipeline.

---

# Decision

Sports RAG adopts **Trafilatura** as the default content extraction engine.

The extraction stage is isolated inside `ContentExtractionService`, allowing the implementation to be replaced without affecting the remaining pipeline.

The output of this stage is plain article text.

---

# Rationale

Trafilatura was selected because it provides:

- high-quality article extraction;
- automatic boilerplate removal;
- support for a wide variety of news websites;
- simple Python integration;
- active open-source maintenance.

Tests performed with multiple sports news websites (including ESPN and BBC Sport) produced consistently good extraction quality.

Keeping extraction behind a dedicated service also preserves architectural flexibility.

---

# Alternatives Considered

## BeautifulSoup

### Advantages

- Lightweight.
- Full control over HTML parsing.

### Disadvantages

- Requires custom extraction logic for each website.
- Difficult to maintain across multiple sources.
- More susceptible to website layout changes.

Decision:

Rejected because the project aims to support many news providers.

---

## Newspaper3k

### Advantages

- Popular article extraction library.
- Simple API.

### Disadvantages

- Less actively maintained.
- Lower extraction quality on several tested websites.

Decision:

Not adopted.

---

## Crawl4AI Extraction

### Advantages

- Can extract content during crawling.
- Useful for dynamic websites.

### Disadvantages

- Couples article discovery with content extraction.
- Introduces unnecessary complexity for sources that already provide stable HTML pages.

Decision:

Not adopted as the default extraction mechanism.

Crawl4AI is reserved for article discovery, while content extraction remains an independent pipeline stage.

---

# Consequences

Positive:

- Consistent extraction quality.
- Cleaner input for chunking.
- Independent extraction layer.
- Easy replacement of the extraction engine in the future.

Negative:

- Extraction quality still depends on the target website structure.
- Some websites may require source-specific improvements over time.

These trade-offs are acceptable because they preserve both architectural separation and learning objectives.

---

# Future Review

This decision should be revisited if:

- Trafilatura no longer provides adequate extraction quality;
- a significant number of sources require custom extraction rules;
- dynamic websites become a primary source of content.

Until then, Trafilatura remains the official content extraction engine for Sports RAG.
