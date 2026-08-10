from fastapi import FastAPI

from app.api.routers.articles import router as article_router
from app.api.routers.news_sources import router as news_source_router
from app.api.routers.embeddings import router as embedding_router
from app.api.routers.vectors import router as vector_router
from app.api.routers.retrievals import router as retrieval_router
from app.api.routers.chat import router as chat_router

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ArticleAlreadyExists,
    ArticleNotFound,
    NewsSourceAlreadyExists,
    NewsSourceNotFound,
    UnsupportedNewsSourceType,
)

from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(lifespan=lifespan)

app.include_router(article_router)
app.include_router(news_source_router)
app.include_router(embedding_router)
app.include_router(vector_router)
app.include_router(retrieval_router)
app.include_router(chat_router)

@app.exception_handler(ArticleAlreadyExists)
async def article_exists_handler(
    request: Request,
    exc: ArticleAlreadyExists,
):
    return JSONResponse(
        status_code=409,
        content={
            "detail": str(exc)
        },
    )
    
@app.exception_handler(ArticleNotFound)
async def article_not_found_handler(
    request: Request,
    exc: ArticleNotFound,
):
    return JSONResponse(
        status_code=404,
        content={
            "detail": str(exc)
        },
    )

@app.exception_handler(NewsSourceAlreadyExists)
async def news_source_exists_handler(
    request: Request,
    exc: NewsSourceAlreadyExists,
):
    return JSONResponse(
        status_code=409,
        content={
            "detail": str(exc)
        },
    )

@app.exception_handler(NewsSourceNotFound)
async def news_source_not_found_handler(
    request: Request,
    exc: NewsSourceNotFound,
):
    return JSONResponse(
        status_code=404,
        content={
            "detail": str(exc)
        },
    )

@app.exception_handler(UnsupportedNewsSourceType)
async def unsupported_news_source_type_handler(
    request: Request,
    exc: UnsupportedNewsSourceType,
):
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc)
        },
    )
