"""Command-line entrypoint for the evaluation harness.

Run from INSIDE the backend container (the ``.env`` hostnames ``postgres`` /
``qdrant`` only resolve there):

    docker compose exec backend python -m evaluation.run_eval sample -n 20
    docker compose exec backend python -m evaluation.run_eval run -e baseline
    docker compose exec backend python -m evaluation.run_eval board

Subcommands:
    sample  Pick N random articles, dump their content for question authoring,
            and freeze the corpus snapshot.
    run     Run the frozen questions through the pipeline and score the RAG Triad.
    board   Print the leaderboard (all experiments so far).
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

QUESTIONS_PATH = Path(__file__).parent / "questions.txt"


def load_questions(path: Path = QUESTIONS_PATH) -> list[str]:
    """One question per line; blank lines and ``#`` comments are ignored."""
    if not path.exists():
        raise SystemExit(f"Questions file not found: {path}")

    questions = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not questions:
        raise SystemExit(f"No questions found in {path} (all blank/comments).")
    return questions


async def _sample(count: int) -> None:
    from app.database.postgres import SessionLocal
    from evaluation import corpus

    async with SessionLocal() as db:
        article_count, chunk_count = await corpus.counts(db)

        if article_count == 0:
            raise SystemExit(
                "No articles in the database. Ingest a corpus before sampling."
            )
        if count > article_count:
            print(
                f"WARNING: requested {count} but only {article_count} articles "
                "exist; sampling all of them."
            )

        article_ids = await corpus.all_article_ids(db)
        sampled = await corpus.sample_articles(db, count)
        snapshot = corpus.build_snapshot(
            article_ids,
            chunk_count,
            [a.id for a in sampled],
        )

    corpus.write_snapshot(snapshot)
    corpus.write_sample_readable(sampled)

    print(
        f"Froze full corpus: {article_count} articles, {chunk_count} chunks."
    )
    print(f"Sampled {len(sampled)} of them for question authoring.")
    print(f"  snapshot -> {corpus.SNAPSHOT_PATH}")
    print(f"  content  -> {corpus.SAMPLE_READABLE_PATH}")
    print("\nNext: read the content file and write questions in questions.txt.")


async def _run(
    experiment: str,
    limit: int,
    rerank: bool,
    candidate_pool: int,
    window: int,
    hybrid: bool,
    hyde: bool,
    multi_query: bool,
    retrieval_only: bool,
) -> None:
    from app.database.postgres import SessionLocal
    from evaluation import corpus
    from evaluation.harness import evaluate
    from evaluation.leaderboard import save_run

    # Warn (don't block) if the live corpus drifted from the frozen snapshot,
    # so results stay honest across experiments.
    snapshot = corpus.load_snapshot()
    if snapshot is None:
        print("WARNING: no corpus snapshot found. Run 'sample' first for comparable results.")
    else:
        async with SessionLocal() as db:
            _, chunk_count = await corpus.counts(db)
            article_ids = await corpus.all_article_ids(db)
        for warning in corpus.diff_against(snapshot, article_ids, chunk_count):
            print(f"WARNING (corpus drift): {warning}")

    questions = load_questions()
    mode = f"top-{limit}"
    if hybrid:
        mode += ", hybrid"
    if rerank:
        mode += f", rerank from {candidate_pool}"
    if window:
        mode += f", window ±{window}"
    if hyde:
        mode += ", HyDE"
    if multi_query:
        mode += ", multi-query"
    if retrieval_only:
        mode += ", retrieval-only (no judge)"
    print(f"\nRunning experiment '{experiment}' over {len(questions)} questions ({mode})...\n")

    summary = await evaluate(
        experiment,
        questions,
        limit,
        rerank=rerank,
        candidate_pool=candidate_pool,
        window=window,
        hybrid=hybrid,
        hyde=hyde,
        multi_query=multi_query,
        retrieval_only=retrieval_only,
    )
    detail_path = save_run(summary)

    print("\n=== RUN SUMMARY ===")
    print(f"experiment        : {summary.experiment}")
    print(f"judge model       : {summary.judge_model}")
    print(f"context relevance : {_fmt(summary.mean_context_relevance)}")
    print(f"groundedness      : {_fmt(summary.mean_groundedness)}")
    print(f"answer relevance  : {_fmt(summary.mean_answer_relevance)}")
    print(f"recall@k          : {_fmt(summary.mean_recall)}")
    print(f"mean latency (s)  : {summary.mean_latency_seconds}")
    print(f"detail written to : {detail_path}")


