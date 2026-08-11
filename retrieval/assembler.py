"""
retrieval/assembler.py
Retrieval logic using FAISS and SQLite to assemble chunks into a context block.
"""
from __future__ import annotations

import faiss

import config
from embedding.embedder import embed
import storage.sqlite_store as sql_store
import storage.faiss_store as faiss_store

def retrieve(question: str, top_k: int = None, filters: dict = None) -> dict:
    if top_k is None:
        top_k = config.TOP_K
        
    # 1. Embed the question
    qv = embed([question])
    
    # 2. Build ID selector if filters provided
    id_selector = None
    if filters:
        faiss_ids = sql_store.get_faiss_ids_by_filter(filters)
        if not faiss_ids:
            # Filters eliminated everything
            return {
                "context_found": False,
                "chunks": [],
                "context_block": "",
                "best_similarity_score": 0.0
            }
        id_selector = faiss.IDSelectorBatch(faiss_ids)
        
    # 3. Search FAISS
    ids, dists = faiss_store.search(qv, k=top_k, id_selector=id_selector)
    
    if not ids:
        return {
            "context_found": False,
            "chunks": [],
            "context_block": "",
            "best_similarity_score": 0.0
        }
        
    # 4. Compute similarities and re-rank
    # Distance is L2 squared. vectors are L2 normalized, so similarity = 1 - dist / 2
    similarities = [1.0 - (d / 2.0) for d in dists]
    best_sim = similarities[0]
    
    # 5. Threshold check
    if best_sim < config.MIN_SIMILARITY_THRESHOLD:
        return {
            "context_found": False,
            "chunks": [],
            "context_block": "",
            "best_similarity_score": best_sim
        }
        
    # 6. Fetch chunks
    rows = sql_store.get_chunks_by_faiss_ids(ids)
    
    # Map faiss_id to row for easy access, ensuring we keep the ranked order
    row_map = {row["faiss_id"]: row for row in rows}
    
    chunks = []
    context_blocks = []
    
    for rank_idx, (faiss_id, sim) in enumerate(zip(ids, similarities)):
        row = row_map.get(faiss_id)
        if not row:
            continue
            
        chunk_dict = {
            "faiss_id": faiss_id,
            "source_file": row["source_file"],
            "chunk_index": row["chunk_index"],
            "similarity_score": sim,
            "text": row["chunk_text"]
        }
        chunks.append(chunk_dict)
        
        # 7. Format block
        header = f"[Chunk {rank_idx + 1} | source: {row['source_file']} | chunk_idx: {row['chunk_index']}]"
        context_blocks.append(f"{header}\n{row['chunk_text']}")
        
    return {
        "context_found": True,
        "chunks": chunks,
        "context_block": "\n\n".join(context_blocks),
        "best_similarity_score": best_sim
    }
