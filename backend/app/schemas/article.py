from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleCreate(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str | None
    content: str | None
    url: str
    source: str
    feed_id: int | None
    published_at: datetime | None
    created_at: datetime
    
class ArticleUpdate(BaseModel):
    title: str | None = None
    source: str | None = None
    published_at: datetime | None = None
    
from pydantic import BaseModel


class ArticleRawResponse(BaseModel):
    article_id: int
    repr: str
    content: str