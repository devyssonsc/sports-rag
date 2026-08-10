# ADR-001: Layered Architecture

- **Status:** Accepted
- **Date:** 2026-08
- **Decision Makers:** Sports RAG Project

---

# Context

Sports RAG is primarily a learning project focused on understanding how modern Retrieval-Augmented Generation (RAG) systems are built.

One of the project goals is to clearly separate responsibilities so that every stage of the pipeline can be understood, tested and evolved independently.

The architecture should remain simple enough for learning while supporting future growth.

---

# Decision

The project adopts a **Layered Architecture**.

The primary layers are:

```text
API
↓
Services
↓
Repositories
↓
Database
```

Supporting layers:

- models
- schemas
- dto

Business logic is concentrated inside the Services layer.

Repositories are responsible only for persistence.

The API layer is responsible only for HTTP concerns.

---

# Rationale

This architecture was selected because it provides:

- clear separation of responsibilities;
- low cognitive load;
- straightforward debugging;
- easy unit testing;
- incremental evolution without major rewrites.

It also aligns well with the educational goals of the project.

---

# Alternatives Considered

## Clean Architecture

### Advantages

- Strong dependency inversion.
- High testability.
- Excellent scalability.

### Disadvantages

- Introduces additional abstractions.
- Higher learning overhead.
- More boilerplate for a project focused on understanding RAG systems.

Decision:

Not adopted at this stage.

---

## Domain-Driven Design (DDD)

### Advantages

- Excellent for large business domains.
- Rich domain modeling.

### Disadvantages

- Unnecessary complexity for the current scope.
- Diverts attention from the primary learning objective.

Decision:

Not adopted.

---

## MVC

### Advantages

- Simple.
- Familiar.

### Disadvantages

- Encourages business logic leakage.
- Less suitable for API-centric backend services.

Decision:

Not adopted.

---

# Consequences

Positive:

- Clear responsibilities.
- Easy navigation.
- Easier onboarding for AI agents.
- Independent evolution of pipeline components.

Negative:

- Some orchestration services become larger over time.
- Additional classes compared to a minimal implementation.

These trade-offs are acceptable for the goals of the project.

---

# Future Review

This decision should be revisited only if:

- the project evolves into a significantly larger codebase;
- multiple bounded contexts emerge;
- the layered architecture becomes a bottleneck.

Until then, the Layered Architecture remains the official architectural style for Sports RAG.
