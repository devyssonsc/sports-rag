"""The evaluation runner: build -> evaluate -> record.

For each frozen question it runs the *real* pipeline (retrieve -> build prompt ->
generate), then scores the result with the RAG Triad. This mirrors
``ChatService`` but keeps the intermediate context around, because two of the
three metrics need it.

It also computes retrieval **recall@k** against a ground-truth article set — a
deterministic, LLM-free measure of coverage. ``retrieval_only=True`` skips the LLM
entirely (generation + triad), so recall can be iterated cheaply and for free.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from app.database.postgres import SessionLocal
from app.repositories.article_repository import ArticleRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.vector_repository import VectorRepository
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.prompt_builder_service import PromptBuilderService
from app.services.rerank_service import RerankService
from app.services.retrieval_service import RetrievalService
from app.services.sparse_embedding_service import SparseEmbeddingService

from evaluation._retry import with_retry
from evaluation.hyde_service import HydeService
from evaluation.multi_query_service import MultiQueryService
from evaluation.judge import JUDGE_MODEL, RagTriadJudge
from evaluation.schemas import MetricScore, QuestionResult, RunSummary

GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"

_SKIPPED = MetricScore(score=None, reason="retrieval-only run (LLM skipped)")


def _load_ground_truth() -> dict[str, list[int]]:
    """question text -> list of article ids that answer it (keys starting with _ ignored)."""
    if not GROUND_TRUTH_PATH.exists():
        return {}
    raw = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def _recall(retrieved_article_ids: list[int], ground_truth_ids: list[int]) -> float | None:
    """Fraction of ground-truth articles present among the retrieved ones."""
    if not ground_truth_ids:
        return None
    retrieved = set(retrieved_article_ids)
    hits = sum(1 for gid in ground_truth_ids if gid in retrieved)
    return hits / len(ground_truth_ids)


# Accept ASCII "[1]" and full-width "【1】" brackets — some models emit the latter —
# plus an optional trailing "†..." line-range annotation, e.g. "【1†L1-L7】".
_CITATION_MARKER_RE = re.compile(r"[\[【]\s*(\d+)(?:\s*†[^\]】]*)?\s*[\]】]")


def _citation_score(answer: str, num_sources: int, answerable: bool) -> MetricScore:
    """Deterministic citation check: are the ``[n]`` source markers valid?

    The prompt presents the context as numbered sources and asks the model to cite
    them as ``[1]``, ``[2]``. This checks — with no LLM — whether the answer
    actually does so and whether every marker points to a real source (an
    out-of-range marker is a fabricated citation, a cheap hallucination signal).

    Score = valid markers / total markers: 1.0 when every marker is valid, dragged
    down by fabricated ones, 0.0 when nothing is cited. Returns ``None`` for a
    question with no answer to attribute (a correct abstention has nothing to
    cite); abstention itself is graded by the quality judge, not here.
    """
    if not answerable:
        return MetricScore(
            score=None,
            reason="Unanswerable question; a correct abstention has nothing to cite.",
        )

    markers = [int(m) for m in _CITATION_MARKER_RE.findall(answer)]
    if not markers:
        return MetricScore(score=0.0, reason="No [n] citation markers in the answer.")

    valid = [m for m in markers if 1 <= m <= num_sources]
    invalid = sorted({m for m in markers if not 1 <= m <= num_sources})
    score = len(valid) / len(markers)

    if invalid:
        reason = (
            f"{len(valid)}/{len(markers)} markers valid; fabricated/out-of-range "
            f"{invalid} (only {num_sources} sources)."
        )
    else:
        reason = f"all {len(markers)} markers valid; cited {sorted(set(valid))}."
    return MetricScore(score=score, reason=reason)


async def evaluate(
    experiment: str,
    questions: list[str],
    limit: int = 5,
    rerank: bool = False,
    candidate_pool: int = 20,
    window: int = 0,
    hybrid: bool = False,
    hyde: bool = False,
    multi_query: bool = False,
    retrieval_only: bool = False,
    question_meta: dict[str, dict] | None = None,
) -> RunSummary:
    """Run the whole question set through the pipeline and score it.

    ``question_meta`` maps a question's text to ``{"kind", "answerable"}`` (from the
    hard set). Missing entries default to a standard, answerable question.
    """
    question_meta = question_meta or {}

    embedding_service = EmbeddingService()
    vector_repository = VectorRepository()
    prompt_builder = PromptBuilderService()
    llm_service = LLMService()  # answer generation (gpt-oss-120b)
    # Independent reasoning judge — a different model, to avoid same-model bias.
    judge = RagTriadJudge(LLMService(model=JUDGE_MODEL))
    ground_truth = _load_ground_truth()

    # The reranker is independent of the judge model, so context-relevance scores
    # stay an honest measurement of the reranked retrieval.
    rerank_service = RerankService() if rerank else None
    sparse_embedding_service = SparseEmbeddingService() if hybrid else None
    hyde_service = HydeService(llm_service, embedding_service) if hyde else None
    multi_query_service = MultiQueryService(llm_service) if multi_query else None

    results: list[QuestionResult] = []

    async with SessionLocal() as db:
        retrieval_service = RetrievalService(
            embedding_service=embedding_service,
            vector_repository=vector_repository,
            chunk_repository=ChunkRepository(db),
            article_repository=ArticleRepository(db),
            rerank_service=rerank_service,
            sparse_embedding_service=sparse_embedding_service,
            hyde_service=hyde_service,
            multi_query_service=multi_query_service,
        )

        for index, question in enumerate(questions, start=1):
            print(f"[{index}/{len(questions)}] {question}")
            meta = question_meta.get(question.strip(), {})
            result = await _evaluate_question(
                question=question,
                kind=meta.get("kind", "standard"),
                answerable=meta.get("answerable", True),
                limit=limit,
                candidate_pool=candidate_pool,
                window=window,
                ground_truth_ids=ground_truth.get(question.strip(), []),
                retrieval_only=retrieval_only,
                retrieval_service=retrieval_service,
                prompt_builder=prompt_builder,
                llm_service=llm_service,
                judge=judge,
            )
            _print_scores(result)
            results.append(result)

    return _summarize(experiment, results)


async def _evaluate_question(
    question: str,
    kind: str,
    answerable: bool,
    limit: int,
    candidate_pool: int,
    window: int,
    ground_truth_ids: list[int],
    retrieval_only: bool,
    retrieval_service: RetrievalService,
    prompt_builder: PromptBuilderService,
    llm_service: LLMService,
    judge: RagTriadJudge,
) -> QuestionResult:

    started = time.perf_counter()

    chunks = await retrieval_service.retrieve_context(
        question,
        limit,
        candidate_pool=candidate_pool,
        window=window,
    )

    # Recall is deterministic — computed from retrieval alone, no LLM.
    retrieved_article_ids = list(dict.fromkeys(chunk.article_id for chunk in chunks))
    recall = _recall(retrieved_article_ids, ground_truth_ids)

    if retrieval_only:
        # Skip the LLM entirely: no answer, no triad. Recall still measured.
        return QuestionResult(
            question=question,
            answer="(retrieval-only)",
            num_chunks=len(chunks),
            latency_seconds=round(time.perf_counter() - started, 3),
            kind=kind,
            answerable=answerable,
            context_relevance=_SKIPPED,
            groundedness=_SKIPPED,
            answer_relevance=_SKIPPED,
            answer_quality=_SKIPPED,
            citation=_SKIPPED,
            recall=recall,
            retrieved_article_ids=retrieved_article_ids,
            ground_truth_article_ids=ground_truth_ids,
        )

    prompt = prompt_builder.build(question, chunks)
    # Generate at temperature 0 so a prompt change is the ONLY thing that moves the
    # answer between runs — otherwise sampling variance (~0.7 default) is larger
    # than the prompt delta and swamps the comparison. Production /chat is
    # unaffected: it calls LLMService.generate() without a temperature.
    answer = await with_retry(lambda: llm_service.generate(prompt, temperature=0.0))

    latency = time.perf_counter() - started

    contexts = [chunk.content for chunk in chunks]
    joined_context = "\n\n".join(contexts)

    # Citation validity is deterministic (no LLM) — computed straight from the
    # answer text and the number of sources fed to the prompt.
    citation = _citation_score(answer, num_sources=len(chunks), answerable=answerable)

    # The LLM metrics are independent once we have the answer, so judge them
    # concurrently to cut wall-clock time.
    answer_relevance, groundedness, context_relevance, answer_quality = await asyncio.gather(
        judge.answer_relevance(question, answer),
        judge.groundedness(joined_context, answer),
        judge.context_relevance(question, contexts),
        judge.answer_quality(question, joined_context, answer),
    )

    return QuestionResult(
        question=question,
        answer=answer,
        num_chunks=len(chunks),
        latency_seconds=round(latency, 3),
        kind=kind,
        answerable=answerable,
        context_relevance=context_relevance,
        groundedness=groundedness,
        answer_relevance=answer_relevance,
        answer_quality=answer_quality,
        citation=citation,
        recall=recall,
        retrieved_article_ids=retrieved_article_ids,
        ground_truth_article_ids=ground_truth_ids,
    )


def _summarize(experiment: str, results: list[QuestionResult]) -> RunSummary:
    return RunSummary(
        experiment=experiment,
        timestamp=datetime.now(timezone.utc).isoformat(),
        question_count=len(results),
        judge_model=JUDGE_MODEL,
        mean_context_relevance=_mean_metric(results, "context_relevance"),
        mean_groundedness=_mean_metric(results, "groundedness"),
        mean_answer_relevance=_mean_metric(results, "answer_relevance"),
        mean_answer_quality=_mean_metric(results, "answer_quality"),
        mean_citation=_mean_metric(results, "citation"),
        mean_recall=_mean_recall(results),
        mean_latency_seconds=round(
            mean([r.latency_seconds for r in results]), 3
        ) if results else 0.0,
        results=results,
    )


def _mean_metric(results: list[QuestionResult], name: str) -> float | None:
    """Average a metric, skipping ``None`` (undefined) scores like the course."""
    scores = [
        getattr(r, name).score
        for r in results
        if getattr(r, name).score is not None
    ]
    if not scores:
        return None
    return round(mean(scores), 4)


def _mean_recall(results: list[QuestionResult]) -> float | None:
    scores = [r.recall for r in results if r.recall is not None]
    if not scores:
        return None
    return round(mean(scores), 4)


def _print_scores(result: QuestionResult) -> None:
    def fmt(value: float | None) -> str:
        return "NaN" if value is None else f"{value:.2f}"

    print(
        "    context={ctx}  groundedness={grd}  answer={ans}  quality={qly}  "
        "citation={cit}  recall={rec}  ({n} chunks, {lat}s)".format(
            ctx=fmt(result.context_relevance.score),
            grd=fmt(result.groundedness.score),
            ans=fmt(result.answer_relevance.score),
            qly=fmt(result.answer_quality.score),
            cit=fmt(result.citation.score),
            rec=fmt(result.recall),
            n=result.num_chunks,
            lat=result.latency_seconds,
        )
    )
