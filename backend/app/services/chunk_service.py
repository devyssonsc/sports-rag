from app.models.article import Article
from app.models.chunk import Chunk
from app.repositories.chunk_repository import ChunkRepository
from app.services.llama_index_chunking_service import LlamaIndexChunkingService


class ChunkService:

    def __init__(
        self,
        chunking_service: LlamaIndexChunkingService,
        chunk_repository: ChunkRepository,
    ) -> None:
        self.chunking_service = chunking_service
        self.chunk_repository = chunk_repository
        
    def create_chunks(
        self,
        article: Article,
    ) -> list[Chunk]:

        if article.content is None:
            return []

        chunks = self.chunking_service.split(article.content)

        chunk_entities = []

        for index, chunk_content in enumerate(chunks):

            chunk = Chunk(
                article_id=article.id,
                content=chunk_content,
                chunk_index=index,
            )

            chunk_entities.append(chunk)

        self.chunk_repository.create_many(chunk_entities)
        
        return chunk_entities