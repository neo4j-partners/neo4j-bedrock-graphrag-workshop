# Lab 6 - Consolidated GraphRAG

Build a complete GraphRAG pipeline over SEC 10-K financial filing data using Neo4j and Amazon Bedrock. Six notebooks progress from data loading to hybrid retrieval.

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
| [05_fulltext_search.ipynb](05_fulltext_search.ipynb) | Fulltext Search | A fulltext index on Chunk text with fuzzy, wildcard, and boolean search operators |
| [06_hybrid_search.ipynb](06_hybrid_search.ipynb) | Hybrid Search | `HybridRetriever` and `HybridCypherRetriever` combining vector and fulltext search with tunable alpha |

## Next Steps

After completing this lab, continue to [Lab 7](../Lab_7_Neo4j_MCP_Agent/) to build MCP agents that use these retrieval patterns as tools.
