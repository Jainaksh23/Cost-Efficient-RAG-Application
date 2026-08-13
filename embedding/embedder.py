"""
embedding/embedder.py
Wraps fastembed TextEmbedding (ONNX-based).
- Lazy singleton: the model is loaded once on first call.
- Batched encoding controlled by EMBED_BATCH_SIZE.
- Returns float32 arrays of shape (N, 384).
"""
from __future__ import annotations

import numpy as np
from fastembed import TextEmbedding

import config

_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        print(f"[Embedder] Loading model: {config.EMBED_MODEL}")
        # Note: Production deployments now use fastembed (ONNX) to avoid torch/CUDA overhead.
        _model = TextEmbedding(model_name=config.EMBED_MODEL)
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

    # fastembed's .embed() accepts an iterable and handles batching internally.
    # It yields numpy arrays for each document, which we collect and stack.
    embeddings = list(model.embed(texts, batch_size=batch_size))
    
    return np.vstack(embeddings).astype(np.float32)
