from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.source_type import SourceType


class NewsSourceCreate(BaseModel):
    name: str
    url: str
    type: SourceType


class NewsSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    type: SourceType
    last_fetched_at: datetime | None
    created_at: datetime
