"""
embedding/embedder.py
Wraps sentence-transformers/all-MiniLM-L6-v2.
- Lazy singleton: the model is loaded once on first call.
- Batched encoding controlled by EMBED_BATCH_SIZE.
- Returns L2-normalised float32 arrays of shape (N, 384).
"""
from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

import config

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"[Embedder] Loading model: {config.EMBED_MODEL}")
        _model = SentenceTransformer(config.EMBED_MODEL)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """
    Embed a list of text strings.

    Args:
        texts: List of strings to embed.

    Returns:
        np.ndarray of shape (N, 384), dtype float32, L2-normalised.
        Returns an empty (0, 384) array for an empty input list.
    """
    if not texts:
        return np.empty((0, config.EMBED_DIMENSION), dtype=np.float32)

    model = _get_model()
    batch_size = config.EMBED_BATCH_SIZE
    batches: list[np.ndarray] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        # normalize_embeddings=True applies L2 normalisation inside the model
        emb = model.encode(
            batch,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=batch_size,
        )
        batches.append(emb.astype(np.float32))

    return np.vstack(batches)
