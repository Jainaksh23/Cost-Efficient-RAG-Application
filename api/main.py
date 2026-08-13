import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MALLOC_ARENA_MAX"] = "2"

import asyncio
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

async def background_startup():
    data_dir = Path("data")
    faiss_path = data_dir / "faiss.index"
    db_path = data_dir / "rag_metadata.db"
    
    try:
        if not faiss_path.exists() or not db_path.exists():
            print("Existing index or DB not found. Running auto-ingestion in background...")
            doc_files = [f for f in data_dir.iterdir() if f.is_file()]
            # Run blocking ingestion in a thread
            res = await asyncio.to_thread(ingest_documents, doc_files)
            print(f"Auto-ingestion complete: {res.files_processed} files processed, {res.chunks_added} chunks added.")
        else:
            print("Existing index and DB found. Loading...")

        print("Pre-loading embedding model at startup...")
        await asyncio.to_thread(embed, ["startup load"])
        print(f"Startup complete. FAISS index size: {faiss_store.ntotal()}, SQLite chunks: {sql_store.count_chunks()}")
    except Exception as e:
        print(f"Background startup failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load FAISS index + SQLite + embedding model once at startup
    sql_store.init_db()
    
    # Launch heavy background work so uvicorn can bind to the port immediately!
    asyncio.create_task(background_startup())
    
    yield
    print("Shutting down API...")

app = FastAPI(title="Vaultly RAG API", lifespan=lifespan)

app.include_router(router)

# Mount static files at / so index.html serves directly
app.mount("/", StaticFiles(directory="static", html=True), name="static")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=config.API_HOST, port=config.API_PORT, reload=True)
