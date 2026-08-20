# ADR-011: Answer-Quality Evaluation and Cited-Sources Prompt

- **Status:** Accepted
- **Date:** 2026-08
- **Decision Makers:** Sports RAG Project

---

# Context

With retrieval at a structural ceiling (ADR-008/009, only e5-instruct + rerank
helped), the next lever for answer quality is the **generation prompt** — improved
by editing `PromptBuilderService` only, with retrieval untouched.

The problem: the RAG Triad is **saturated** for prompt work under the Llama judge
(ADR-010). Measured on the current prompt, the baseline was Context `0.533`,
Groundedness `0.978`, **Answer Relevance `1.000`**. Two of the three metrics cannot
register a prompt improvement:

- **Context Relevance** compares question ↔ retrieved chunk; the answer is not even
  an input, so it is invariant to the prompt (pure retrieval).
- **Answer Relevance** is already at the 1.000 ceiling — it can only go down.
- **Groundedness** has ~0.02 of headroom.

So the leaderboard would show ~`0.53 / 0.98 / 1.00` for almost any reasonable
prompt, making it blind to the qualities prompt engineering targets (source
attribution, conciseness, clarity, handling of unanswerable/ambiguous questions).
The frozen 20-question set also contains **no unanswerable questions**, so refusal
behaviour was entirely unmeasured.

---

# Decision

Extend the harness with **two prompt-sensitive metrics** and an **adversarial
question set**, make generation **deterministic** for comparisons, then adopt a
**cited-sources prompt**.

1. **Answer-quality judge** (LLM, independent Llama, temp 0) — a single 0..1 score
   over four equally-weighted dimensions: conciseness, clarity, attribution, and
   appropriate abstention. This is the primary signal for prompt work; the RAG
   Triad is kept for grounding/relevance regression checks.
2. **Citation check** (deterministic, no LLM) — the prompt presents the context as
   numbered sources and the answer must cite `[n]`. The check verifies markers are
   present and every marker points to a real source (an out-of-range marker is a
   fabricated citation — a free hallucination signal). Score = valid / total
   markers; `None` when there is nothing to cite (a correct abstention).
3. **Adversarial set** (`questions_hard.json`, run with `--hard`) — 10 questions:
   4 unanswerable (in-domain but absent from the corpus), 2 ambiguous
   (no referent), 4 hard thematic. Kept **separate** from the frozen 20 so
   historical comparisons stay valid; it has its own baseline.
4. **Deterministic generation for evaluation** — the harness now generates at
   `temperature=0`. Production `/chat` is unchanged (it calls `generate()` without
   a temperature). See "Key lesson".
5. **Adopted prompt** — number the sources and require a plain-ASCII `[n]` citation
   after every factual claim; keep the existing "state unavailable" instruction and
   add a (benign) ambiguity clause; ask for concise, synthesised answers.

---

# Evaluation

Adopted prompt vs. the previous prompt, judge Llama-3.3-70B. The `-t0` rows are the
canonical baselines (deterministic generation); the two new columns are
answer-quality and citation.

| Config (e5 + rerank)         | Context | Grounded | Answer | Quality | Cite | Set |
|------------------------------|:------:|:-------:|:-----:|:------:|:----:|-----|
| prompt-baseline              | 0.533  | 0.978   | 1.000 | 0.863  | 0.000 | std (20) |
| **prompt-v2 (adopted, t0)**  | 0.530  | 0.965   | 1.000 | 0.864  | **1.000** | std (20) |
| prompt-baseline-hard         | 0.432  | 0.950   | 0.900 | 0.830  | 0.000 | hard (10) |
| **prompt-v2 (adopted, t0)**  | 0.424  | 0.937   | 0.580 | 0.863  | **1.000** | hard (10) |

Findings:

- **Citations are the clean win.** `citation` went 0.000 → **1.000**: every claim is
  now attributed to a verifiable source, with zero fabricated markers. The Triad is
  flat within noise and answer quality is unchanged — but the product is genuinely
  better (a news RAG whose claims can be checked).
- **The Triad is saturated/blind, as predicted.** It moved only within run-to-run
  noise; it is kept as a regression guard, not a progress signal for prompt work.
- **The quality judge is only weakly sensitive** (0.863 → 0.864 despite full
  attribution — attribution is 1 of 4 diluted dimensions in 0.05 steps).
- **The adversarial set earned its place.** It exposed a failure the Triad is blind
  to: on referent-less questions the model **confidently fabricates** (e.g. *"Did the
  club complete the signing?"* → *"Yes, Chelsea signed Pep Chavarría"*, quality
  0.25) while Groundedness/Answer stay ~1.0. Genuine unanswerable questions, by
  contrast, are **already handled well** (clean abstention, quality 1.0). Ambiguity
  handling was left as-is by decision (degenerate single-turn input; forcing refusal
  risks over-refusing legitimate questions).
- **Answer Relevance is the wrong lens for the hard set** (0.580): the
  answer-relevance judge scores a correct "information unavailable" as "did not
  answer". On the hard set, `quality` (which rewards appropriate abstention) is the
  metric to read.

---

# Key lesson

**Generator non-determinism was larger than the prompt effect.** Evaluation
generation ran at the provider default (~0.7), so answers varied run-to-run and a
single thematic question could swing Groundedness ±0.2 (moving the 20-question mean
±0.01) — swamping the prompt delta. Fixing generation at `temperature=0` for
evaluation makes a prompt change the only thing that moves the answer. Absolute
values shift slightly, so adopted-prompt baselines were re-fixed at temp 0;
production is unaffected.

Corollary: a **deterministic** metric (the citation check) gave the crispest,
most trustworthy signal of the whole phase — worth more here than the coarse LLM
quality judge.

---

# Alternatives Considered

- **Only qualitative side-by-side reading** of stored answers — most sensitive to
  real quality but subjective and not a board number; kept as a companion, not the
  measurement.
- **Quality judge with separate sub-scores** (conciseness / clarity / attribution)
  — more diagnostic but more columns and judge calls; deferred (single composite
  chosen to start).
- **`[Source: title]` citations** — more human-readable without the numbered list
  but verbose and harder to validate; rejected in favour of numbered `[n]`.
- **Replacing the frozen 20** with harder questions — would break historical
  comparability; rejected in favour of a separate `--hard` set.

---

# Consequences

Positive:

- Prompt work is now measurable: a deterministic citation metric plus a
  quality/abstention judge, and an adversarial set that probes refusal and
  ambiguity.
- The adopted prompt attributes every claim to a verifiable, non-fabricated source.
- Deterministic evaluation makes prompt comparisons reproducible.

Negative / notes:

- The RAG Triad is confirmed saturated for prompt work; it remains a regression
  guard only.
- The LLM quality judge is coarse; large prompt effects show, small ones may not.
- New leaderboard columns are `NaN` for pre-existing rows (backward compatible);
  temp-0 rows are not directly comparable to earlier default-temp rows.
- Ambiguity on degenerate single-turn inputs is a known, accepted gap.

---

# Future Review

Revisit if a more sensitive quality signal is needed (sub-scores or a harsher
rubric), if the corpus/questions grow (author ground truth for the hard thematic
set to restore recall there), or if multi-turn `/chat` makes ambiguity handling
worth addressing.
