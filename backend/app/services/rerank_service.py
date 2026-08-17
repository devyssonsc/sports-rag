import asyncio
import os

from fastembed.rerank.cross_encoder import TextCrossEncoder

from app.schemas.retrieval import RetrievedChunk


class RerankService:
    """Local cross-encoder reranking via fastembed (ONNX, no torch).

    A bi-encoder (embeddings) scores query and chunk independently; a
    cross-encoder reads the (query, chunk) pair together and judges relevance far
    more accurately. It cannot be precomputed, so it runs only over a small
    candidate set produced by the embedding search (retrieve-then-rerank).

    The default model is English (matching the corpus); override with RERANK_MODEL.
    The ONNX model is downloaded on first use and runs on CPU.
    """

    MODEL_NAME = os.getenv("RERANK_MODEL", "Xenova/ms-marco-MiniLM-L-6-v2")

    def __init__(self):
        # Loads (and, on first use, downloads) the ONNX model once.
        self.encoder = TextCrossEncoder(model_name=self.MODEL_NAME)

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_n: int,
    ) -> list[RetrievedChunk]:
        """Return the ``top_n`` chunks most relevant to ``query``, reordered.

        The returned chunks carry the reranker's relevance score in ``score``.
        """
        if not chunks:
            return chunks

        documents = [chunk.content for chunk in chunks]

        # rerank is CPU-bound; offload it so it doesn't block the event loop.
        scores = await asyncio.to_thread(
            lambda: list(self.encoder.rerank(query, documents))
        )

        ranked = sorted(
            zip(chunks, scores),
            key=lambda pair: pair[1],
            reverse=True,
        )

        return [
            chunk.model_copy(update={"score": float(score)})
            for chunk, score in ranked[:top_n]
        ]
