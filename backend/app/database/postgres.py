from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.settings import settings

from sqlalchemy.orm import sessionmaker

from sqlalchemy.orm import Session


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

engine = create_engine(
    settings.postgres_url,
    echo=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass