# ADR-010: Independent Judge Model for Evaluation

- **Status:** Accepted
- **Date:** 2026-08
- **Decision Makers:** Sports RAG Project

---

# Context

The RAG Triad harness (ADR-007) used the **same model** for both generating
answers and judging them: `openai/gpt-oss-120b`. ADR-007 flagged the resulting
**same-model bias** as a known limitation — a model may score its own output
differently than an independent one would.

To remove that bias, the judge should be a **different, capable** model, ideally
with reasoning. Constraint: it must be serverless on the project's Together
account.

---

# Decision

Use an **independent judge**, separate from the answer generator:
**`meta-llama/Llama-3.3-70B-Instruct-Turbo`** (Together, serverless, different
family). `LLMService` is parametrized by model; the harness builds a dedicated
judge `LLMService` while generation keeps `gpt-oss-120b`. The judge is used only
by the evaluation harness — production `/chat` is unaffected.

The judge model is configurable via `JUDGE_MODEL` (with `JUDGE_TEMPERATURE` and
`JUDGE_MAX_TOKENS`), and the JSON parser strips `<think>...</think>` traces so a
reasoning judge can be swapped in.

---

# Evaluation

Three judges scored the same production config (e5 + rerank). The judge-independent
**recall stayed constant at 0.758**, confirming only the judge changed:

| Judge (e5 + rerank)                 | Context | Groundedness | Answer |
|-------------------------------------|:------:|:-----------:|:-----:|
| gpt-oss-120b (== generator)         | 0.484  | 0.989       | 0.961  |
| Qwen3.5-9B (independent, small)     | 0.524  | **1.000**   | 1.000  |
| **Llama-3.3-70B (independent)**     | 0.531  | 0.9925      | 1.000  |

- **Same-model was not inflation here** — gpt-oss was slightly *harder* on itself.
- **Qwen3.5-9B rubber-stamped** groundedness and answer at a flat 1.0 (found no
  issues in any of 20 questions) — too small to discriminate.
- **Llama-3.3-70B discriminates**: groundedness < 1.0 (it flagged real issues), and
  on a probe with an unsupported claim (a transfer fee absent from the context) it
  correctly scored groundedness 0.0. Independent **and** capable.

---

# Key lesson

**Absolute metric values depend heavily on the judge** (context 0.48 → 0.53 just by
changing who judges). Therefore only comparisons made with the **same judge** are
valid. The leaderboard now records the judge model per row; rows produced before
this change are gpt-oss-era and are not directly comparable to new ones.

A capable judge matters as much as an independent one: a weak independent judge
(9B) that scores everything perfect is less useful than a strong self-judge.

---

# Alternatives Considered

- **Dedicated reasoning models** (`Qwen/QwQ-32B`, `deepseek-ai/DeepSeek-R1-*`,
  `Qwen3-Next-...-Thinking`): all **non-serverless** on the account (require a paid
  dedicated endpoint) — rejected (same friction as ADR-008's rerank endpoints).
- **Qwen3.5-9B** (serverless, reasoning): too lenient (flat 1.0) — rejected.
- **`moonshotai/Kimi-K2.6` / `deepcogito/cogito-v2-671b`** (serverless, strong):
  much larger → slower/costlier for ~140 calls per run — not chosen for now, but
  viable if a stronger judge is wanted.

---

# Consequences

Positive:

- Judging is now independent of the generator, removing same-model bias.
- Leaderboard rows are labeled by judge, making cross-run comparisons honest.
- The harness supports swapping in a reasoning judge (env + `<think>` parsing).

Negative / notes:

- Judge choice shifts absolute scores, so historical (gpt-oss-judged) rows are not
  directly comparable; the adopted-config decisions (e5-instruct, rerank) were made
  consistently within the gpt-oss judge and still stand (the recall anchor confirms
  retrieval is unchanged).
- No serverless *reasoning* judge is available on the account; a strong instruct
  model is used instead.
- Slightly higher eval cost/latency (a 70B judge vs 120B — comparable).

---

# Future Review

Revisit if a serverless reasoning judge becomes available, if a stronger judge
(Kimi/cogito) is warranted, or if key configs are re-baselined under the new judge
for a fully coherent leaderboard.
