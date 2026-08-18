"""The RAG Triad as native LLM-as-a-judge feedback functions.

Three metrics, each comparing a different pair of (question, context, answer):

    Context Relevance = question <-> context   (was the retrieval good?)
    Groundedness      = context  <-> answer    (is the answer backed by sources?)
    Answer Relevance  = question <-> answer    (does the answer address the ask?)

Every metric is scored by an LLM (``LLMService``) which returns a 0..1 score and
a short chain-of-thought reason (the course's ``with_cot_reasons``). The reason
is what lets you debug *why* a run scored low, not just *that* it did.
"""

from __future__ import annotations

import json
import re
from statistics import mean

from app.services.llm_service import LLMService

from evaluation._retry import with_retry
from evaluation.schemas import MetricScore


# Temperature 0 => judging is as deterministic as the provider allows, so the
# same run is reproducible and experiments stay comparable.
JUDGE_TEMPERATURE = 0.0


_ANSWER_RELEVANCE_PROMPT = """\
You are a strict evaluator for a football/sports news RAG system.

Rate how well the ANSWER responds to the QUESTION. Judge only relevance and
responsiveness — NOT factual correctness, NOT grounding in any source. A perfect
answer directly and completely addresses what was asked; an off-topic or evasive
answer scores low.

QUESTION:
{question}

ANSWER:
{answer}

Respond with ONLY a JSON object, no markdown, no extra text:
{{"score": <float between 0 and 1>, "reason": "<one short sentence>"}}
"""


_CONTEXT_RELEVANCE_PROMPT = """\
You are a strict evaluator for the RETRIEVAL step of a football/sports news RAG
system.

Rate how relevant the retrieved CONTEXT passage is for answering the QUESTION.
1.0 = directly and fully relevant; 0.0 = completely unrelated.

QUESTION:
{question}

CONTEXT PASSAGE:
{context}

Respond with ONLY a JSON object, no markdown, no extra text:
{{"score": <float between 0 and 1>, "reason": "<one short sentence>"}}
"""


_GROUNDEDNESS_PROMPT = """\
You are a strict evaluator checking for hallucinations in a football/sports news
RAG system.

Decide how well the ANSWER is supported by the CONTEXT. Break the answer into its
individual factual claims; a claim counts as supported only if the CONTEXT states
or clearly implies it. 1.0 = every claim is supported by the context; 0.0 = the
answer is fabricated / unsupported. Do not reward correct-sounding facts that are
absent from the context.

CONTEXT:
{context}

ANSWER:
{answer}

Respond with ONLY a JSON object, no markdown, no extra text:
{{"score": <float between 0 and 1>, "reason": "<one short sentence>"}}
"""


class RagTriadJudge:
    """Computes the three RAG Triad metrics using an LLM as the judge.

    The same model that generates answers also judges them. This is simple and
    good enough to start; swapping in a different judge model later means only
    passing a second ``LLMService`` here.
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def answer_relevance(
        self,
        question: str,
        answer: str,
    ) -> MetricScore:
        prompt = _ANSWER_RELEVANCE_PROMPT.format(
            question=question,
            answer=answer,
        )
        return await self._judge(prompt)

    async def groundedness(
        self,
        context: str,
        answer: str,
    ) -> MetricScore:
        if not context.strip():
            return MetricScore(
                score=None,
                reason="No context retrieved; groundedness is undefined.",
            )

        prompt = _GROUNDEDNESS_PROMPT.format(
            context=context,
            answer=answer,
        )
        return await self._judge(prompt)

    async def context_relevance(
        self,
        question: str,
        contexts: list[str],
    ) -> MetricScore:
        """Score each retrieved passage and average them (the course's np.mean)."""
        if not contexts:
            return MetricScore(
                score=None,
                reason="No context retrieved; context relevance is undefined.",
            )

        per_chunk: list[MetricScore] = []
        for context in contexts:
            prompt = _CONTEXT_RELEVANCE_PROMPT.format(
                question=question,
                context=context,
            )
            per_chunk.append(await self._judge(prompt))

        scores = [c.score for c in per_chunk if c.score is not None]
        if not scores:
            return MetricScore(
                score=None,
                reason="Judge failed to score any passage.",
            )

        avg = mean(scores)
        reason = "; ".join(
            f"[{c.score}] {c.reason}" for c in per_chunk
        )
        return MetricScore(score=avg, reason=reason)

    async def _judge(self, prompt: str) -> MetricScore:
        raw = await with_retry(
            lambda: self.llm_service.generate(
                prompt,
                temperature=JUDGE_TEMPERATURE,
            )
        )
        return _parse_score(raw)


def _parse_score(raw: str) -> MetricScore:
    """Extract ``{"score": ..., "reason": ...}`` from the judge's reply.

    LLMs sometimes wrap JSON in prose or code fences, so we grab the first
    balanced-looking object rather than trusting the whole string.
    """
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return MetricScore(score=None, reason=f"Unparseable judge reply: {raw[:200]}")

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return MetricScore(score=None, reason=f"Invalid JSON from judge: {raw[:200]}")

    score = data.get("score")
    reason = str(data.get("reason", "")).strip()

    if score is None:
        return MetricScore(score=None, reason=reason or "Judge returned no score.")

    try:
        score = float(score)
    except (TypeError, ValueError):
        return MetricScore(score=None, reason=f"Non-numeric score: {score!r}")

    # Clamp defensively; judges occasionally return 0-100 or slight overshoots.
    if score > 1.0:
        score = score / 100.0 if score <= 100.0 else 1.0
    score = max(0.0, min(1.0, score))

    return MetricScore(score=score, reason=reason)
