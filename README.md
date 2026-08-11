# 🔐 Vaultly RAG Service

> A **cost-efficient, production-ready** Question Answering (QA) backend built on Retrieval-Augmented Generation (RAG). Ask any question about Vaultly's documentation and get a grounded, cited answer — in under 600ms.

---

## 📌 What Does This Project Do?

This system lets you **ask questions in plain English** about Vaultly's product documentation (install guides, pricing, API reference, FAQs, etc.) and get back accurate, source-cited answers — without hallucination.

**Example:**
```
Q: "What Python version is required to install Vaultly?"
A: [Chunk 1 | source: install_guide.pdf | chunk_idx: 0]
   Vaultly will not start on Python versions below 3.10 due to use of
   structural pattern matching introduced in that version.
```

It works by:
1. **Ingesting** your documents (PDF, HTML, Markdown)
2. **Chunking + embedding** them into a vector store
3. On every query — **retrieving** the most relevant chunks
4. **Feeding them to an LLM** that answers only from the retrieved evidence

---

## 🏗️ Architecture Overview

```
📄 PDF / 🌐 HTML / 📝 Markdown
         │
         ▼
  ┌─────────────────────────────┐
  │     Document Loader         │  (ingestion/loaders.py)
  │  Extracts raw text per type │
  └────────────┬────────────────┘
               │
               ▼
  ┌─────────────────────────────┐
  │         Chunker             │  (ingestion/chunker.py)
  │  Size: 2048 tokens          │
  │  Overlap: 256 tokens        │
  └────────────┬────────────────┘
               │
               ▼
  ┌─────────────────────────────┐
  │      Content Hasher         │  (ingestion/hasher.py)
  │  SHA-256 per chunk          │
  │  Skips duplicates → idempotent│
  └────────────┬────────────────┘
               │
               ▼
  ┌─────────────────────────────┐
  │      Embedding Model        │  sentence-transformers/all-MiniLM-L6-v2
  │  384-dim L2-normalised      │  (embedding/embedder.py)
  └───────┬──────────┬──────────┘
          │          │
          ▼          ▼
  ┌──────────┐  ┌───────────────┐
  │  FAISS   │  │    SQLite     │  (storage/)
  │  Index   │  │   Metadata    │
  │ (vectors)│  │(text,source..)│
  └────┬─────┘  └──────┬────────┘
       │               │
       └──────┬─────────┘
              │  (at query time)
              ▼
  ┌─────────────────────────────┐
  │   Top-K FAISS Search (k=5)  │
  │   + Metadata filter         │
  └────────────┬────────────────┘
               │
        ┌──────┴──────┐
        │             │
   similarity    similarity
    < 0.25        ≥ 0.25
        │             │
        ▼             ▼
  "No relevant   Context Assembly
   context"     [Chunk 1 | source]
   (returned)         │
                      ▼
              ┌───────────────┐
              │  Groq LLM     │  llama-3.3-70b-versatile
              │  Generation   │
              └───────┬───────┘
                      │
                      ▼
              Grounded Answer
              + Inline Citations
              + Token Usage Logged
```

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **API** | FastAPI + Uvicorn | Async, fast, auto-docs at `/docs` |
| **Embedding** | `sentence-transformers/all-MiniLM-L6-v2` | Free, 384-dim, runs locally — zero API cost |
| **Vector Store** | FAISS `IndexFlatL2` | Exact search, <50ms, no monthly fee |
| **Metadata Store** | SQLite | Zero-cost, filters by source/chunk |
| **LLM** | Groq API — `llama-3.3-70b-versatile` | Fast inference, pay-per-token |
| **Document Parsing** | PyMuPDF (PDF), BeautifulSoup (HTML), plain text (MD) | Multi-format support |
| **Evaluation** | Custom retrieval + LLM-as-judge harness | Honest, reproducible metrics |
| **Testing** | pytest | Unit + integration tests |

---

## 📁 Project Structure

