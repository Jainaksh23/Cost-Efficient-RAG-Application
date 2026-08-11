import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config
from api.schemas import IngestRequest, IngestResponse, QueryRequest, QueryResponse, HealthResponse, TokenUsage
from api.logging_utils import log_query

from ingestion.pipeline import ingest_documents
from retrieval.assembler import retrieve
from generation.generator import generate_answer
import storage.faiss_store as faiss_store
import storage.sqlite_store as sql_store

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse)
def api_ingest(request: IngestRequest):
    try:
        result = ingest_documents(request.file_paths)
        return IngestResponse(
            files_processed=result.files_processed,
            chunks_added=result.chunks_added,
            chunks_skipped=result.chunks_skipped,
            faiss_size=result.faiss_size,
            sqlite_count=result.sqlite_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
def api_query(request: QueryRequest):
    start_total = time.time()
    
    # Retrieval
    start_retrieval = time.time()
    try:
        retrieval_result = retrieve(
            question=request.question,
            top_k=request.top_k,
            filters=request.filters
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")
    retrieval_latency_ms = int((time.time() - start_retrieval) * 1000)
    
    # Generation
    try:
        gen_result = generate_answer(request.question, retrieval_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")
    
    generation_latency_ms = gen_result.get("generation_latency_ms", 0)
    total_latency_ms = int((time.time() - start_total) * 1000)
    
    token_usage = gen_result.get("token_usage")
    if token_usage:
        token_usage_obj = TokenUsage(**token_usage)
    else:
        token_usage_obj = None
        
    # Log the query
    log_query(
        question=request.question,
        filters=request.filters,
        chunks_retrieved=len(retrieval_result.get("chunks", [])),
        context_found=retrieval_result.get("context_found", False),
        retrieval_latency_ms=retrieval_latency_ms,
        generation_latency_ms=generation_latency_ms,
        total_latency_ms=total_latency_ms,
        token_usage=token_usage
    )
    
    return QueryResponse(
        answer=gen_result.get("answer"),
        citations=gen_result.get("citations", []),
        context_found=retrieval_result.get("context_found", False),
        chunks_retrieved=len(retrieval_result.get("chunks", [])),
        best_similarity_score=retrieval_result.get("best_similarity_score", 0.0),
        retrieval_latency_ms=retrieval_latency_ms,
        generation_latency_ms=generation_latency_ms,
        total_latency_ms=total_latency_ms,
        token_usage=token_usage_obj
    )

@router.get("/health", response_model=HealthResponse)
def api_health():
    try:
        faiss_size = faiss_store.ntotal()
        sqlite_count = sql_store.count_chunks()
        return HealthResponse(
            status="ok",
            faiss_index_size=faiss_size,
            sqlite_chunk_count=sqlite_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
