from fastapi import FastAPI

app = FastAPI(
    title="Sports RAG API",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "Sports RAG API via Docker Compose!"
    }