```
Cost-Efficient RAG Application/
│
├── api/                    # FastAPI application
│   ├── main.py             # App entry point + startup
│   ├── routes.py           # /query, /ingest, /health endpoints
│   ├── schemas.py          # Request/response models
│   └── logging_utils.py    # Query logging to JSONL
│
├── ingestion/              # Document ingestion pipeline
│   ├── loaders.py          # PDF / HTML / Markdown readers
│   ├── chunker.py          # Text splitter (size + overlap)
│   ├── hasher.py           # SHA-256 dedup
│   └── pipeline.py         # Orchestrates the full ingestion flow
│
├── embedding/
│   └── embedder.py         # Lazy-loaded sentence-transformer singleton
│
├── storage/
│   ├── faiss_store.py      # FAISS index read/write/search
│   └── sqlite_store.py     # SQLite chunk metadata CRUD
│
├── retrieval/
│   └── assembler.py        # Embeds query → FAISS search → returns chunks
│
├── generation/
│   └── generator.py        # Calls Groq API with retrieved context
│
├── eval/                   # Evaluation harness
│   ├── questions.jsonl     # 16 evaluation questions with gold answers
│   ├── run_retrieval_eval.py
│   ├── run_answer_eval.py
│   └── results/            # All evaluation result reports
│       ├── retrieval_metrics.md
│       ├── answer_metrics.md
│       ├── latency.md
│       └── cost_comparison.md
│
├── scripts/
│   └── run_ingest.py       # CLI to ingest all docs in data/
│
├── tests/                  # pytest unit + integration tests
├── data/                   # Your documents go here (PDF/HTML/MD)
├── logs/queries.jsonl      # Auto-generated query log
├── docs/                   # Architecture diagram, latency docs
├── config.py               # All settings from environment variables
├── .env.example            # Template — copy to .env and fill in
└── requirements.txt
```

---

## ⚙️ Setup — Step by Step (Zero to Running)

### Prerequisites
- Python **3.10+**
- A free **Groq API key** → get one at [console.groq.com](https://console.groq.com)

---

### Step 1 — Clone the repo

```bash
git clone https://github.com/Jainaksh23/Cost-Efficient-RAG-Application.git
cd "Cost-Efficient-RAG-Application"
```

---

### Step 2 — Create a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4 — Set up your environment file

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Now open `.env` in any text editor and set your Groq API key:

```
GROQ_API_KEY=gsk_your_actual_key_here
```

> ⚠️ **Never commit `.env` to git.** It is already in `.gitignore`.

---

### Step 5 — Add your documents

Put any PDF, HTML, or Markdown files you want to query into the `data/` folder.  
The project already includes 8 Vaultly documents as examples:
- `install_guide.pdf`, `pricing_policy.pdf`, `troubleshooting.pdf`
- `api_reference.md`, `faq.md`, `getting_started.md`
- `company_overview.html`, `release_notes.html`

---

### Step 6 — Ingest the documents

```bash
python scripts/run_ingest.py
```

Expected output:
```
============================================================
RAG Ingestion — data/ folder: 8 files
============================================================
  INGESTION COMPLETE
  Files processed  : 8
  Chunks added     : 15
  Chunks skipped   : 0
  FAISS index size : 15  vectors
  SQLite row count : 15  rows
  [OK]  FAISS and SQLite agree: 15 vectors/rows
============================================================
```

> 💡 Running ingestion again on the same files will **skip all chunks** (idempotent — SHA-256 deduplication). Chunks added will be 0.

---

### Step 7 — Start the API server

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

You'll see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 🚀 Using the API

### Option A — Interactive API Docs (easiest)

Open your browser and go to:  
**`http://127.0.0.1:8000/docs`**

You'll see a full Swagger UI where you can test every endpoint by clicking.

---

### Option B — curl from terminal

**Ask a question:**
```bash
curl -X POST "http://127.0.0.1:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What Python version is required to install Vaultly?"}'
```

**Response:**
```json
{
  "answer": "[Chunk 1 | source: install_guide.pdf | chunk_idx: 0]\nVaultly will not start on Python versions below 3.10...",
  "citations": [1],
  "context_found": true,
  "chunks_retrieved": 5,
  "best_similarity_score": 0.8027,
  "retrieval_latency_ms": 26,
  "generation_latency_ms": 582,
  "total_latency_ms": 608,
  "token_usage": {
    "prompt_tokens": 2374,
    "completion_tokens": 48,
    "total_tokens": 2422
  }
}
```

**Ask something not in your docs (tests no-context path):**
```bash
curl -X POST "http://127.0.0.1:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of France?"}'
```

**Check server health:**
```bash
curl http://127.0.0.1:8000/health
```

---

### Option C — Python

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/query",
    json={"question": "What is the monthly price of the Professional plan?"}
)
data = response.json()
print(data["answer"])
print(f"Retrieval: {data['retrieval_latency_ms']}ms | Generation: {data['generation_latency_ms']}ms")
```

---

## 📊 Evaluation Results (Summary)

| Metric | Value |
|---|---|
| Recall@5 | 93.75% |
| MRR | 0.81 |
| No-Context Accuracy | 100% |
| Context Precision | 45.52% |
| F1 (token overlap) | 0.44 |
| Retrieval Latency p50 | 28 ms |
| Total Latency p50 | 331 ms |
| Cost per 1,000 queries | ~$0.07 |

Full reports: [`eval/results/`](eval/results/)

---

## 🧪 Running Tests & Evaluation

```bash
# Unit and integration tests
pytest tests/ -v

