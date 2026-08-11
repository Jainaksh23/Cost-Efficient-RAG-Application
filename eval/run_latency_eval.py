import json
import numpy as np
from pathlib import Path

def run_latency_eval():
    logs_path = Path("logs/queries.jsonl")
    results_dir = Path("eval/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    retrieval_latencies = []
    total_latencies = []
    
    if logs_path.exists():
        with open(logs_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    retrieval_latencies.append(data.get("retrieval_latency_ms", 0))
                    total_latencies.append(data.get("total_latency_ms", 0))
                    
    if not retrieval_latencies:
        print("No queries logged yet. Please run queries first.")
        return
        
    r_p50 = np.percentile(retrieval_latencies, 50)
    r_p95 = np.percentile(retrieval_latencies, 95)
    
    t_p50 = np.percentile(total_latencies, 50)
    t_p95 = np.percentile(total_latencies, 95)
    
    md = "# Latency Evaluation\n\n"
    md += "Based on real queries logged during evaluation.\n\n"
    md += "| Metric | p50 (ms) | p95 (ms) |\n"
    md += "|---|---|---|\n"
    md += f"| Retrieval Latency | {r_p50:.1f} | {r_p95:.1f} |\n"
    md += f"| Total Latency | {t_p50:.1f} | {t_p95:.1f} |\n"
    
    with open(results_dir / "latency.md", "w", encoding="utf-8") as f:
        f.write(md)
        
    print("Latency eval complete.")

if __name__ == "__main__":
    run_latency_eval()
