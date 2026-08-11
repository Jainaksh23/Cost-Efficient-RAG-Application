# Vaultly RAG Architecture

```mermaid
flowchart TD
    %% Data Sources
    subgraph Sources [Document Sources]
        PDF[PDF Files]
        HTML[HTML Pages]
        MD[Markdown Files]
    end

    %% Ingestion Pipeline
    subgraph Ingestion [Ingestion Pipeline]
        DocIngest[Document Ingestion<br>PyMuPDF / BeautifulSoup]
        Chunking[Chunking<br>Size: 2048, Overlap: 256]
        EmbedModel[Embedding Model<br>all-MiniLM-L6-v2<br>Dim: 384]
    end
    
    %% Storage
    subgraph Storage [Storage Layer]
        FAISS[(FAISS Vector Store<br>L2 Distance)]
        SQLite[(SQLite DB<br>Metadata + Text)]
    end

    %% Query Pipeline
    subgraph Retrieval [Retrieval & Query]
        API[API Endpoint<br>/query POST]
        MetadataFilter[Metadata Filter<br>e.g. source_file]
        TopK[Top-k Retrieval<br>k=5]
        NoContext[No-Context Response<br>"I cannot answer..."]
        Generator[LLM Generation<br>Groq: llama-3.3-70b-versatile]
        FinalAnswer[Final Answer<br>with Citations]
    end

    %% Flow
    PDF --> DocIngest
    HTML --> DocIngest
    MD --> DocIngest
    
    DocIngest --> Chunking
    Chunking --> EmbedModel
    EmbedModel --> FAISS
    Chunking --> SQLite
    
    API --> MetadataFilter
    MetadataFilter --> TopK
    TopK <--> FAISS
    TopK <--> SQLite
    
    TopK --> |Context Found?| Check{Context?}
    Check -- No --> NoContext
    Check -- Yes --> Generator
    Generator --> FinalAnswer
```
