from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from app.database.postgres import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    feed_id: Mapped[int | None] = mapped_column(
        ForeignKey("feeds.id"),
        nullable=True
    )

    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)

    source: Mapped[str] = mapped_column(String(100), nullable=False)

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    
    chunks = relationship(
        "Chunk",
        back_populates="article",
        cascade="all, delete-orphan",
    )