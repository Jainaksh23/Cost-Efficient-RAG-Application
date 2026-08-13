"""
config.py — Centralised settings loader.
All configuration is read from environment variables (or .env file).
Nothing is hardcoded; every value has a safe default.
"""
import os
from pathlib import Path
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()  # reads .env if present; silently ignored if absent

# ── Paths ─────────────────────────────────────────────────────────────────────
FAISS_INDEX_PATH: Path = Path(os.getenv("FAISS_INDEX_PATH", "data/faiss.index"))
SQLITE_DB_PATH: Path   = Path(os.getenv("SQLITE_DB_PATH",   "data/rag_metadata.db"))

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE: int    = int(os.getenv("CHUNK_SIZE",    "2048"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "256"))

# ── Embedding ─────────────────────────────────────────────────────────────────
EMBED_MODEL: str       = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBED_BATCH_SIZE: int  = int(os.getenv("EMBED_BATCH_SIZE", "32"))
EMBED_DIMENSION: int   = 384  # fixed for all-MiniLM-L6-v2; not overridable

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K: int                      = int(os.getenv("TOP_K", "5"))
MIN_SIMILARITY_THRESHOLD: float = float(os.getenv("MIN_SIMILARITY_THRESHOLD", "0.25"))

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str         = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str | None   = os.getenv("LOG_FILE", None)

# ── API ───────────────────────────────────────────────────────────────────────
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))

# ── Groq (required for generation + LLM-as-judge eval) ────────────────────────
GROQ_API_KEY: str   = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str     = os.getenv("GROQ_MODEL",       "llama-3.3-70b-versatile")
GROQ_JUDGE_MODEL: str = os.getenv("GROQ_JUDGE_MODEL", "llama-3.3-70b-versatile")

# ── Evaluation ────────────────────────────────────────────────────────────────
EVAL_QUESTIONS_PATH: Path = Path(os.getenv("EVAL_QUESTIONS_PATH", "eval/questions.jsonl"))
EVAL_RESULTS_PATH: Path   = Path(os.getenv("EVAL_RESULTS_PATH",   "eval/results.json"))
