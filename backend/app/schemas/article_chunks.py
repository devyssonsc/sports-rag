from pydantic import BaseModel

from app.schemas.chunk import ChunkResponse
 
class ArticleChunksResponse(BaseModel):
    article_id: int
    title: str
    content_length: int
    chunk_count: int
    chunks: list[ChunkResponse]