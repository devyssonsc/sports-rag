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

Current implementations:

- RSSDiscovery (feedparser)
- HtmlDiscovery (plain HTTP + HTML parsing)
- SitemapDiscovery (XML sitemaps, including Google News sitemaps)

Current source model:

- NewsSource

Current functional source types:

- RSS
- CRAWL (server-rendered HTML pages)
- SITEMAP (XML sitemaps)

SITEMAP sources read an XML sitemap and build one article per `<loc>`. For
Google News sitemaps, the title and publication date come directly from the
`news:title` and `news:publication_date` fields, which also populates the
article's `published_at`. `article_url_pattern` is optional for SITEMAP (a news
sitemap is already a curated list); when provided it is applied as an extra
filter.

`article_url_pattern` is an **include** filter by default (keep URLs that match
the regex). Prefixing the pattern with `!` turns it into an **exclude** filter
(keep URLs that do *not* match) — e.g. `!/betting/` drops betting URLs while
keeping everything else. This is shared by all URL-filtering strategies
(HtmlDiscovery, SitemapDiscovery).

CRAWL sources discover articles by fetching a listing/section page with a plain
HTTP GET (no browser) and keeping the links that match a per-source regular
expression (`article_url_pattern`). This covers sites that render their content
as normal HTML.

Sites that expose their links only through JavaScript are intentionally out of
scope for HtmlDiscovery. They will be handled by a future browser-based strategy
(Crawl4AI) under a separate SourceType (e.g. CRAWL4AI), added only when such a
source is actually needed — to avoid paying the browser/Chromium cost
prematurely.

Planned implementations:

- Crawl4AI-based discovery (browser, for JavaScript-rendered sites)
- API-based discovery
- Additional providers

The correct strategy is selected through a DiscoveryFactory according to the
configured SourceType on the NewsSource.

A CRAWL NewsSource requires a valid `article_url_pattern`. This is validated at
creation time so that a misconfigured source is rejected up front instead of
failing later during fetch.

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
