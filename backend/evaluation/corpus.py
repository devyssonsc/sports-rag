"""Freeze the evaluation corpus and sample articles for question authoring.

Two distinct concerns, deliberately kept separate:

* The FROZEN CORPUS (``corpus_snapshot.json``) records the WHOLE article set —
  all ids plus total counts. Retrieval searches the entire Qdrant collection, so
  the thing that must stay fixed between experiments is the full corpus. The
  snapshot lets ``run`` detect drift (articles added/removed/swapped, re-chunk).

* The SAMPLE (``sample_articles.md``) is just N random articles dumped with their
  full content, so you can read them and write grounded questions. The sampled
  ids are also stored in the snapshot as provenance (which articles the questions
  were authored from) — but they do NOT limit retrieval.

Workflow:
    1. ``sample -n N``  -> freezes the full corpus + dumps N articles to read.
    2. write questions in ``questions.txt`` from ``sample_articles.md``.
    3. ``run``          -> measures the pipeline, warns on corpus drift.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.chunk import Chunk

SNAPSHOT_PATH = Path(__file__).parent / "corpus_snapshot.json"
SAMPLE_READABLE_PATH = Path(__file__).parent / "sample_articles.md"


async def counts(db: AsyncSession) -> tuple[int, int]:
    """Return (total article count, total chunk count) in the database."""
    article_count = await db.scalar(select(func.count(Article.id)))
    chunk_count = await db.scalar(select(func.count(Chunk.id)))
    return int(article_count or 0), int(chunk_count or 0)


async def all_article_ids(db: AsyncSession) -> list[int]:
    """Return every article id, sorted (the full frozen corpus)."""
    result = await db.scalars(select(Article.id).order_by(Article.id))
    return list(result.all())


async def sample_articles(db: AsyncSession, n: int) -> list[Article]:
    """Pick ``n`` random articles for question authoring (server-side random)."""
    statement = select(Article).order_by(func.random()).limit(n)
    result = await db.scalars(statement)
    return list(result.all())


def build_snapshot(
    article_ids: list[int],
    chunk_count: int,
    sample_ids: list[int],
) -> dict:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "article_count": len(article_ids),
        "chunk_count": chunk_count,
        "article_ids": article_ids,
        # Provenance only: the articles the questions were authored from. Does not
        # restrict retrieval, which always searches the whole collection.
        "authored_from_sample_ids": sample_ids,
    }


def write_snapshot(snapshot: dict, path: Path = SNAPSHOT_PATH) -> None:
    path.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_sample_readable(
    sampled: list[Article],
    path: Path = SAMPLE_READABLE_PATH,
) -> None:
    """Dump the sampled articles' full content for question authoring."""
    parts: list[str] = [
        "# Sampled articles for evaluation question authoring",
        "",
        f"{len(sampled)} articles. Write questions in `questions.txt` that are "
        "answerable from the content below.",
        "",
    ]

    for article in sampled:
        published = (
            article.published_at.isoformat()
            if article.published_at
            else "unknown"
        )
        parts.extend(
            [
                "---",
                "",
                f"## [{article.id}] {article.title}",
                "",
                f"- source: {article.source}",
                f"- published_at: {published}",
                f"- url: {article.url}",
                "",
                (article.content or "(no content)").strip(),
                "",
            ]
        )

    path.write_text("\n".join(parts), encoding="utf-8")


def diff_against(
    snapshot: dict,
    current_article_ids: list[int],
    current_chunk_count: int,
) -> list[str]:
    """Return drift warnings (empty == corpus unchanged)."""
    warnings: list[str] = []

    frozen_ids = set(snapshot.get("article_ids", []))
    current_ids = set(current_article_ids)

    added = current_ids - frozen_ids
    removed = frozen_ids - current_ids

    if added:
        warnings.append(f"{len(added)} article(s) added since snapshot: {sorted(added)}")
    if removed:
        warnings.append(f"{len(removed)} article(s) removed since snapshot: {sorted(removed)}")

    if snapshot.get("chunk_count") != current_chunk_count:
        warnings.append(
            "chunk count changed "
            f"({snapshot.get('chunk_count')} -> {current_chunk_count}) "
            "— expected only if you re-chunked on purpose."
        )

    return warnings
