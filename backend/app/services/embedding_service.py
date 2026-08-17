import os

from together import AsyncTogether


class EmbeddingService:

    MODEL_NAME = "intfloat/multilingual-e5-large-instruct"

    # Maximum number of inputs sent to the embeddings API per request.
    MAX_BATCH = 100

    # The e5 *-instruct models are asymmetric: passages are embedded as raw text,
    # while queries must carry an instruction prefix in the form
    # "Instruct: {task}\nQuery: {text}". This aligns the query vector with the
    # "query space" the model was trained on. Documents are NOT prefixed.
    QUERY_INSTRUCTION = (
        "Given a football news question, "
        "retrieve news passages that answer it"
    )

    def __init__(self):
        self.client = AsyncTogether(
            api_key=os.getenv("TOGETHER_API_KEY")
        )

    # embed_document embeds passages as raw text (the document side of e5).
    # embed_query prefixes the instruction (the query side). They are now
    # deliberately different — that asymmetry is what e5-instruct expects.
    async def embed_document(
        self,
        text: str,
    ) -> list[float]:

        response = await self.client.embeddings.create(
            model=self.MODEL_NAME,
            input=text,
        )

        return response.data[0].embedding

    async def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Embed several documents, batching them into few API requests.

        Returns one embedding per input, in the same order as ``texts``.
        """
        embeddings: list[list[float]] = []

        for start in range(0, len(texts), self.MAX_BATCH):
            batch = texts[start:start + self.MAX_BATCH]

            response = await self.client.embeddings.create(
                model=self.MODEL_NAME,
                input=batch,
            )

            # Order by index so the result aligns with the input order.
            ordered = sorted(response.data, key=lambda item: item.index)
            embeddings.extend(item.embedding for item in ordered)

        return embeddings

    async def embed_query(
        self,
        query: str,
    ) -> list[float]:

        formatted = f"Instruct: {self.QUERY_INSTRUCTION}\nQuery: {query}"

        response = await self.client.embeddings.create(
            model=self.MODEL_NAME,
            input=formatted,
        )

        return response.data[0].embedding
