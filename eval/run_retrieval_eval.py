import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from retrieval.assembler import retrieve

def run_retrieval_eval():
    questions_path = Path("eval/questions.jsonl")
    results_dir = Path("eval/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    questions = []
    with open(questions_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))
                
    # Metrics accumulators
    cat_ab_count = 0
    cat_c_count = 0
    cat_c_correct = 0
    
    sum_recall = 0.0
    sum_mrr = 0.0
    sum_ndcg = 0.0
    sum_precision = 0.0
    
    for q in questions:
        category = q.get("category")
        filters = q.get("filters", {})
        question_text = q.get("question")
        relevant = set(q.get("relevant_chunk_sources", []))
        
        # Retrieve
        result = retrieve(question_text, top_k=config.TOP_K, filters=filters)
        
        if category == "C":
            cat_c_count += 1
            if not result.get("context_found"):
                cat_c_correct += 1
            continue
            
        cat_ab_count += 1
        
        retrieved_chunks = result.get("chunks", [])
        # Extract source_file for each chunk in rank order
        retrieved_sources = [c.get("source_file") for c in retrieved_chunks]
        
        # Unique retrieved sources for precision/recall intersection
        # The prompt says "retrieved" vs "relevant". 
        # Usually, retrieved is the set of documents.
        retrieved_set = set(retrieved_sources)
        
        intersection = retrieved_set.intersection(relevant)
        
        # Recall@k
        if len(relevant) > 0:
            recall = len(intersection) / len(relevant)
        else:
            recall = 0.0
        sum_recall += recall
        
        # Context precision
        if len(retrieved_set) > 0:
            precision = len(intersection) / len(retrieved_set)
        else:
            precision = 0.0
        sum_precision += precision
        
        # MRR
        rank = 0
        for i, src in enumerate(retrieved_sources):
            if src in relevant:
                rank = i + 1
                break
        if rank > 0:
            sum_mrr += 1.0 / rank
            
        # nDCG@k
        dcg = 0.0
        idcg = 0.0
        # Compute DCG
        credited = set()
        for i, src in enumerate(retrieved_sources):
            rel = 1 if (src in relevant and src not in credited) else 0
            if rel == 1:
                credited.add(src)
            dcg += rel / math.log2(i + 2)  # i is 0-indexed, so i+1 is rank, +1 for log2 formula = i+2
            
        # Compute IDCG (ideal is all relevant items first)
        ideal_rels = [1] * min(len(relevant), len(retrieved_sources)) + [0] * max(0, len(retrieved_sources) - len(relevant))
        for i, rel in enumerate(ideal_rels):
            idcg += rel / math.log2(i + 2)
            
        if idcg > 0:
            sum_ndcg += dcg / idcg
            
    # Aggregation
    avg_recall = sum_recall / cat_ab_count if cat_ab_count > 0 else 0
    avg_precision = sum_precision / cat_ab_count if cat_ab_count > 0 else 0
    avg_mrr = sum_mrr / cat_ab_count if cat_ab_count > 0 else 0
    avg_ndcg = sum_ndcg / cat_ab_count if cat_ab_count > 0 else 0
    no_context_acc = cat_c_correct / cat_c_count if cat_c_count > 0 else 0
    
    metrics = {
        "Recall@k": avg_recall,
        "MRR": avg_mrr,
        "nDCG@k": avg_ndcg,
        "ContextPrecision": avg_precision,
        "NoContextAccuracy (Cat C)": no_context_acc
    }
    
    with open(results_dir / "retrieval_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        
    md_content = "# Retrieval Metrics\n\n| Metric | Score |\n|---|---|\n"
    for k, v in metrics.items():
        md_content += f"| {k} | {v:.4f} |\n"
        
    with open(results_dir / "retrieval_metrics.md", "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print("Retrieval eval complete.")

if __name__ == "__main__":
    run_retrieval_eval()
