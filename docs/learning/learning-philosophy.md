# Learning Philosophy

## Purpose

This document defines the learning principles that guide every technical decision in the Sports RAG project.

It exists to ensure that the project remains a learning platform rather than becoming only an implementation exercise.

Whenever a technical decision is made, the principles in this document should take precedence over implementation speed.

---

# Primary Goal

The purpose of Sports RAG is to develop a deep understanding of modern Retrieval-Augmented Generation systems.

Success is measured by understanding, not by the number of implemented features.

---

# Core Principle

> Understand first. Abstract later.

Whenever possible, the learning process should follow this order:

1. Understand the concept.
2. Understand the problem it solves.
3. Implement a simple version when appropriate.
4. Identify its limitations.
5. Adopt a mature framework when its value becomes clear.

---

# Frameworks

Frameworks are encouraged.

However, they should never become "black boxes".

Before introducing a framework, the developer should understand:

- why it exists;
- which problem it solves;
- which parts of the implementation it abstracts;
- what trade-offs it introduces.

Example:

Manual chunking was implemented before adopting LlamaIndex SentenceSplitter.

This allowed the project to understand overlap, chunk size and semantic boundaries before delegating those concerns to a framework.

---

# Architectural Decisions

Every important architectural decision should answer three questions:

1. Why is this needed?
2. Which alternatives exist?
3. Why is this the best choice for this project?

The goal is not only to make good decisions, but also to understand why they are good decisions.

---

# Comparing Alternatives

When multiple valid solutions exist, they should be compared before implementation.

The comparison should include:

- advantages;
- disadvantages;
- complexity;
- scalability;
- maintainability;
- educational value.

The developer makes the final decision.

---

# Role of AI

AI assistants are expected to act as technical mentors.

They should:

- explain concepts before implementation;
- propose architectural improvements;
- encourage engineering best practices;
- maximize learning.

They should not simply generate code.

---

# Documentation

Documentation is considered part of the learning process.

Every relevant feature should leave behind documentation explaining:

- what was implemented;
- why it was implemented;
- which decisions were taken.

The documentation should allow another developer to understand the reasoning without reading the entire Git history.

---

# Incremental Development

Large features should be divided into small, understandable steps.

Each step should have:

- a clear objective;
- a clear implementation;
- a clear validation;
- a dedicated commit.

---

# Long-Term Vision

By the end of the project, the developer should understand the complete lifecycle of a modern RAG system, including:

- document discovery;
- content extraction;
- text normalization;
- chunking;
- embeddings;
- vector databases;
- retrieval;
- prompt construction;
- LLM integration;
- evaluation;
- architectural evolution.

The project is successful only if the knowledge acquired is reusable beyond this repository.
