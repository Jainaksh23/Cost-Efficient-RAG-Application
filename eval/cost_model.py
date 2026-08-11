from pathlib import Path

def generate_cost_model():
    results_dir = Path("eval/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 10,000 queries per month
    queries_per_month = 10000
    
    # Vectors to evaluate
    vector_counts = [100_000, 1_000_000, 10_000_000]
    
    md = "# Cost Comparison: FAISS+SQLite vs Pinecone Serverless\n\n"
    md += "## Assumptions\n"
    md += "- **Pinecone Serverless**: storage $0.33/GB/month, ~$17 per million read units, ~$4.25 per million write units, $50/month minimum (Standard plan). Cite these as \"Pinecone published Standard plan rates, verified August 2026.\"\n"
    md += "- **Self-hosted**: embedding is free/local (no API cost). FAISS flat index storage ≈ 1.5KB/vector. Groq API cost for `llama-3.3-70b-versatile` is $0.59/1M prompt tokens and $0.79/1M completion tokens.\n"
    md += "- **Traffic**: Assume 10,000 queries/month for both sides.\n"
    md += "- **Hardware (Self-hosted)**: Assume a small compute host (~$20/month for <1M vectors, ~$80/month for 10M vectors since IndexFlatL2 needs everything in RAM).\n\n"
    
    md += "## Trade-off Note\n"
    md += "IndexFlatL2 becomes RAM-constrained around 5-10M vectors and a real deployment would migrate to IndexIVFFlat or IndexIVFPQ at that point.\n\n"
    
    md += "## Comparison Table\n"
    md += "| Vectors | FAISS+SQLite (Self-Hosted) | Pinecone Serverless |\n"
    md += "|---|---|---|\n"
    
    for v in vector_counts:
        # Self hosted compute cost
        if v < 1_000_000:
            sh_host = 20
        elif v == 1_000_000:
            sh_host = 20
        else:
            sh_host = 80
            
        # Groq generation cost is the same for both RAG architectures if they use the same LLM,
        # but let's calculate it. Say 1000 prompt tokens + 100 completion tokens per query.
        groq_cost = (queries_per_month * 1000 / 1_000_000) * 0.59 + (queries_per_month * 100 / 1_000_000) * 0.79
        
        sh_total = sh_host + groq_cost
        
        # Pinecone cost
        # Storage: v * 1.5KB = v * 1.5 / 1024 / 1024 GB
        pine_gb = (v * 1.5) / (1024 * 1024)
        pine_storage = pine_gb * 0.33
        # Reads: 10,000 queries
        pine_reads = (queries_per_month / 1_000_000) * 17
        pine_base = pine_storage + pine_reads
        # Minimum is $50
        pine_db = max(50.0, pine_base)
        
        pine_total = pine_db + groq_cost
        
        md += f"| {v:,} | ${sh_total:.2f}/mo (Host: ${sh_host}, LLM: ${groq_cost:.2f}) | ${pine_total:.2f}/mo (DB: ${pine_db:.2f}, LLM: ${groq_cost:.2f}) |\n"
        
    with open(results_dir / "cost_comparison.md", "w", encoding="utf-8") as f:
        f.write(md)
        
    print("Cost model generated.")

if __name__ == "__main__":
    generate_cost_model()
