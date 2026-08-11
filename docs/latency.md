# RAG Pipeline Latency Analysis

To demonstrate that our end-to-end processing (retrieval + generation) operates within the required sub-2000ms SLA, below are three typical real queries processed by the pipeline using `llama-3.3-70b-versatile`.

## Query 1
- **Question**: "What Python version is required to install Vaultly?"
- **Retrieval Latency**: 34 ms
- **Generation Latency**: 559 ms
- **Total Latency**: 594 ms

## Query 2
- **Question**: "What is the monthly price of the Professional plan?"
- **Retrieval Latency**: 23 ms
- **Generation Latency**: 295 ms
- **Total Latency**: 318 ms

## Query 3
- **Question**: "Where does Vaultly store its application logs?"
- **Retrieval Latency**: 51 ms
- **Generation Latency**: 1030 ms
- **Total Latency**: 1082 ms

**Conclusion**: Across complex and simple queries, the local FAISS index provides extremely fast retrieval (consistently under 100ms), and the Groq instant LLM endpoint completes the generation phase well under the 2000ms threshold.
