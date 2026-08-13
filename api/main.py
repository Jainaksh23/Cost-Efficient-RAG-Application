import os
# Memory optimizations for 512MB RAM limit (Render free tier)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MALLOC_ARENA_MAX"] = "2"

import torch
torch.set_num_threads(1)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

import config
from embedding.embedder import embed
import storage.faiss_store as faiss_store
import storage.sqlite_store as sql_store
from ingestion.pipeline import ingest_documents
from api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load FAISS index + SQLite + embedding model once at startup
    sql_store.init_db()
    
    data_dir = Path("data")
    faiss_path = data_dir / "faiss.index"
    db_path = data_dir / "rag_metadata.db"
    
    if not faiss_path.exists() or not db_path.exists():
        print("Existing index or DB not found. Running auto-ingestion...")
        doc_files = [f for f in data_dir.iterdir() if f.is_file()]
        res = ingest_documents(doc_files)
        print(f"Auto-ingestion complete: {res.files_processed} files processed, {res.chunks_added} chunks added.")
    else:
        print("Existing index and DB found. Loading...")

    # Embed a dummy string to load the sentence-transformer model into memory
    print("Pre-loading embedding model at startup...")
    _ = embed(["startup load"])
    print(f"Startup complete. FAISS index size: {faiss_store.ntotal()}, SQLite chunks: {sql_store.count_chunks()}")
    yield
    print("Shutting down API...")

app = FastAPI(title="Vaultly RAG API", lifespan=lifespan)

app.include_router(router)

# Mount static files at / so index.html serves directly
app.mount("/", StaticFiles(directory="static", html=True), name="static")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=config.API_HOST, port=config.API_PORT, reload=True)
