# ADR-006: Async-first Architecture

- **Status:** Accepted
- **Date:** 2026-08
- **Decision Makers:** Sports RAG Project

---

# Context

The application was built as a fully synchronous stack:

- FastAPI endpoints declared with `def`;
- SQLAlchemy with a synchronous `Session`;
- synchronous repositories (`db.execute`, `db.commit`);
- synchronous Qdrant client;
- synchronous Together AI client (embeddings and LLM);
- the discovery layer (`DiscoveryStrategy.discover`) is synchronous.

This was adequate while the only discovery mechanism was RSS, which is a simple
synchronous network read.

Two forces now push against this design:

1. **Crawl4AI is async-native.** The next discovery strategy (`CrawlDiscovery`,
   see ADR-004) is built on `AsyncWebCrawler`. Bridging it into a synchronous
   pipeline would require `asyncio.run(...)` inside `discover()`, which blocks a
   worker thread for the entire crawl and mixes execution models.

2. **The workload is I/O-bound.** Ingestion and question answering are dominated
   by network calls: content download, embedding generation, vector search and
   LLM generation. This is exactly the workload async concurrency is designed
   for. Under the synchronous model, a single `def` endpoint occupies a worker
   for the full duration of every external call.

Continuing to add async components (starting with Crawl4AI) on top of a
synchronous core would produce a hybrid stack that is harder to reason about
than committing to a single execution model.

---

# Decision

Migrate the **entire application stack to async**.

Concretely:

- FastAPI endpoints become `async def`.
- SQLAlchemy uses `create_async_engine` + `async_sessionmaker` with
  `AsyncSession`. The `get_db` dependency yields an `AsyncSession`.
- Repositories `await` all database operations.
- The Qdrant client becomes `AsyncQdrantClient`.
- The Together AI client becomes the async client (`AsyncTogether`) for both
  embeddings and generation.
- `DiscoveryStrategy.discover` becomes an async method.

## Database driver

No driver change is required. The project already depends on `psycopg`
(psycopg 3), which supports async natively. The async engine uses the same
`postgresql+psycopg://` URL, so only the engine/session construction changes,
not the connection string or the dependency set.

## Handling blocking libraries

Some dependencies have no async API and are CPU/IO-blocking:

- **Trafilatura** (content extraction);
- **feedparser** (RSS parsing).

These will be wrapped with `asyncio.to_thread(...)` so they run in a worker
thread instead of blocking the event loop. Where a native async client exists
(PostgreSQL via psycopg, Qdrant, Together AI), the native async client is used
instead of a thread wrapper.

## Alembic stays synchronous

Database migrations are a separate, offline concern. Alembic will continue to
use a synchronous engine. `env.py` and the existing migrations are **not**
affected by this decision. This keeps the migration tooling simple and avoids
coupling schema evolution to the runtime execution model.

---

# Rationale

- The workload is I/O-bound, which is the scenario where async concurrency
  provides real benefit (a worker is released while awaiting external calls).
- The upcoming `CrawlDiscovery` is async-native; an async stack lets it be
  expressed as ordinary `await` calls with no execution-model bridging.
- Committing to a single execution model is simpler to reason about than a
  hybrid stack where some layers are sync and others async.
- psycopg 3 already supports async, so the foundational change (Postgres access)
  carries no new dependency and no driver migration.
- As a learning project, migrating a working synchronous stack to async is an
  explicit goal in itself: understanding event loops, `AsyncSession`, blocking
  vs non-blocking calls, and `to_thread` boundaries.

---

# Alternatives Considered

## Keep the stack synchronous; run Crawl4AI via `asyncio.run` inside discovery

### Advantages

- Minimal change.
- Only the discovery layer is touched.

### Disadvantages

- Blocks a worker thread for the entire crawl.
- Creates and tears down an event loop per fetch.
- Produces a hybrid model (sync core, async island) that is harder to reason
  about as more async components are added.

Decision: Rejected. It postpones the problem and increases long-term complexity.

---

## Make only the ingestion/discovery path async

### Advantages

- Smaller migration than the full stack.
- Covers the immediate Crawl4AI need.

### Disadvantages

- Leaves `/chat`, `/retrieval` and `/articles` synchronous while the ingestion
  path is async — still a hybrid stack.
- The retrieval and chat paths are equally I/O-bound (embeddings, vector search,
  LLM) and would benefit from the same model.

Decision: Rejected in favor of a consistent, single-model stack.

---

## Full async stack (chosen)

### Advantages

- Single execution model across all layers.
- Native fit for both the ingestion pipeline and the RAG (chat/retrieval) path.
- Clean integration point for Crawl4AI and future async providers.

### Disadvantages

- Touches every layer (database, repositories, services, routers, tests).
- Introduces async-specific failure modes (blocking the event loop, forgotten
  `await`, mixing sync/async sessions).
- Tests must adopt `pytest-asyncio` and async mocks.

Decision: Accepted.

---

# Consequences

Positive:

- Consistent execution model end to end.
- Better concurrency for I/O-bound ingestion and question answering.
- Crawl4AI (and future async providers) integrate without bridging.
- No new database driver; the async change reuses psycopg 3.

Negative:

- A cross-cutting refactor with no user-facing behavior change, guarded today by
  only a minimal test suite.
- New classes of async bugs to watch for (event-loop blocking, missing `await`).
- Blocking libraries (Trafilatura, feedparser) must be explicitly offloaded with
  `to_thread`; forgetting to do so silently stalls the event loop.

---

# Migration Plan

The migration is performed bottom-up, in small independent steps, so the
application remains consistent at each stage. `CrawlDiscovery` is intentionally
**out of scope** for this ADR — it is implemented after the async foundation is
in place.

1. **ADR-006** — this document (the decision).
2. **Database foundation** — async engine, `async_sessionmaker`, async `get_db`.
   Alembic remains synchronous.
3. **Repositories** — article, chunk, news_source (Postgres) and vector
   repository (`AsyncQdrantClient`).
4. **Services** — news_source, ingestion, article, chunk, embedding, retrieval,
   chat, article_content (Trafilatura via `to_thread`).
5. **Discovery** — `DiscoveryStrategy.discover` becomes async; `RSSDiscovery`
   offloads feedparser via `to_thread`; the factory is unchanged.
6. **Routers** — all endpoints become `async def`.
7. **Tests** — adopt `pytest-asyncio`; update `NewsSourceService` tests to use
   async mocks; keep the `DiscoveryFactory` tests.
8. **Documentation** — update `architecture.md`, `data-flow.md`,
   `project-state.md`, `roadmap.md` and the project history.

Each step is a separate commit with no behavioral change.

---

# Future Review

This decision should be revisited if:

- the application ceases to be I/O-bound and becomes CPU-bound in a way that
  makes the async overhead unjustified;
- a required dependency provides only a synchronous API and cannot be safely
  offloaded to a thread;
- operational complexity from the async model outweighs its concurrency
  benefits for the project's scale.

Until then, async-first is the official execution model for Sports RAG.
