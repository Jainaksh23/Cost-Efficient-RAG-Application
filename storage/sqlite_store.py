"""
storage/sqlite_store.py
SQLite metadata + idempotency sidecar for the FAISS index.

Schema (from architecture doc Section 3.2):
  chunks table — keyed by faiss_id (integer row ID assigned by FAISS)
  content_hash UNIQUE — hard idempotency guarantee at the DB level
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import config

# ── DDL ───────────────────────────────────────────────────────────────────────
_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS chunks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    faiss_id      INTEGER NOT NULL UNIQUE,
    content_hash  TEXT    NOT NULL UNIQUE,
    source_file   TEXT    NOT NULL,
    file_type     TEXT    NOT NULL,
    chunk_index   INTEGER NOT NULL,
    chunk_text    TEXT    NOT NULL,
    token_count   INTEGER,
    ingested_at   TEXT    NOT NULL
);
"""

_CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_chunks_file_type   ON chunks(file_type);
CREATE INDEX IF NOT EXISTS idx_chunks_source_file ON chunks(source_file);
CREATE INDEX IF NOT EXISTS idx_chunks_hash        ON chunks(content_hash);
"""

_INSERT_CHUNK = """
INSERT INTO chunks
    (faiss_id, content_hash, source_file, file_type, chunk_index,
     chunk_text, token_count, ingested_at)
VALUES
    (:faiss_id, :content_hash, :source_file, :file_type, :chunk_index,
     :chunk_text, :token_count, :ingested_at)
"""

# ── Connection factory ────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    db_path: Path = config.SQLITE_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # better concurrent read performance
    conn.execute("PRAGMA synchronous=NORMAL") # safe + faster than FULL
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Public API ────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create the chunks table and indexes if they do not already exist."""
    with _connect() as conn:
        conn.execute(_CREATE_TABLE)
        conn.executescript(_CREATE_INDEXES)


def hash_exists(content_hash: str) -> bool:
    """Return True if a chunk with this SHA-256 hash is already stored."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM chunks WHERE content_hash = ? LIMIT 1",
            (content_hash,),
        ).fetchone()
    return row is not None


def insert_chunks(rows: list[dict[str, Any]]) -> None:
    """
    Insert a batch of chunk rows in a single atomic transaction.

    Each dict must contain:
        faiss_id, content_hash, source_file, file_type,
        chunk_index, chunk_text, token_count, ingested_at

    Raises sqlite3.IntegrityError if any content_hash or faiss_id is duplicate.
    The caller (pipeline.py) treats any exception here as a signal to NOT
    add the vectors to FAISS, preserving consistency.
    """
    if not rows:
        return
    with _connect() as conn:
        conn.executemany(_INSERT_CHUNK, rows)


def get_faiss_ids_by_filter(filters: dict[str, str]) -> list[int]:
    """
    Return a list of faiss_ids matching the given metadata filters.

    Supported filter keys: "file_type", "source_file".
    Returns an empty list if filters is empty (caller decides behaviour).
    """
    if not filters:
        return []

    allowed = {"file_type", "source_file"}
    bad_keys = set(filters) - allowed
    if bad_keys:
        raise ValueError(f"Unsupported filter key(s): {bad_keys}")

    conditions = [f"{k} = ?" for k in filters]
    params = list(filters.values())
    query = "SELECT faiss_id FROM chunks WHERE " + " AND ".join(conditions)

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [r["faiss_id"] for r in rows]


def get_chunks_by_faiss_ids(faiss_ids: list[int]) -> list[dict]:
    """Fetch full chunk rows for a list of faiss_ids (for context assembly)."""
    if not faiss_ids:
        return []
    placeholders = ",".join("?" * len(faiss_ids))
    query = f"SELECT * FROM chunks WHERE faiss_id IN ({placeholders})"
    with _connect() as conn:
        rows = conn.execute(query, list(faiss_ids)).fetchall()
    return [dict(r) for r in rows]


def count_chunks() -> int:
    """Return the total number of chunk rows in the database."""
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
