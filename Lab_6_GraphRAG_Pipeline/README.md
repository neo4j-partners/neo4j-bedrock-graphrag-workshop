# Lab 6 - Building a GraphRAG Data Pipeline

Build a complete GraphRAG pipeline from scratch using SEC 10-K financial filing data. Three notebooks progress from loading raw data into a knowledge graph to running graph-enriched retrieval queries.

## What You'll Learn

- **Data Loading**: Build a two-layer knowledge graph — structured entities (Company, Product, RiskFactor) and unstructured document chunks — connected by cross-links
- **Embeddings**: Generate vector embeddings with Amazon Nova and create a vector index for semantic search
- **VectorCypherRetriever**: Combine vector similarity search with Cypher graph traversal to enrich LLM context with entity data

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 1** (Neo4j Aura instance created and running)
- Filled in your credentials in `CONFIG.txt` at the project root
- A running environment (SageMaker Studio or GitHub Codespace)

**Note:** This lab wipes and rebuilds the graph from scratch using `financial_data.json`. It does not depend on data from previous labs.

## Notebooks

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [01_data_loading.ipynb](01_data_loading.ipynb) | Data Loading | Company, Product, RiskFactor, Document, and Chunk nodes linked by `OFFERS`, `FACES_RISK`, `FILED`, `FROM_DOCUMENT`, `NEXT_CHUNK`, and `FROM_CHUNK` relationships |
| [02_embeddings.ipynb](02_embeddings.ipynb) | Embeddings | Vector embeddings on every Chunk node, plus a `chunkEmbeddings` vector index |
| [03_vector_cypher_retriever.ipynb](03_vector_cypher_retriever.ipynb) | VectorCypher Retriever | A `VectorCypherRetriever` that enriches each vector match with document metadata and connected entities via Cypher, wired into a `GraphRAG` pipeline |
