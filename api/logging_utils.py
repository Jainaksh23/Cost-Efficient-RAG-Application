import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

LOGS_DIR = Path("logs")
QUERIES_LOG_FILE = LOGS_DIR / "queries.jsonl"

def log_query(
    question: str,
    filters: Optional[Dict[str, Any]],
    chunks_retrieved: int,
    context_found: bool,
    retrieval_latency_ms: int,
    generation_latency_ms: int,
    total_latency_ms: int,
    token_usage: Optional[Dict[str, int]]
):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "question": question,
        "filters": filters,
        "chunks_retrieved": chunks_retrieved,
        "context_found": context_found,
        "retrieval_latency_ms": retrieval_latency_ms,
        "generation_latency_ms": generation_latency_ms,
        "total_latency_ms": total_latency_ms,
        "token_usage": token_usage
    }
    
    # Write JSON line
    with open(QUERIES_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
        
    # Print to console
    print(f"  [Query Log] Latency={total_latency_ms}ms, Context={context_found}, Chunks={chunks_retrieved}")
