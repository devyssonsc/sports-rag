# Documentation

## Purpose

This directory contains the permanent documentation for the Sports RAG project.

The documentation is intended for both developers and AI agents working on the project. Each document has a single responsibility and should be kept up to date as the project evolves.

---

# Reading Order

When starting work on the project, read the documents in the following order:

1. `project-history/00-project-history.md`
   - Explains how the project evolved and why important decisions were made.

2. `learning/learning-philosophy.md`
   - Defines the learning principles that guide technical decisions.

3. `architecture/architecture.md`
   - Describes the current architecture of the system.

4. `development/project-state.md`
   - Shows the current implementation status.

5. `development/roadmap.md`
   - Describes the long-term direction of the project.

---

# Directory Structure

## architecture/

Documents describing the current system architecture.

Contents:

- architecture.md
- folder-structure.md
- data-flow.md

---

## project-history/

Historical evolution of the project.

Contents:

- 00-project-history.md

---

## development/

Documents related to the current development process.

Contents:

- project-state.md
- roadmap.md
- progress/

The `progress/` directory contains chronological development logs.

---

## learning/

Documents describing the educational philosophy of the project.

Contents:

- learning-philosophy.md

---

## decisions/

Architectural Decision Records (ADRs).

Each ADR documents a significant architectural decision, including alternatives considered and the reasons for the chosen solution.

---

# Documentation Rules

- Every document has a single responsibility.
- Avoid duplicating information across documents.
- Keep documentation synchronized with the implementation.
- Prefer updating existing documents over creating new ones.
- Record architectural changes in both the appropriate document and, when relevant, in an ADR and the Project History.

---

# Ownership

Documentation is considered part of the implementation.

A feature is only considered complete when both the code and its corresponding documentation have been updated.
