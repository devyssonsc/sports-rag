from pydantic import BaseModel

class ChunkResponse(BaseModel):
    index: int
    length: int
    content: str
    
