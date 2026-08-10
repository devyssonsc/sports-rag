from datetime import datetime

from pydantic import BaseModel


class RetrievalRequest(BaseModel):
    query: str
    limit: int = 5


class RetrievedChunk(BaseModel):
    chunk_id: int
    article_id: int
    article_title: str
    chunk_index: int
    score: float
    source: str
    published_at: datetime | None = None
    content: str


class RetrievalResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]