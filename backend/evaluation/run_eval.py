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


async def _run(experiment: str, limit: int) -> None:
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
    print(f"\nRunning experiment '{experiment}' over {len(questions)} questions (top-{limit})...\n")

    summary = await evaluate(experiment, questions, limit)
    detail_path = save_run(summary)

    print("\n=== RUN SUMMARY ===")
    print(f"experiment        : {summary.experiment}")
    print(f"context relevance : {_fmt(summary.mean_context_relevance)}")
    print(f"groundedness      : {_fmt(summary.mean_groundedness)}")
    print(f"answer relevance  : {_fmt(summary.mean_answer_relevance)}")
    print(f"mean latency (s)  : {summary.mean_latency_seconds}")
    print(f"detail written to : {detail_path}")


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

    sub.add_parser("board", help="Print the leaderboard of all experiments.")

    args = parser.parse_args()

    if args.command == "sample":
        asyncio.run(_sample(args.count))
    elif args.command == "run":
        asyncio.run(_run(args.experiment, args.limit))
    elif args.command == "board":
        _board()


if __name__ == "__main__":
    main()
