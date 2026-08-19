"""HyDE (Hypothetical Document Embeddings) as a query transform.

Instead of embedding the raw question, HyDE asks the LLM to write a hypothetical
answer passage and embeds *that*. A hypothetical passage reads like a real
article, so its vector lands nearer the real documents than a question's would —
closing the query/document space mismatch and improving retrieval recall.

The hypothetical passage is embedded with the *document* encoder (raw text, no e5
instruction prefix), so it shares the space of the indexed passages.

Kept in evaluation/ (not app/services) because it is an experiment: it adds an
LLM call to every query, so it only moves to production if it earns its cost.
"""

from __future__ import annotations

from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService

from evaluation._retry import with_retry

HYDE_PROMPT = """\
Write a short, factual passage (2-4 sentences) from a football news article that
directly answers the question below. Write it as if it were an excerpt from the
article itself — no preamble, no caveats, just the passage.

Question: {query}

Passage:"""


class HydeService:
    """Duck-typed to stand in for the query-embedding step in RetrievalService."""

    def __init__(
        self,
        llm_service: LLMService,
        embedding_service: EmbeddingService,
    ):
        self.llm_service = llm_service
        self.embedding_service = embedding_service

    async def embed_query(self, query: str) -> list[float]:
        hypothetical = await with_retry(
            lambda: self.llm_service.generate(HYDE_PROMPT.format(query=query))
        )
        # Document-side embedding: the hypothetical passage is document-like.
        return await self.embedding_service.embed_document(hypothetical)
