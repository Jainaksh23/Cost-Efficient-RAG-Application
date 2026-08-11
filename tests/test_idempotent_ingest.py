import os
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
import storage.faiss_store as faiss_store
import storage.sqlite_store as sql_store
from ingestion.pipeline import ingest_documents

def test_idempotent_reingest(tmp_path, monkeypatch):
    # Setup temporary paths for FAISS and SQLite
    temp_faiss = tmp_path / "faiss.index"
    temp_sqlite = tmp_path / "rag_metadata.db"
    
    monkeypatch.setattr(config, "FAISS_INDEX_PATH", temp_faiss)
    monkeypatch.setattr(config, "SQLITE_DB_PATH", temp_sqlite)
    
    # Also need to re-init since modules might hold state or paths
    sql_store.init_db()
    
    # Reset FAISS index in memory in case it was loaded globally
    import faiss
    faiss_store.INDEX = faiss.IndexFlatL2(384)
    faiss_store.save()
    
    # We will ingest the actual `data/` directory
    data_dir = Path(__file__).resolve().parent.parent / "data"
    docs_to_ingest = list(data_dir.glob("*.md")) + list(data_dir.glob("*.html")) + list(data_dir.glob("*.pdf"))
    
    # Run 1: Initial Ingest
    res1 = ingest_documents(docs_to_ingest)
    faiss_size_1 = faiss_store.ntotal()
    sqlite_count_1 = sql_store.count_chunks()
    
    assert res1.chunks_added > 0, "First run should add chunks"
    assert faiss_size_1 == res1.chunks_added, "FAISS should match chunks added"
    assert sqlite_count_1 == res1.chunks_added, "SQLite should match chunks added"
    
    # Run 2: Re-ingest
    res2 = ingest_documents(docs_to_ingest)
    faiss_size_2 = faiss_store.ntotal()
    sqlite_count_2 = sql_store.count_chunks()
    
    # Asserts
    assert faiss_size_1 == faiss_size_2, "FAISS size should not change on re-ingest"
    assert sqlite_count_1 == sqlite_count_2, "SQLite count should not change on re-ingest"
    assert res2.chunks_added == 0, "No new chunks should be added on re-ingest"
    assert res2.chunks_skipped == res1.chunks_added, "All chunks should be skipped as duplicates"
