"""The evaluation runner: build -> evaluate -> record.

For each frozen question it runs the *real* pipeline (retrieve -> build prompt ->
generate), then scores the result with the RAG Triad. This mirrors
``ChatService`` but keeps the intermediate context around, because two of the
three metrics need it.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
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

from evaluation.judge import RagTriadJudge
from evaluation.schemas import QuestionResult, RunSummary


async def evaluate(
    experiment: str,
    questions: list[str],
    limit: int = 5,
    rerank: bool = False,
    candidate_pool: int = 20,
) -> RunSummary:
    """Run the whole question set through the pipeline and score it."""

    embedding_service = EmbeddingService()
    vector_repository = VectorRepository()
    prompt_builder = PromptBuilderService()
    llm_service = LLMService()
    judge = RagTriadJudge(llm_service)

    # The reranker is independent of the judge model, so context-relevance scores
    # stay an honest measurement of the reranked retrieval.
    rerank_service = RerankService() if rerank else None

    results: list[QuestionResult] = []

    async with SessionLocal() as db:
        retrieval_service = RetrievalService(
            embedding_service=embedding_service,
            vector_repository=vector_repository,
            chunk_repository=ChunkRepository(db),
            article_repository=ArticleRepository(db),
            rerank_service=rerank_service,
        )

        for index, question in enumerate(questions, start=1):
            print(f"[{index}/{len(questions)}] {question}")
            result = await _evaluate_question(
                question=question,
                limit=limit,
                candidate_pool=candidate_pool,
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
    limit: int,
    candidate_pool: int,
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
    )
    prompt = prompt_builder.build(question, chunks)
    answer = await llm_service.generate(prompt)

    latency = time.perf_counter() - started

    contexts = [chunk.content for chunk in chunks]
    joined_context = "\n\n".join(contexts)

    # The three metrics are independent once we have the answer, so judge them
    # concurrently to cut wall-clock time.
    answer_relevance, groundedness, context_relevance = await asyncio.gather(
        judge.answer_relevance(question, answer),
        judge.groundedness(joined_context, answer),
        judge.context_relevance(question, contexts),
    )

    return QuestionResult(
        question=question,
        answer=answer,
        num_chunks=len(chunks),
        latency_seconds=round(latency, 3),
        context_relevance=context_relevance,
        groundedness=groundedness,
        answer_relevance=answer_relevance,
    )


def _summarize(experiment: str, results: list[QuestionResult]) -> RunSummary:
    return RunSummary(
        experiment=experiment,
        timestamp=datetime.now(timezone.utc).isoformat(),
        question_count=len(results),
        mean_context_relevance=_mean_metric(results, "context_relevance"),
        mean_groundedness=_mean_metric(results, "groundedness"),
        mean_answer_relevance=_mean_metric(results, "answer_relevance"),
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


def _print_scores(result: QuestionResult) -> None:
    def fmt(value: float | None) -> str:
        return "NaN" if value is None else f"{value:.2f}"

    print(
        "    context={ctx}  groundedness={grd}  answer={ans}  ({n} chunks, {lat}s)".format(
            ctx=fmt(result.context_relevance.score),
            grd=fmt(result.groundedness.score),
            ans=fmt(result.answer_relevance.score),
            n=result.num_chunks,
            lat=result.latency_seconds,
        )
    )
