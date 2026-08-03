from pydantic import BaseModel

from app.schemas.chunk import ChunkResponse
 
class ArticleChunksResponse(BaseModel):
    article_id: int
    title: str
    chunk_count: int
    chunks: list[ChunkResponse]