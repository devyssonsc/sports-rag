from sqlalchemy.orm import Session

from app.models.chunk import Chunk


class ChunkRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, chunk: Chunk) -> Chunk:
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)

        return chunk

    def create_many(self, chunks: list[Chunk]) -> None:
        self.db.add_all(chunks)
        self.db.commit()
        
        for chunk in chunks:
            self.db.refresh(chunk)
        
    def get_by_article_id(
        self,
        article_id: int,
    ) -> list[Chunk]:

        return (
            self.db.query(Chunk)
            .filter(Chunk.article_id == article_id)
            .order_by(Chunk.chunk_index)
            .all()
        )
        
    def get_by_ids(
        self,
        chunk_ids: list[int],
    ) -> list[Chunk]:

        return (
            self.db.query(Chunk)
            .filter(Chunk.id.in_(chunk_ids))
            .all()
        )