import asyncio
import os

from fastembed import SparseTextEmbedding


class SparseEmbeddingService:
    """BM25 sparse embeddings via fastembed (local, ONNX, no torch).

    Sparse vectors capture exact-term overlap (player names, clubs, numbers) that
    dense embeddings blur. Used for hybrid retrieval: dense (semantic) and sparse
    (lexical) results are fused, so a query wins on either signal.
    """

    MODEL_NAME = os.getenv("SPARSE_MODEL", "Qdrant/bm25")
    CACHE_DIR = os.getenv("FASTEMBED_CACHE_PATH")

    def __init__(self):
        kwargs = {"cache_dir": self.CACHE_DIR} if self.CACHE_DIR else {}
        self.model = SparseTextEmbedding(model_name=self.MODEL_NAME, **kwargs)

    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[tuple[list[int], list[float]]]:
        """Embed passages (BM25 document side). Returns (indices, values) each."""

        def run() -> list[tuple[list[int], list[float]]]:
            return [
                ([int(i) for i in emb.indices], [float(v) for v in emb.values])
                for emb in self.model.embed(texts)
            ]

        return await asyncio.to_thread(run)

    async def embed_query(
        self,
        query: str,
    ) -> tuple[list[int], list[float]]:
        """Embed a query (BM25 query side)."""

        def run() -> tuple[list[int], list[float]]:
            emb = next(iter(self.model.query_embed(query)))
            return [int(i) for i in emb.indices], [float(v) for v in emb.values]

        return await asyncio.to_thread(run)
