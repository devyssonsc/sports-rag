from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class SourceResponse(BaseModel):
    article_id: int
    article_title: str
    source: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]