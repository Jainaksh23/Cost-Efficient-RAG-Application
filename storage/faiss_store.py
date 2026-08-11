"""
storage/faiss_store.py
Thin wrapper around faiss.IndexFlatL2(384).

Design notes (from architecture doc Section 3.1):
- IndexFlatL2: exact L2 search, no training, no approximation error.
- faiss_id for a vector = index.ntotal BEFORE the add() call.
- The index is saved to disk explicitly after every successful ingest batch.
- On process restart, load_or_create() restores ntotal from the saved file.
"""
from __future__ import annotations

import numpy as np
import faiss

import config

# Module-level singleton — shared across all calls within one process.
_index: faiss.IndexFlatL2 | None = None


# ── Index lifecycle ───────────────────────────────────────────────────────────

def get_index() -> faiss.IndexFlatL2:
    """Return the in-memory index, loading from disk or creating fresh if needed."""
    global _index
    if _index is None:
        _index = _load_or_create()
    return _index


def _load_or_create() -> faiss.IndexFlatL2:
    path = config.FAISS_INDEX_PATH
    if path.exists():
        idx = faiss.read_index(str(path))
        if idx.d != config.EMBED_DIMENSION:
            raise ValueError(
                f"Saved FAISS index has dimension {idx.d}; "
                f"expected {config.EMBED_DIMENSION}. "
                f"Delete {path} and re-ingest to reset."
            )
        print(
            f"[FAISS] Loaded index from {path}  "
            f"(ntotal={idx.ntotal}, dim={idx.d})"
        )
        return idx

    # First run — create an empty flat index
    path.parent.mkdir(parents=True, exist_ok=True)
    idx = faiss.IndexFlatL2(config.EMBED_DIMENSION)
    print(f"[FAISS] Created new IndexFlatL2(dim={config.EMBED_DIMENSION})")
    return idx


def reset() -> None:
    """
    Drop the in-memory reference so the next get_index() call reloads from disk.
    Useful for testing or after external writes to the index file.
    """
    global _index
    _index = None


# ── Write operations ──────────────────────────────────────────────────────────

def add_vectors(vectors: np.ndarray) -> list[int]:
    """
    Add N vectors to the index.

    Args:
        vectors: float32 array of shape (N, 384).

    Returns:
        List of assigned faiss_ids [start, start+1, ..., start+N-1]
        where start = index.ntotal before the add.

    Note: This modifies the in-memory index only. Call save() to persist.
    """
    idx = get_index()
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)

    start_id = int(idx.ntotal)
    idx.add(vectors)
    return list(range(start_id, int(idx.ntotal)))


def save() -> None:
    """Flush the in-memory index to disk at FAISS_INDEX_PATH."""
    idx = get_index()
    path = config.FAISS_INDEX_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(idx, str(path))


# ── Read operations (used by retrieval layer) ─────────────────────────────────

def search(query_vector: np.ndarray, k: int,
           id_selector: faiss.IDSelector | None = None) -> tuple[list[int], list[float]]:
    """
    Search for the top-k nearest neighbours of query_vector.

    Args:
        query_vector: float32 array of shape (384,) or (1, 384).
        k:            Number of results to return.
        id_selector:  Optional FAISS IDSelector to restrict search to a subset.

    Returns:
        (faiss_ids, distances) — both lists of length <= k.
        faiss_ids of -1 indicate unfilled slots (fewer than k results).
    """
    idx = get_index()
    qv = np.asarray(query_vector, dtype=np.float32).reshape(1, -1)
    k = min(k, int(idx.ntotal))
    if k == 0:
        return [], []

    if id_selector is not None:
        params = faiss.SearchParameters(sel=id_selector)
        D, I = idx.search(qv, k, params=params)
    else:
        D, I = idx.search(qv, k)

    ids   = [int(i)   for i in I[0] if int(i) != -1]
    dists = [float(d) for i, d in zip(I[0], D[0]) if int(i) != -1]
    return ids, dists


def ntotal() -> int:
    """Return the number of vectors currently in the index."""
    return int(get_index().ntotal)
