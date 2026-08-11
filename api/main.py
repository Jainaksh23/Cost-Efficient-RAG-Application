from fastapi import FastAPI
from contextlib import asynccontextmanager

import config
from embedding.embedder import embed
import storage.faiss_store as faiss_store
import storage.sqlite_store as sql_store
from api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load FAISS index + SQLite + embedding model once at startup
    sql_store.init_db()
    # Embed a dummy string to load the sentence-transformer model into memory
    print("Pre-loading embedding model at startup...")
    _ = embed(["startup load"])
    print(f"Startup complete. FAISS index size: {faiss_store.ntotal()}, SQLite chunks: {sql_store.count_chunks()}")
    yield
    print("Shutting down API...")

app = FastAPI(title="Vaultly RAG API", lifespan=lifespan)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=config.API_HOST, port=config.API_PORT, reload=True)
