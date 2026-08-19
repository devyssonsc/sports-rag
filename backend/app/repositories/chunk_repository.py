from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk


class ChunkRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, chunk: Chunk) -> Chunk:
        self.db.add(chunk)
        await self.db.commit()
        await self.db.refresh(chunk)

        return chunk

    async def create_many(self, chunks: list[Chunk]) -> None:
        self.db.add_all(chunks)
        await self.db.commit()

        for chunk in chunks:
            await self.db.refresh(chunk)

    async def get_by_article_id(
        self,
        article_id: int,
    ) -> list[Chunk]:

        statement = (
            select(Chunk)
            .where(Chunk.article_id == article_id)
            .order_by(Chunk.chunk_index)
        )
        result = await self.db.scalars(statement)
        return list(result.all())

    async def get_by_ids(
        self,
        chunk_ids: list[int],
    ) -> list[Chunk]:

        statement = select(Chunk).where(Chunk.id.in_(chunk_ids))
        result = await self.db.scalars(statement)
        return list(result.all())

    async def list_all(self) -> list[Chunk]:
        statement = select(Chunk).order_by(Chunk.id)
        result = await self.db.scalars(statement)
        return list(result.all())

    async def delete_all(self) -> None:
        await self.db.execute(delete(Chunk))
        await self.db.commit()
