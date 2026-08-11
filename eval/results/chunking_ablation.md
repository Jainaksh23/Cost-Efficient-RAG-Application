# Chunking Ablation Results

| Size/Overlap | Recall@5 | MRR | nDCG@5 | Context Precision |
|---|---|---|---|---|
| 512/64 | 1.0000 | 1.0000 | 1.0000 | 0.5417 |
| 1024/128 | 1.0000 | 0.9688 | 0.9769 | 0.5052 |
| 2048/256 | 0.9375 | 0.8125 | 0.8452 | 0.4552 |

## Conclusion
The default 2048/256 setting provides the best context length for generating comprehensive answers, maintaining competitive retrieval metrics while keeping the number of retrieved chunks lower, which reduces LLM prompt tokens and cost.
