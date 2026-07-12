# Lab 3 - Semantic Search and GraphRAG

Run two notebooks that build GraphRAG retrieval over the SEC 10-K knowledge graph using the neo4j-graphrag Python library. You progress from pure vector search to graph-enriched retrieval, seeing why traversing relationships returns richer context than vector similarity alone.

## What You'll Learn

- **Vector Search**: Use `VectorRetriever` to find semantically similar chunks and generate answers with `GraphRAG`
- **Graph-Enriched Search**: Use `VectorCypherRetriever` to combine vector search with Cypher graph traversal for richer, connected context

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 1** (Aura instance created and knowledge graph loaded)
- `CONFIG.txt` at the project root filled in with `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `MODEL_ID`, and `REGION`
- A running environment (SageMaker Studio or GitHub Codespace)

> **Note:** This lab uses the same Neo4j Aura instance from Lab 1. The knowledge graph — including document chunks, chunk embeddings, and the `chunkEmbeddings` vector index — must already be loaded. These notebooks do not load data themselves. To see how that data is built, run the optional [Lab 2 - Data Pipeline](../Lab_2_Data_Pipeline).

## Notebooks

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [01_vector_retriever.ipynb](01_vector_retriever.ipynb) | Vector Retriever | Semantic search with `VectorRetriever` and end-to-end question answering with `GraphRAG` |
| [02_vector_cypher_retriever.ipynb](02_vector_cypher_retriever.ipynb) | VectorCypher Retriever | Graph-enriched retrieval that adds companies, products, and risk factors to vector search results |

> **Beyond these two retrievers:** neo4j-graphrag also offers hybrid retrievers (`HybridRetriever` and `HybridCypherRetriever`) that fuse vector search with fulltext (keyword) search to boost recall on exact names and tickers, plus Text2Cypher for fact and aggregation questions (covered in Lab 6). This lab focuses on the two vector-based strategies; the others build on the same patterns.

## Next Steps

After completing this lab, continue to [Lab 4 - Strands GraphRAG Agent](../Lab_4_GraphRAG_Agent) to wrap these retrievers as agent tools, or to [Lab 6 - Neo4j MCP Server](../Lab_6_MCP_Server) to connect agents to Neo4j via MCP.
