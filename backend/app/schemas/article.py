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
    url: str
    source: str
    published_at: datetime
    created_at: datetime
    
class ArticleUpdate(BaseModel):
    title: str | None = None
    source: str | None = None
    published_at: datetime | None = None