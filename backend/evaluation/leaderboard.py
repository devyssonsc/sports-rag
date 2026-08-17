"""Persist run results and render the leaderboard.

Each run writes a detailed JSON (every question, score and judge reason) plus one
appended row in ``leaderboard.jsonl``. The leaderboard is the objective,
side-by-side comparison of experiments — the whole point of the course loop.
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.schemas import RunSummary

RESULTS_DIR = Path(__file__).parent / "results"
LEADERBOARD_PATH = RESULTS_DIR / "leaderboard.jsonl"


def save_run(summary: RunSummary) -> Path:
    """Write the full per-question detail and append the leaderboard row."""
    RESULTS_DIR.mkdir(exist_ok=True)

    safe_experiment = summary.experiment.replace("/", "-").replace(" ", "_")
    safe_time = summary.timestamp.replace(":", "-")
    detail_path = RESULTS_DIR / f"{safe_experiment}__{safe_time}.json"

    detail_path.write_text(
        summary.model_dump_json(indent=2),
        encoding="utf-8",
    )

    row = {
        "experiment": summary.experiment,
        "timestamp": summary.timestamp,
        "questions": summary.question_count,
        "context_relevance": summary.mean_context_relevance,
        "groundedness": summary.mean_groundedness,
        "answer_relevance": summary.mean_answer_relevance,
        "latency_s": summary.mean_latency_seconds,
    }
    with LEADERBOARD_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(row, ensure_ascii=False) + "\n")

    return detail_path


def load_leaderboard() -> list[dict]:
    if not LEADERBOARD_PATH.exists():
        return []
    return [
        json.loads(line)
        for line in LEADERBOARD_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def render_leaderboard(rows: list[dict]) -> str:
    if not rows:
        return "(leaderboard is empty — run an experiment first)"

    def fmt(value) -> str:
        return "  NaN" if value is None else f"{value:5.3f}"

    header = (
        f"{'experiment':<28} {'ctx.rel':>8} {'ground':>8} "
        f"{'ans.rel':>8} {'lat(s)':>8} {'#q':>4}"
    )
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(
            f"{row['experiment']:<28} "
            f"{fmt(row.get('context_relevance')):>8} "
            f"{fmt(row.get('groundedness')):>8} "
            f"{fmt(row.get('answer_relevance')):>8} "
            f"{row.get('latency_s', 0):>8.2f} "
            f"{row.get('questions', 0):>4}"
        )
    return "\n".join(lines)
