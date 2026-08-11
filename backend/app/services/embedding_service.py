import os

from together import AsyncTogether


class EmbeddingService:

    MODEL_NAME = "intfloat/multilingual-e5-large-instruct"

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

    async def embed_query(
        self,
        query: str,
    ) -> list[float]:

        response = await self.client.embeddings.create(
            model=self.MODEL_NAME,
            input=query,
        )

        return response.data[0].embedding
