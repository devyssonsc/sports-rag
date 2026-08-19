"""Data structures produced by the evaluation harness."""

from __future__ import annotations

from pydantic import BaseModel


class MetricScore(BaseModel):
    """A single RAG Triad metric result.

    ``score`` is ``None`` when the metric could not be computed (e.g. no context
    was retrieved). This mirrors the ``NaN`` cells in the course dashboard: it is
    informative, not an error.
    """

    score: float | None
    reason: str


class QuestionResult(BaseModel):
    """The full evaluation record for one question."""

    question: str
    answer: str
    num_chunks: int
    latency_seconds: float

    context_relevance: MetricScore
    groundedness: MetricScore
    answer_relevance: MetricScore

    # Retrieval recall@k against the ground-truth article ids (None when the
    # question has no ground-truth entry). This is deterministic — no LLM — and
    # measures coverage (did we retrieve the right articles?), unlike the
    # precision-oriented Context Relevance.
    recall: float | None
    retrieved_article_ids: list[int]
    ground_truth_article_ids: list[int]


class RunSummary(BaseModel):
    """The leaderboard row for one experiment run.

    Averages ignore ``None`` scores, exactly like the course leaderboard skips
    ``NaN`` values.
    """

    experiment: str
    timestamp: str
    question_count: int

    mean_context_relevance: float | None
    mean_groundedness: float | None
    mean_answer_relevance: float | None
    mean_recall: float | None

    mean_latency_seconds: float

    results: list[QuestionResult]