async def _index_sparse() -> None:
    """Backfill the BM25 sparse collection from all chunks in Postgres.

    Dense vectors are untouched; this only adds the sparse index that hybrid
    retrieval fuses with. Idempotent (upserts by chunk id).
    """
    from app.database.postgres import SessionLocal
    from app.repositories.chunk_repository import ChunkRepository
    from app.repositories.vector_repository import VectorRepository
    from app.services.sparse_embedding_service import SparseEmbeddingService

    sparse_service = SparseEmbeddingService()
    vector_repository = VectorRepository()

    async with SessionLocal() as db:
        chunks = await ChunkRepository(db).list_all()

    if not chunks:
        raise SystemExit("No chunks found. Ingest a corpus first.")

    # Clear first: after a reindex the chunk ids change, so a plain upsert would
    # leave orphaned points from earlier generations.
    await vector_repository.recreate_sparse_collection()

    print(f"Indexing {len(chunks)} chunks into the BM25 sparse collection...")

    embeddings = await sparse_service.embed_documents(
        [chunk.content for chunk in chunks]
    )

    for chunk, (indices, values) in zip(chunks, embeddings):
        await vector_repository.upsert_sparse_embedding(
            chunk_id=chunk.id,
            article_id=chunk.article_id,
            indices=indices,
            values=values,
        )

    print(f"Done. Sparse collection '{vector_repository.SPARSE_COLLECTION_NAME}' ready.")


async def _reindex(chunk_size: int, chunk_overlap: int) -> None:
    """Rebuild chunks + dense vectors from the existing articles.

    Destructive: deletes all chunks (Postgres) and dense vectors (Qdrant), then
    re-chunks every article with the given size/overlap and re-embeds. Articles
    (the frozen corpus) are untouched. This is the base step of the chunking
    sweep — the retrieval config (e5-instruct + rerank) is unchanged.
    """
    from app.database.postgres import SessionLocal
    from app.repositories.article_repository import ArticleRepository
    from app.repositories.chunk_repository import ChunkRepository
    from app.repositories.vector_repository import VectorRepository
    from app.services.chunk_service import ChunkService
    from app.services.embedding_service import EmbeddingService
    from app.services.llama_index_chunking_service import LlamaIndexChunkingService

    embedding_service = EmbeddingService()
    vector_repository = VectorRepository()

    print(f"Reindexing (chunk_size={chunk_size}, chunk_overlap={chunk_overlap}).")
    print("Clearing dense vectors (Qdrant) and chunks (Postgres)...")
    await vector_repository.recreate_dense_collection()

    total_chunks = 0
    async with SessionLocal() as db:
        chunk_repository = ChunkRepository(db)
        article_repository = ArticleRepository(db)

        await chunk_repository.delete_all()

        chunk_service = ChunkService(
            LlamaIndexChunkingService(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            ),
            chunk_repository,
        )

        articles = await article_repository.list()
        print(f"Re-chunking and embedding {len(articles)} articles...")

        for index, article in enumerate(articles, start=1):
            chunks = await chunk_service.create_chunks(article)
            if chunks:
                embeddings = await embedding_service.embed_documents(
                    [chunk.content for chunk in chunks]
                )
                for chunk, embedding in zip(chunks, embeddings):
                    await vector_repository.upsert_chunk_embedding(
                        chunk_id=chunk.id,
                        article_id=chunk.article_id,
                        embedding=embedding,
                    )
                total_chunks += len(chunks)
            if index % 50 == 0:
                print(f"  {index}/{len(articles)} articles, {total_chunks} chunks")

    print(
        f"Done: {len(articles)} articles -> {total_chunks} chunks "
        f"(size={chunk_size}, overlap={chunk_overlap})."
    )
    print(
        "Note: the BM25 sparse index is now stale (chunk ids changed). "
        "Re-run 'index-sparse' before using --hybrid."
    )


