# Query Run Examples (CLI Transcripts)

Since this project runs in a terminal/backend environment without a GUI, the following CLI transcripts represent the query responses.

## 1. Filtered Query (Category B)
This demonstrates a query using metadata filtering (`source_file='api_reference.md'`) to narrow down the context.

```text
================================================================================
--- Category B (With Filter) ---
Question ID: q011
Question: What is the Vaultly API base URL?
Filters: {'source_file': 'api_reference.md'}
----------------------------------------
Context Found: True
Best Similarity: 0.6972
Chunks Retrieved: 2

[Retrieval Step complete, invoking generator...]

Generation Result:
Latency: 591 ms
Tokens: Prompt=999, Completion=32, Total=1031
Citations parsed: []

--- Answer ---
[Chunk 1 | source: api_reference.md | chunk_idx: 0] 
**Base URL:** https://api.vaultly.io/v1
================================================================================
```

## 2. No-Context Query (Category C)
This demonstrates the system's guardrail when a question has no relevant chunks in the database (exceeds the distance threshold).

```text
================================================================================
--- Category C (Unrelated) ---
Question ID: q017
Question: What is the boiling point of liquid nitrogen in degrees Celsius?
Filters: {}
----------------------------------------
Context Found: False

Generation Result:
Latency: 0 ms
Citations parsed: []

--- Answer ---
I cannot answer this question from the provided context.
================================================================================
```
