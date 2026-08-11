import json
import re
import string
import sys
import time
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from groq import Groq

import config
from retrieval.assembler import retrieve
from generation.generator import generate_answer

def normalize_answer(s: str) -> str:
    """Lower text and remove punctuation, articles and extra whitespace."""
    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    if s is None:
        return ""
    return white_space_fix(remove_articles(remove_punc(lower(s))))

def f1_score(prediction: str, ground_truth: str) -> float:
    prediction_tokens = normalize_answer(prediction).split()
    ground_truth_tokens = normalize_answer(ground_truth).split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    return (2 * precision * recall) / (precision + recall)

def exact_match_score(prediction: str, ground_truth: str) -> float:
    return 1.0 if normalize_answer(prediction) == normalize_answer(ground_truth) else 0.0

def llm_judge(metric: str, criterion: str, question: str, context: str, answer: str) -> dict:
    prompt = f"""You are a strict, objective evaluator for a RAG system. Given a question, retrieved context,
and a generated answer, score the {metric} on a 1-5 integer scale. Respond with ONLY JSON:
{{"score": <int>, "reason": "<one sentence>"}}.
Question: {question}
Context: {context}
Answer: {answer}
Rubric for {metric}: {criterion}"""

    client = Groq(api_key=config.GROQ_API_KEY, timeout=10)
    
    def try_call():
        response = client.chat.completions.create(
            model=config.GROQ_JUDGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        content = response.choices[0].message.content or ""
        # try to parse json, stripping any markdown formatting
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)

    for attempt in range(3):
        try:
            time.sleep(3)
            return try_call()
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate limit" in err_str.lower():
                print(f"Rate limit error: {err_str}", flush=True)
                match_s = re.search(r"try again in ([\d\.]+)s", err_str.lower())
                match_ms = re.search(r"try again in ([\d\.]+)ms", err_str.lower())
                match_m_s = re.search(r"try again in (\d+)m([\d\.]+)s", err_str.lower())
                
                if match_m_s:
                    wait_time = float(match_m_s.group(1)) * 60 + float(match_m_s.group(2))
                elif match_s:
                    wait_time = float(match_s.group(1))
                elif match_ms:
                    wait_time = float(match_ms.group(1)) / 1000.0
                else:
                    wait_time = 20.0
                    
                print(f"Rate limit hit in judge. Waiting {wait_time}s and retrying ({attempt+1}/3)...", flush=True)
                time.sleep(wait_time)
            else:
                print(f"Warning: Judge call failed on attempt {attempt+1}: {e}", flush=True)
                if attempt == 2:
                    return {"score": None, "reason": f"Failed after 3 attempts: {e}"}
                time.sleep(5)
    return {"score": None, "reason": "Failed to parse judge output after 3 attempts."}

def safe_generate_answer(q_text, retrieval_result):
    for attempt in range(3):
        time.sleep(5)
        gen_result = generate_answer(q_text, retrieval_result)
        answer = gen_result.get("answer", "")
        if answer and answer.startswith("Error: API Error -"):
            err_str = answer
            if "429" in err_str or "rate limit" in err_str.lower():
                print(f"Rate limit error: {err_str}", flush=True)
                match_s = re.search(r"try again in ([\d\.]+)s", err_str.lower())
                match_ms = re.search(r"try again in ([\d\.]+)ms", err_str.lower())
                match_m_s = re.search(r"try again in (\d+)m([\d\.]+)s", err_str.lower())
                
                if match_m_s:
                    wait_time = float(match_m_s.group(1)) * 60 + float(match_m_s.group(2))
                elif match_s:
                    wait_time = float(match_s.group(1))
                elif match_ms:
                    wait_time = float(match_ms.group(1)) / 1000.0
                else:
                    wait_time = 20.0
                    
                print(f"Rate limit hit in generation. Waiting {wait_time}s and retrying ({attempt+1}/3)...", flush=True)
                time.sleep(wait_time)
                continue
            else:
                print(f"Warning: Generation failed: {answer}", flush=True)
                if attempt == 2:
                    return gen_result
                continue
        elif answer and answer.startswith("Error:"):
            print(f"Warning: Generation error: {answer}", flush=True)
            if attempt == 2:
                return gen_result
            continue
        return gen_result
    return {"answer": "Error: Failed after 3 attempts", "citations": [], "token_usage": None, "context_found": True, "generation_latency_ms": 0}

