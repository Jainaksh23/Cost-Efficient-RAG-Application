from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class IngestRequest(BaseModel):
    file_paths: List[str]

class IngestResponse(BaseModel):
    files_processed: int
    chunks_added: int
    chunks_skipped: int
    faiss_size: int
    sqlite_count: int

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = None
    filters: Optional[Dict[str, Any]] = None

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class QueryResponse(BaseModel):
    answer: Optional[str]
    citations: List[int]
    context_found: bool
    chunks_retrieved: int
    best_similarity_score: float
    retrieval_latency_ms: int
    generation_latency_ms: int
    total_latency_ms: int
    token_usage: Optional[TokenUsage]

class HealthResponse(BaseModel):
    status: str
    faiss_index_size: int
    sqlite_chunk_count: int
