import os

from together import AsyncTogether


class EmbeddingService:

    MODEL_NAME = "intfloat/multilingual-e5-large-instruct"

    # Maximum number of inputs sent to the embeddings API per request.
    MAX_BATCH = 100

    def __init__(self):
        self.client = AsyncTogether(
            api_key=os.getenv("TOGETHER_API_KEY")
        )

    #Os métodos embed_document() e embed_query() são iguais.
    #Mas, se amanhã mudarmos para um modelo que exija prompts diferentes
    #ou algum pré-processamento específico para documentos e consultas, não precisaremos alterar o restante do projeto.
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

        response = await self.client.embeddings.create(
            model=self.MODEL_NAME,
            input=query,
        )

        return response.data[0].embedding
