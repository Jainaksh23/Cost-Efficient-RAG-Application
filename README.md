# Vaultly RAG Service

This repository contains the Retrieval-Augmented Generation (RAG) backend for Vaultly's support documentation.

## Setup Instructions

From a clean clone, run the following commands to get the server running and test your first query:

```bash
# 1. Create a virtual environment and activate it
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .env file and set your GROQ_API_KEY
cp .env.example .env
# Edit .env and set your GROQ_API_KEY!

# 4. Ingest the documents to build the FAISS index and SQLite DB
python scripts/run_ingest.py

# 5. Start the FastAPI server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# 6. Run your first query (in another terminal)
curl -X POST "http://127.0.0.1:8000/query" -H "Content-Type: application/json" -d '{"question":"What Python version is required to install Vaultly?"}'
```

## Running Tests & Evaluation

To run the full suite of unit tests and RAG evaluations:

```bash
# 1. Run standard unit/integration tests
pytest tests/

# 2. Run retrieval evaluations
python eval/run_retrieval_eval.py

# 3. Run full answer generation and judge evaluations
python eval/run_answer_eval.py
```

> **Note on Groq Rate Limits**: The `run_answer_eval.py` script makes intensive use of the Groq API (calling both the generation model and the judge model). Due to restrictive Tokens-Per-Day (TPD) or Tokens-Per-Minute (TPM) limits on free Groq accounts, the script implements automatic retries with exponential backoff. If you hit rate limits, the evaluation will pause and automatically resume when the limit window resets.

## Architecture: Vector Store Choice

We use a self-hosted combination of **FAISS** (FlatL2 index for embeddings) and **SQLite** (for metadata and structured filtering). 

**Justification**: At our current scale (well under 1 million vectors), an in-memory FAISS flat index provides 100% accurate exhaustive search in under 50ms, while SQLite perfectly handles the metadata filtering. This eliminates the massive base cost ($50/mo minimum) and network overhead of a managed service like Pinecone, keeping our infrastructure cost strictly bound to our compute host (~$20/mo). 

## Evaluation Results

Detailed evaluation results can be found in the following reports:
- [Retrieval Metrics](eval/results/retrieval_metrics.md)
- [Latency Evaluation](eval/results/latency.md)
- [Cost Comparison](eval/results/cost_comparison.md)
- [Answer Quality Metrics](eval/results/answer_metrics.md)

## Discussion

### 1. When would you switch to a managed vector DB?
We would migrate to a managed vector database (like Pinecone) when the index size approaches 5-10 million vectors. At that scale, an exhaustive `IndexFlatL2` FAISS index would require significantly more expensive, high-RAM compute instances, eclipsing the cost of a managed database. Additionally, managed DBs provide built-in High Availability (HA), sharding, and real-time indexing which are critical at larger scales.

### 2. Based on the actual metrics, was retrieval or generation the weaker link?
**Retrieval is extremely strong**: Recall is at 93.75%, MRR is 0.81, and our No-Context Accuracy is perfect (1.0). The median retrieval latency is exceptionally fast at 28.0ms.
**Generation is the weaker link**: While the LLM generation itself adds minimal overhead (Total Latency p50 is 331ms), the generation layer is heavily bottlenecked by LLM provider rate limits (as seen when we hit rate-limit stalls running evaluations). Furthermore, Context Precision is only 45.52%, meaning that although we retrieve the correct chunks, we also pull in many irrelevant ones which wastes generation token budgets.
