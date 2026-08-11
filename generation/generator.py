"""
generation/generator.py
LLM Generation layer calling the Groq API.
"""
from __future__ import annotations
import time
import re

from groq import Groq
from groq import APIError

import config

def generate_answer(question: str, retrieval_result: dict) -> dict:
    if not retrieval_result.get("context_found"):
        return {
            "answer": "I cannot answer this question from the provided context.",
            "citations": [],
            "token_usage": None,
            "context_found": False,
            "generation_latency_ms": 0
        }
        
    prompt = f"Context:\n{retrieval_result['context_block']}\n\nQuestion:\n{question}"
    
    start_time = time.time()
    try:
        system_instruction = (
            "You are a helpful assistant. You must answer the user's question ONLY using the provided context. "
            "Cite chunk labels inline like [Chunk 1]. "
            "If the context genuinely doesn't support an answer, respond exactly with: "
            "'I cannot answer this question from the provided context.'"
        )
        
        client = Groq(api_key=config.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        answer_text = response.choices[0].message.content or ""
        
        # Extract citations
        # Looking for things like [Chunk 1], [Chunk 2], etc.
        citations = []
        matches = re.findall(r"\[Chunk (\d+)\]", answer_text)
        num_retrieved_chunks = len(retrieval_result.get("chunks", []))
        for match in matches:
            idx = int(match)
            if idx >= 1 and idx <= num_retrieved_chunks:
                if idx not in citations:
                    citations.append(idx)
                
        token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        if response.usage:
            token_usage["prompt_tokens"] = response.usage.prompt_tokens
            token_usage["completion_tokens"] = response.usage.completion_tokens
            token_usage["total_tokens"] = response.usage.total_tokens
            
        return {
            "answer": answer_text,
            "citations": sorted(citations),
            "token_usage": token_usage,
            "context_found": True,
            "generation_latency_ms": latency_ms
        }
        
    except APIError as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "answer": f"Error: API Error - {str(e)}",
            "citations": [],
            "token_usage": None,
            "context_found": True,
            "generation_latency_ms": latency_ms
        }
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "answer": f"Error: Unexpected error - {str(e)}",
            "citations": [],
            "token_usage": None,
            "context_found": True,
            "generation_latency_ms": latency_ms
        }
