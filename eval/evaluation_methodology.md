# Evaluation Methodology

## Retrieval Metrics

Retrieval evaluation assesses the ability of the system to find relevant context for a given question. 

### Relevance Definition
The ground truth provided in `eval/questions.jsonl` defines relevance at the **source file level** (e.g., `kubernetes_docs.md`), not at the exact chunk level. 

When a chunk is retrieved, it is considered a "relevant hit" if its `source_file` metadata matches any of the expected source files for that question. 

### Context Precision and nDCG
Because multiple chunks can be retrieved from the same relevant source file, our metrics are calculated as follows:
- **Recall / Hit Rate:** Measures whether at least one relevant source file was found in the top-k results.
- **MRR (Mean Reciprocal Rank):** Based on the rank of the *first* retrieved chunk that comes from a relevant source file.
- **nDCG@k:** To prevent a single relevant source document from receiving multiple relevance credits (which would falsely inflate DCG above IDCG), we track credited sources. Once a retrieved chunk from a relevant source file is scored, subsequent chunks from that same source file receive a relevance score of 0.
- **Context Precision:** Measures the proportion of relevant chunks in the retrieved set, but since ground truth is at the file level, it essentially measures the proportion of retrieved chunks that come from *any* of the relevant source files.

## Answer Metrics

Answer generation evaluation uses a combination of deterministic matching and LLM-as-a-judge:

- **Exact Match (EM) / F1 Score:** Computes token overlap and exact string matching between the generated answer and a human-written gold answer.
- **Faithfulness:** An LLM judge evaluates if the generated answer is fully supported by the retrieved context (1-5 scale). 5 indicates no hallucination.
- **Answer Relevance:** An LLM judge evaluates if the generated answer directly addresses the user's question (1-5 scale). 5 indicates the answer is fully on-topic.
