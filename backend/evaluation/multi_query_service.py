"""Multi-query expansion as a query transform.

The LLM rephrases the question into several search-query variants (different
wording, explicit entities). Retrieval runs for the original plus each variant
and the results are fused (RRF, in RetrievalService). A wider net raises recall,
especially for thematic questions that need several articles.

Unlike HyDE, this does NOT ask the model for facts it may not know — only to
rephrase the question — so it is robust when the corpus is outside the model's
knowledge.

Kept in evaluation/ (eval-only): it adds an LLM call per query, so it only moves
to production if it earns its cost.
"""

from __future__ import annotations

from app.services.llm_service import LLMService

from evaluation._retry import with_retry

EXPAND_PROMPT = """\
Generate {n} alternative search queries for retrieving football news articles that
answer the question below. Rephrase it with different wording, and include the
specific entities (clubs, players, competitions) where helpful. Return exactly {n}
queries, one per line, with no numbering and no extra text.

Question: {query}"""


class MultiQueryService:
    """Expands a question into the original plus a few rephrased variants."""

    def __init__(self, llm_service: LLMService, n: int = 3):
        self.llm_service = llm_service
        self.n = n

    async def expand(self, query: str) -> list[str]:
        raw = await with_retry(
            lambda: self.llm_service.generate(
                EXPAND_PROMPT.format(n=self.n, query=query)
            )
        )

        variants = [line.strip() for line in raw.splitlines() if line.strip()]

        # Keep the original query plus up to n distinct variants.
        expanded = [query]
        for variant in variants:
            if variant not in expanded:
                expanded.append(variant)
            if len(expanded) >= self.n + 1:
                break

        return expanded
