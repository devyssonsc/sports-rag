from datetime import datetime
from pydantic import BaseModel, ConfigDict

class FeedCreate(BaseModel):
    name: str
    url: str
    
class FeedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    last_fetched_at: datetime | None
    created_at: datetime