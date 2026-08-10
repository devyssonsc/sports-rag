# Folder Structure

## Purpose

This document explains the responsibility of every major directory in the Sports RAG repository.

The goal is to make the project structure predictable, easy to navigate and easy to evolve.

Every directory should have a single responsibility.

---

# Repository Structure

```text
Sports-RAG/
├── app/
├── alembic/
├── tests/
├── docs/
├── CODEX.md
└── README.md
```

---

# Root Files

## README.md

Project overview.

Contains:

- project description;
- installation;
- execution;
- basic usage.

---

## CODEX.md

Defines how AI agents should collaborate on this repository.

It is the operational constitution for AI-assisted development.

---

# app/

Contains the application source code.

## api/

HTTP layer.

Responsibilities:

- routers;
- dependency injection;
- request handling.

No business logic should be implemented here.

---

## models/

SQLAlchemy persistence models.

Each model represents a database entity.

---

## schemas/

Pydantic request and response models exposed by the API.

---

## dto/

Internal data transfer objects exchanged between services.

DTOs are independent from persistence.

---

## repositories/

Database access layer.

Responsibilities:

- queries;
- inserts;
- updates;
- deletes.

Repositories should not implement business rules.

---

## services/

Business logic.

Services coordinate repositories, external providers and application workflows.

Whenever possible, each service should have a single responsibility.

---

## database/

Database configuration and session management.

---

# alembic/

Database migrations.

Responsibilities:

- schema evolution;
- version control for the database.

---

# tests/

Automated tests.

Suggested organization:

```text
tests/
├── unit/
├── integration/
└── e2e/
```

---

# docs/

Project documentation.

See `docs/README.md` for the documentation index.

---

# Design Rules

The following dependency direction should be respected whenever possible:

```text
API
 ↓
Services
 ↓
Repositories
 ↓
Database
```

Services may communicate with external providers.

Repositories should never call services.

Schemas should never contain business logic.

DTOs should never depend on ORM models.

---

# Adding New Features

When introducing a new feature:

1. Create or update the required models.
2. Create repositories if persistence is needed.
3. Implement business logic in services.
4. Expose the feature through the API layer.
5. Add or update documentation.
6. Add tests when appropriate.

---

# Maintenance

If the repository structure changes significantly, this document must be updated together with the implementation.
