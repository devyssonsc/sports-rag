from pydantic import BaseModel

class ChunkResponse(BaseModel):
    id: int
    index: int
    length: int
    content: str
    
