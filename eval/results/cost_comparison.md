# Cost Comparison: FAISS+SQLite vs Pinecone Serverless

## Assumptions
- **Pinecone Serverless**: storage $0.33/GB/month, ~$17 per million read units, ~$4.25 per million write units, $50/month minimum (Standard plan). Cite these as "Pinecone published Standard plan rates, verified August 2026."
- **Self-hosted**: embedding is free/local (no API cost). FAISS flat index storage ≈ 1.5KB/vector. Groq API cost for `llama-3.3-70b-versatile` is $0.59/1M prompt tokens and $0.79/1M completion tokens.
- **Traffic**: Assume 10,000 queries/month for both sides. Assume 2000 prompt tokens and 100 completion tokens per query.
  - Groq `llama-3.3-70b-versatile` LLM Cost: `10000 * ((2000/1e6)*0.59 + (100/1e6)*0.79) = $12.59`
- **Hardware (Self-hosted)**: Assume a small compute host (~$20/month for <1M vectors, ~$80/month for 10M vectors since IndexFlatL2 needs everything in RAM).

## Trade-off Note
IndexFlatL2 becomes RAM-constrained around 5-10M vectors and a real deployment would migrate to IndexIVFFlat or IndexIVFPQ at that point.

## Comparison Table
| Vectors | FAISS+SQLite + Groq Llama-3.3-70B | Pinecone Serverless + Groq Llama-3.3-70B |
|---|---|---|
| 100,000 | $32.59/mo (Host: $20, LLM: $12.59) | $62.59/mo (DB: $50.00, LLM: $12.59) |
| 1,000,000 | $32.59/mo (Host: $20, LLM: $12.59) | $62.59/mo (DB: $50.00, LLM: $12.59) |
| 10,000,000 | $92.59/mo (Host: $80, LLM: $12.59) | $62.59/mo (DB: $50.00, LLM: $12.59) |