# Retrieval quality evaluation (Recall, MRR, nDCG, Precision)
python eval/run_retrieval_eval.py

# Answer quality evaluation (F1, EM, LLM-as-judge)
# Note: uses Groq API — may hit rate limits on free tier
python eval/run_answer_eval.py
```

> The answer eval script has **automatic retry with exponential backoff** built in for Groq rate limit errors. It will pause and resume automatically.

---

## 💰 Cost Analysis

| Component | Cost |
|---|---|
| Embedding model | **$0** — runs locally |
| FAISS vector store | **$0** — no managed service |
| SQLite metadata | **$0** — file-based |
| Groq LLM (llama-3.3-70b-versatile) | ~$0.07 per 1,000 queries |
| **Total infrastructure** | **~$20/month** (compute host only) |

vs. Pinecone + OpenAI: ~$70+/month minimum

---

## 🔑 Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | Your Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model name |
| `TOP_K` | `5` | Number of chunks to retrieve |
| `MIN_SIMILARITY_THRESHOLD` | `0.25` | Below this → no-context response |
| `CHUNK_SIZE` | `2048` | Token size per chunk |
| `CHUNK_OVERLAP` | `256` | Token overlap between chunks |
| `EMBED_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `FAISS_INDEX_PATH` | `data/faiss.index` | Where the vector index is saved |
| `SQLITE_DB_PATH` | `data/rag_metadata.db` | Where chunk metadata is saved |
| `API_HOST` | `0.0.0.0` | Server bind address |
| `API_PORT` | `8000` | Server port |

---

## ❓ Troubleshooting

**`401 Invalid API Key`**  
→ Check `.env` — make sure `GROQ_API_KEY` has your real key, not the placeholder `your_groq_api_key_here`. Restart the server after editing `.env`.

**`FAISS index not found`**  
→ You need to run ingestion first: `python scripts/run_ingest.py`

**`Rate limit exceeded` from Groq**  
→ Free Groq accounts have a daily token limit. Wait a few minutes and retry, or upgrade your Groq plan.

**Server not responding**  
→ Make sure nothing else is on port 8000. Try `--port 8001` if needed.

---

## 📋 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/query` | Ask a question, get a grounded answer |
| `GET` | `/health` | Check server + index status |
| `POST` | `/ingest` | Trigger ingestion via API |
| `GET` | `/docs` | Interactive Swagger UI |

---

## Discussion

### 1. When would you switch to a managed vector DB?
We would migrate to a managed vector database (like Pinecone) when the index size approaches 5-10 million vectors. At that scale, an exhaustive `IndexFlatL2` FAISS index would require significantly more expensive, high-RAM compute instances, eclipsing the cost of a managed database. Additionally, managed DBs provide built-in High Availability (HA), sharding, and real-time indexing which are critical at larger scales.

### 2. Based on the actual metrics, was retrieval or generation the weaker link?
**Retrieval is extremely strong**: Recall is at 93.75%, MRR is 0.81, and our No-Context Accuracy is perfect (1.0). The median retrieval latency is exceptionally fast at 28.0ms.

**Generation is the weaker link**: While the LLM generation itself adds minimal overhead (Total Latency p50 is 331ms), the generation layer is heavily bottlenecked by LLM provider rate limits (as seen when we hit rate-limit stalls running evaluations). Furthermore, Context Precision is only 45.52%, meaning that although we retrieve the correct chunks, we also pull in many irrelevant ones which wastes generation token budgets. Exact Match (EM) is expectedly near-zero across all questions — this is not a bug: generated answers are full grounded sentences with inline citations (e.g. `[Chunk 1]`), while gold answers are short factual spans, so a literal string match is structurally unlikely. F1 (token overlap) is the more meaningful metric here and shows real partial credit across questions.