def _board() -> None:
    from evaluation.leaderboard import load_leaderboard, render_leaderboard

    print(render_leaderboard(load_leaderboard()))


def _fmt(value: float | None) -> str:
    return "NaN" if value is None else f"{value:.4f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Sports RAG evaluation harness (RAG Triad).")
    sub = parser.add_subparsers(dest="command", required=True)

    sample_parser = sub.add_parser(
        "sample",
        help="Pick N random articles, dump content, and freeze the corpus.",
    )
    sample_parser.add_argument(
        "-n", "--count",
        type=int,
        default=20,
        help="Number of random articles to sample (default: 20).",
    )

    run_parser = sub.add_parser("run", help="Run the RAG Triad over the frozen questions.")
    run_parser.add_argument(
        "-e", "--experiment",
        required=True,
        help="Name/app_id for this run (e.g. baseline, e5-instruct, sentence-window).",
    )
    run_parser.add_argument(
        "-k", "--limit",
        type=int,
        default=5,
        help="Retrieval top-k (default: 5).",
    )
    run_parser.add_argument(
        "--rerank",
        action="store_true",
        help="Rerank a larger candidate pool down to top-k (needs a Together "
             "rerank endpoint; model via RERANK_MODEL).",
    )
    run_parser.add_argument(
        "--candidates",
        type=int,
        default=20,
        help="Candidate pool size fetched before reranking (default: 20).",
    )
    run_parser.add_argument(
        "--window",
        type=int,
        default=0,
        help="Sentence-window: expand each final chunk with +/-N neighbours "
             "(default: 0 = off).",
    )
    run_parser.add_argument(
        "--hybrid",
        action="store_true",
        help="Hybrid retrieval: fuse dense + BM25 sparse (needs 'index-sparse').",
    )
    run_parser.add_argument(
        "--hyde",
        action="store_true",
        help="HyDE: embed a hypothetical LLM-written passage instead of the raw query.",
    )
    run_parser.add_argument(
        "--multi-query",
        action="store_true",
        help="Multi-query: rephrase into variants, search each, fuse (RRF).",
    )
    run_parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Skip generation + triad judging; compute only recall@k. "
             "(HyDE still calls the LLM to build the query.)",
    )

    sub.add_parser(
        "index-sparse",
        help="Backfill the BM25 sparse collection from all chunks (for --hybrid).",
    )

    reindex_parser = sub.add_parser(
        "reindex",
        help="Rebuild chunks + dense vectors with a given chunk size/overlap "
             "(chunking sweep). Destructive; keeps articles.",
    )
    reindex_parser.add_argument(
        "--chunk-size",
        type=int,
        required=True,
        help="Target chunk size in tokens (e.g. 256, 350, 512).",
    )
    reindex_parser.add_argument(
        "--chunk-overlap",
        type=int,
        required=True,
        help="Chunk overlap in tokens (e.g. 32, 50, 64).",
    )

    sub.add_parser("board", help="Print the leaderboard of all experiments.")

    args = parser.parse_args()

    if args.command == "sample":
        asyncio.run(_sample(args.count))
    elif args.command == "run":
        asyncio.run(_run(
            args.experiment,
            args.limit,
            args.rerank,
            args.candidates,
            args.window,
            args.hybrid,
            args.hyde,
            args.multi_query,
            args.retrieval_only,
        ))
    elif args.command == "index-sparse":
        asyncio.run(_index_sparse())
    elif args.command == "reindex":
        asyncio.run(_reindex(args.chunk_size, args.chunk_overlap))
    elif args.command == "board":
        _board()


if __name__ == "__main__":
    main()
