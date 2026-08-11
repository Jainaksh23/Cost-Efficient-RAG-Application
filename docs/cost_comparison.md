# Cost Comparison: FAISS+SQLite vs Pinecone Serverless

## Assumptions
- **Pinecone Serverless**: storage $0.33/GB/month, ~$17 per million read units, ~$4.25 per million write units, $50/month minimum (Standard plan). Cite these as "Pinecone published Standard plan rates, verified August 2026."
- **Self-hosted**: embedding is free/local (no API cost). FAISS flat index storage ≈ 1.5KB/vector. Groq API cost for `llama-3.1-8b-instant` is $0.05/1M prompt tokens and $0.08/1M completion tokens. OpenAI `GPT-4o` is $5.00/1M prompt tokens and $15.00/1M completion tokens.
- **Traffic**: Assume 10,000 queries/month for both sides. Assume 2000 prompt tokens and 100 completion tokens per query.
  - Groq `llama-3.1-8b-instant` LLM Cost: `10000 * ((2000/1e6)*0.05 + (100/1e6)*0.08) = $1.08`
  - OpenAI `GPT-4o` LLM Cost: `10000 * ((2000/1e6)*5.00 + (100/1e6)*15.00) = $115.00`
- **Hardware (Self-hosted)**: Assume a small compute host (~$20/month for <1M vectors, ~$80/month for 10M vectors since IndexFlatL2 needs everything in RAM).

## Trade-off Note
IndexFlatL2 becomes RAM-constrained around 5-10M vectors and a real deployment would migrate to IndexIVFFlat or IndexIVFPQ at that point.

## Comparison Table
| Vectors | FAISS+SQLite + Groq Llama-3.1-8B | Pinecone Serverless + OpenAI GPT-4o |
|---|---|---|
| 100,000 | $21.08/mo (Host: $20, LLM: $1.08) | $165.00/mo (DB: $50.00, LLM: $115.00) |
| 1,000,000 | $21.08/mo (Host: $20, LLM: $1.08) | $165.00/mo (DB: $50.00, LLM: $115.00) |
| 10,000,000 | $81.08/mo (Host: $80, LLM: $1.08) | $165.00/mo (DB: $50.00, LLM: $115.00) |
