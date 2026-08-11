"""
scripts/test_retrieval.py
Test the retrieval pipeline on 3 specific cases from questions.jsonl.
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from retrieval.assembler import retrieve
import config

def get_questions():
    q_file = PROJECT_ROOT / config.EVAL_QUESTIONS_PATH
    questions = []
    with open(q_file, "r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))
    return questions

def run_tests():
    questions = get_questions()
    
    # Pick one from each category
    q_a = next(q for q in questions if q["category"] == "A")
    q_b = next(q for q in questions if q["category"] == "B")
    q_c = next(q for q in questions if q["category"] == "C")
    
    test_cases = [
        ("Category A (No Filter)", q_a),
        ("Category B (With Filter)", q_b),
        ("Category C (Unrelated)", q_c),
    ]
    
    for label, q_data in test_cases:
        print("=" * 80)
        print(f"--- {label} ---")
        print(f"Question ID: {q_data['id']}")
        print(f"Question: {q_data['question']}")
        print(f"Filters: {q_data.get('filters', {})}")
        print("-" * 40)
        
        res = retrieve(
            question=q_data["question"],
            filters=q_data.get("filters")
        )
        
        print(f"Context Found: {res['context_found']}")
        print(f"Best Similarity: {res['best_similarity_score']:.4f}")
        print(f"Chunks Retrieved: {len(res['chunks'])}")
        
        if res["chunks"]:
            print("\nSources:")
            for c in res["chunks"]:
                print(f"  - {c['source_file']} (idx {c['chunk_index']}) [sim: {c['similarity_score']:.4f}]")
            
            print("\n--- Context Block ---")
            print(res["context_block"])
        print("=" * 80)
        print()

if __name__ == "__main__":
    run_tests()