def run_answer_eval():
    questions_path = Path("eval/questions.jsonl")
    results_dir = Path("eval/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    questions = []
    with open(questions_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))
                
    results = []
    
    sum_em = 0.0
    sum_f1 = 0.0
    sum_faithfulness = 0.0
    sum_relevance = 0.0
    count_ab = 0
    valid_faithfulness = 0
    valid_relevance = 0
    
    # Calculate calls and print
    expected_calls = sum([1 for q in questions if q.get("category") != "C"]) * 3
    print(f"Total Groq calls expected: ~{expected_calls} (questions * 3 calls)", flush=True)
    print(f"Expected minimum runtime at 5s delay: ~{expected_calls * 5 / 60:.1f} minutes", flush=True)
    
    for q in questions:
        if q.get("category") == "C":
            continue
            
        count_ab += 1
        q_text = q.get("question")
        filters = q.get("filters", {})
        gold_answer = q.get("gold_answer", "")
        
        retrieval_result = retrieve(q_text, top_k=config.TOP_K, filters=filters)
        gen_result = safe_generate_answer(q_text, retrieval_result)
        
        answer = gen_result.get("answer", "")
        context = retrieval_result.get("context_block", "")
        
        em = exact_match_score(answer, gold_answer)
        f1 = f1_score(answer, gold_answer)
        sum_em += em
        sum_f1 += f1
        
        faithfulness = llm_judge(
            "Faithfulness", 
            "5=fully supported by context, 1=hallucinated or contradicts context",
            q_text, context, answer
        )
        relevance = llm_judge(
            "Answer Relevance",
            "5=fully relevant to the question, 1=off-topic or completely avoids the question",
            q_text, context, answer
        )
        
        f_score = faithfulness.get("score")
        if f_score is not None:
            sum_faithfulness += f_score
            valid_faithfulness += 1
            
        r_score = relevance.get("score")
        if r_score is not None:
            sum_relevance += r_score
            valid_relevance += 1
            
        results.append({
            "id": q.get("id"),
            "question": q_text,
            "em": em,
            "f1": f1,
            "faithfulness_score": f_score,
            "faithfulness_reason": faithfulness.get("reason"),
            "relevance_score": r_score,
            "relevance_reason": relevance.get("reason")
        })
        print(f"Evaluated {q.get('id')}: EM={em}, F1={f1:.2f}, F={f_score}, R={r_score}", flush=True)
        
    avg_em = sum_em / count_ab if count_ab > 0 else 0
    avg_f1 = sum_f1 / count_ab if count_ab > 0 else 0
    avg_faithfulness = sum_faithfulness / valid_faithfulness if valid_faithfulness > 0 else 0
    avg_relevance = sum_relevance / valid_relevance if valid_relevance > 0 else 0
    
    aggregate = {
        "Exact Match": avg_em,
        "F1 Score": avg_f1,
        "Faithfulness": avg_faithfulness,
        "Answer Relevance": avg_relevance
    }
    
    output = {
        "aggregate": aggregate,
        "per_question": results
    }
    
    with open(results_dir / "answer_metrics.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        
    md_content = "# Answer Metrics\n\n## Aggregate\n| Metric | Score |\n|---|---|\n"
    for k, v in aggregate.items():
        md_content += f"| {k} | {v:.4f} |\n"
        
    md_content += "\n## Per Question\n| ID | EM | F1 | Faithfulness | Relevance |\n|---|---|---|---|---|\n"
    for r in results:
        f_s = r['faithfulness_score'] if r['faithfulness_score'] is not None else "N/A"
        r_s = r['relevance_score'] if r['relevance_score'] is not None else "N/A"
        md_content += f"| {r['id']} | {r['em']:.2f} | {r['f1']:.2f} | {f_s} | {r_s} |\n"
        
    with open(results_dir / "answer_metrics.md", "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print("Answer eval complete.")

if __name__ == "__main__":
    run_answer_eval()
