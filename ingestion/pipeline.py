"""
ingestion/pipeline.py
End-to-end ingestion orchestrator.

Flow (from architecture doc Section 1.1):
  1. Load each file via the appropriate loader.
  2. Chunk the text with the sliding-window chunker.
  3. Compute SHA-256 hash for each chunk; skip if already in SQLite.
  4. Embed all new chunks in one batched call.
  5. Assign provisional faiss_ids (current_ntotal + i for each new chunk).
  6. Attempt SQLite batch insert (atomic transaction).
     - If SQLite fails: raise — FAISS index is never touched.
  7. If SQLite succeeds: add vectors to FAISS and flush to disk.

This ordering means SQLite is the gate: FAISS is only updated after a
successful commit, so the two stores are always consistent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ingestion.loaders import load_document
from ingestion.chunker import chunk_text, Chunk
from ingestion.hasher import compute_hash
from embedding.embedder import embed
import storage.sqlite_store as sql_store
import storage.faiss_store as faiss_store


@dataclass
class IngestResult:
    files_processed: int = 0
    chunks_added: int    = 0
    chunks_skipped: int  = 0
    faiss_size: int      = 0
    sqlite_count: int    = 0


def ingest_documents(file_paths: list[Path | str]) -> IngestResult:
    """
    Ingest a list of document files into the FAISS + SQLite knowledge base.

    Args:
        file_paths: Iterable of Path objects or string paths to files.

    Returns:
        IngestResult with counts of files, chunks added, chunks skipped,
        and the final FAISS index size and SQLite row count.
    """
    sql_store.init_db()   # no-op if table already exists

    result = IngestResult()
    new_chunks: list[Chunk]  = []
    new_hashes: list[str]    = []

    # ── Phase 1: Load, chunk, hash-check ─────────────────────────────────────
    for fp in file_paths:
        fp = Path(fp)
        try:
            text, meta = load_document(fp)
        except Exception as exc:
            print(f"  [WARN] Skipping {fp.name}: {exc}")
            continue

        result.files_processed += 1
        chunks = chunk_text(text, meta)

        for chunk in chunks:
            h = compute_hash(chunk.source_file, chunk.chunk_index, chunk.text)
            if sql_store.hash_exists(h):
                result.chunks_skipped += 1
            else:
                new_chunks.append(chunk)
                new_hashes.append(h)

    # ── Short-circuit if nothing new ─────────────────────────────────────────
    if not new_chunks:
        result.faiss_size   = faiss_store.ntotal()
        result.sqlite_count = sql_store.count_chunks()
        return result

    # ── Phase 2: Embed all new chunks in one batched call ────────────────────
    print(f"  [Embed] Embedding {len(new_chunks)} new chunks...")
    vectors: np.ndarray = embed([c.text for c in new_chunks])   # (N, 384), float32

    # ── Phase 3: Assign provisional faiss_ids and build SQLite rows ───────────
    base_id = faiss_store.ntotal()   # snapshot BEFORE any add
    rows = [
        {
            "faiss_id":     base_id + i,
            "content_hash": h,
            "source_file":  chunk.source_file,
            "file_type":    chunk.file_type,
            "chunk_index":  chunk.chunk_index,
            "chunk_text":   chunk.text,
            "token_count":  len(chunk.text) // 4,   # rough approximation
            "ingested_at":  chunk.ingested_at,
        }
        for i, (chunk, h) in enumerate(zip(new_chunks, new_hashes))
    ]

    # ── Phase 4: SQLite transaction (GATE) ────────────────────────────────────
    # If this raises, FAISS is untouched — stores remain consistent.
    try:
        sql_store.insert_chunks(rows)
    except Exception as exc:
        raise RuntimeError(
            f"SQLite insert failed — FAISS index was NOT modified. "
            f"Stores remain consistent. Error: {exc}"
        ) from exc

    # ── Phase 5: FAISS add + persist ─────────────────────────────────────────
    # Only reached if SQLite commit succeeded.
    faiss_store.add_vectors(vectors)
    faiss_store.save()

    result.chunks_added  = len(new_chunks)
    result.faiss_size    = faiss_store.ntotal()
    result.sqlite_count  = sql_store.count_chunks()
    return result
