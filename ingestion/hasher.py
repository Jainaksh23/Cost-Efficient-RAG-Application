"""
ingestion/hasher.py
SHA-256 idempotency hashing for chunks.

Canonical input format (from architecture doc Section 3.3):
    "{source_file}::{chunk_index}::{chunk_text_stripped}"

source_file  — basename only (path-agnostic)
chunk_index  — zero-based integer position within the source document
chunk_text   — stripped of leading/trailing whitespace before hashing
"""
import hashlib


def compute_hash(source_file: str, chunk_index: int, chunk_text: str) -> str:
    """
    Return a 64-character hex SHA-256 digest for this chunk.

    Example:
        compute_hash("install_guide.pdf", 3, "Python 3.10 or higher...")
        -> "a3f7c1d9e2b4..."
    """
    canonical = f"{source_file}::{chunk_index}::{chunk_text.strip()}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
