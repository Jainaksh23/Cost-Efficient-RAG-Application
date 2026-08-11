"""
ingestion/chunker.py
Sliding-window character-based text splitter.

Window:   CHUNK_SIZE characters
Step:     CHUNK_SIZE - CHUNK_OVERLAP characters
Each chunk carries a zero-based chunk_index within its source document.
"""
from __future__ import annotations

from dataclasses import dataclass

import config


@dataclass
class Chunk:
    text: str
    chunk_index: int       # zero-based position within source document
    source_file: str
    file_type: str
    ingested_at: str


def chunk_text(text: str, metadata: dict) -> list[Chunk]:
    """
    Split *text* into overlapping chunks.

    Args:
        text:     Full plain-text content of the document.
        metadata: Dict with source_file, file_type, ingested_at.

    Returns:
        Ordered list of Chunk objects. Empty list if text is blank.
    """
    size    = config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP
    step    = size - overlap

    if step <= 0:
        raise ValueError(
            f"CHUNK_OVERLAP ({overlap}) must be strictly less than "
            f"CHUNK_SIZE ({size})."
        )

    text = text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    idx = 0
    pos = 0

    while pos < len(text):
        window_text = text[pos : pos + size].strip()
        if window_text:                        # skip windows that are pure whitespace
            chunks.append(
                Chunk(
                    text=window_text,
                    chunk_index=idx,
                    source_file=metadata["source_file"],
                    file_type=metadata["file_type"],
                    ingested_at=metadata["ingested_at"],
                )
            )
            idx += 1
        pos += step

    return chunks
