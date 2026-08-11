"""
scripts/test_generation.py
Test the end-to-end generation pipeline on 3 specific cases from questions.jsonl.
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from retrieval.assembler import retrieve
from generation.generator import generate_answer
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
        
        # 1. Retrieve
        retrieval_res = retrieve(
            question=q_data["question"],
            filters=q_data.get("filters")
        )
        
        print(f"Context Found: {retrieval_res['context_found']}")
        if retrieval_res["context_found"]:
            print(f"Best Similarity: {retrieval_res['best_similarity_score']:.4f}")
            print(f"Chunks Retrieved: {len(retrieval_res['chunks'])}")
            print("\n[Retrieval Step complete, invoking generator...]")
            
        # 2. Generate
        gen_res = generate_answer(
            question=q_data["question"],
            retrieval_result=retrieval_res
        )
        
        print("\nGeneration Result:")
        print(f"Latency: {gen_res['generation_latency_ms']} ms")
        if gen_res['token_usage']:
            print(f"Tokens: Prompt={gen_res['token_usage']['prompt_tokens']}, "
                  f"Completion={gen_res['token_usage']['completion_tokens']}, "
                  f"Total={gen_res['token_usage']['total_tokens']}")
        print(f"Citations parsed: {gen_res['citations']}")
        
        print("\n--- Answer ---")
        print(gen_res['answer'])
        print("=" * 80)
        print()

if __name__ == "__main__":
    run_tests()
