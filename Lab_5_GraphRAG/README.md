# Lab 5 - Consolidated GraphRAG

Build a complete GraphRAG pipeline over SEC 10-K financial filing data using Neo4j and Amazon Bedrock. Six notebooks progress from data loading to hybrid retrieval.

## What You'll Learn

- **Data Loading**: Build Document and Chunk nodes linked by graph relationships
- **Embeddings**: Generate vector embeddings with Amazon Nova and create a vector index
- **VectorRetriever**: Pure semantic similarity search over embedded chunks
- **VectorCypherRetriever**: Vector search enriched with graph traversal to connected entities
- **Hybrid RAG**: Hybrid retrieval (vector + fulltext) powering GraphRAG answer generation
- **HybridRetriever**: Combined vector and fulltext search with tunable alpha parameter

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 1** (Neo4j Aura instance created and running)
- Filled in your credentials in `CONFIG.txt` at the project root
- A running environment (SageMaker Studio or GitHub Codespace)

## Notebooks

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [01_data_loading.ipynb](01_data_loading.ipynb) | Data Loading | Document and Chunk nodes linked by `FROM_DOCUMENT` and `NEXT_CHUNK` relationships |
| [02_embeddings.ipynb](02_embeddings.ipynb) | Embeddings | Vector embeddings on every Chunk node, plus a `chunkEmbeddings` vector index |
| [03_vector_retriever.ipynb](03_vector_retriever.ipynb) | Vector Retriever | A `VectorRetriever` wired into a `GraphRAG` pipeline for semantic Q&A |
| [04_vector_cypher_retriever.ipynb](04_vector_cypher_retriever.ipynb) | VectorCypher Retriever | A `VectorCypherRetriever` that enriches each vector match with neighboring chunks and document metadata via Cypher |
| [05_hybrid_rag.ipynb](05_hybrid_rag.ipynb) | Hybrid RAG | `HybridRetriever` + `GraphRAG` comparing vector-only vs hybrid RAG answers with alpha tuning |
| [06_hybrid_search.ipynb](06_hybrid_search.ipynb) | Hybrid Search | `HybridRetriever` and `HybridCypherRetriever` combining vector and fulltext search with tunable alpha |

## Next Steps

After completing this lab, continue to [Lab 6](../Lab_6_Advanced_Agents/) to build autonomous agents that discover the graph schema and write their own Cypher queries.
