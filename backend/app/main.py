from fastapi import FastAPI

from app.api.routers.articles import router as article_router
from app.api.routers.feeds import router as feed_router

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ArticleAlreadyExists,
    ArticleNotFound,
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
app.include_router(feed_router)

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