from pydantic import BaseModel


class IngestionResult(BaseModel):
    processed: int
    inserted: int
    ignored: int