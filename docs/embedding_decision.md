# Embedding Model Decision

## Selected Model: `sentence-transformers/all-MiniLM-L6-v2`

For the Vaultly Cost-Efficient RAG application, we chose the `all-MiniLM-L6-v2` embedding model over proprietary alternatives such as OpenAI's `text-embedding-ada-002`.

### Rationale

1. **Cost Efficiency**: `all-MiniLM-L6-v2` is an open-source model that runs completely locally. This eliminates per-token embedding costs, which is crucial for an application optimizing for cost-efficiency. Over thousands of documents, API-based embeddings like `ada-002` would incur significant recurring fees.
2. **Performance vs Size**: With 384 dimensions, `all-MiniLM-L6-v2` offers an excellent balance between index size and retrieval accuracy. A smaller dimensionality means the FAISS index consumes less memory, and similarity searches (L2/Cosine) execute significantly faster than with 1536-dimensional embeddings (e.g. `ada-002`).
3. **Data Privacy**: Running the model locally guarantees that sensitive Vaultly document contents are not sent to third-party APIs during the ingestion or retrieval phases.
4. **Acceptable Quality**: Although smaller, the model provides highly competitive context precision and recall for general-purpose technical documentation like the Vaultly corpus, proving more than adequate for our retrieval pipeline.

### Integration Details
The model is loaded using the `sentence-transformers` library and runs on CPU or GPU seamlessly during the ingestion pipeline (`ingestion/pipeline.py`) and retrieval pipeline (`retrieval/assembler.py`).
