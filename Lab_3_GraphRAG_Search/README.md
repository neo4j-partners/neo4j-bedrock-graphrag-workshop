# Lab 3 - Semantic Search and GraphRAG

Run three notebooks that build GraphRAG retrieval over the SEC 10-K knowledge graph using the neo4j-graphrag Python library. You progress from pure vector search to graph-enriched retrieval to hybrid search, seeing why traversing relationships returns richer context than vector similarity alone and how fusing keyword and semantic signals catches what either misses.

> **Run this in Amazon SageMaker AI.** These notebooks are designed to run in Amazon SageMaker AI Studio. Running them locally (e.g. VS Code) or elsewhere is not supported and will fail. Follow the [Environment Setup guide](https://neo4j-partners.github.io/neo4j-bedrock-graphrag-workshop/workshop/neo4j-bedrock-graphrag-workshop/1.0/part2-setup-instructions.html) to launch SageMaker AI Studio first.

## What You'll Learn

- **Vector Search**: Use `VectorRetriever` to find semantically similar chunks and generate answers with `GraphRAG`
- **Graph-Enriched Search**: Use `VectorCypherRetriever` to combine vector search with Cypher graph traversal for richer, connected context
- **Hybrid Search**: Use `HybridRetriever` and `HybridCypherRetriever` to fuse vector and full-text keyword search, and re-rank the merged results with the `NAIVE` and `LINEAR` rankers

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 1** (Aura instance created and knowledge graph loaded)
- `CONFIG.txt` at the project root filled in with `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `MODEL_ID`, and `REGION`
- A running Amazon SageMaker AI Studio environment (see [Part 2 Setup Instructions](https://neo4j-partners.github.io/neo4j-bedrock-graphrag-workshop/workshop/neo4j-bedrock-graphrag-workshop/1.0/part2-setup-instructions.html))

> **Note:** This lab uses the same Neo4j Aura instance from Lab 1. The knowledge graph — including document chunks, chunk embeddings, and the `chunkEmbeddings` vector index — must already be loaded. These notebooks do not load data themselves. To see how that data is built, run the optional [Lab 2 - Data Pipeline](../Lab_2_Data_Pipeline).

## Notebooks

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [01_vector_retriever.ipynb](01_vector_retriever.ipynb) | Vector Retriever | Semantic search with `VectorRetriever` and end-to-end question answering with `GraphRAG` |
| [02_vector_cypher_retriever.ipynb](02_vector_cypher_retriever.ipynb) | VectorCypher Retriever | Graph-enriched retrieval that adds companies, products, and risk factors to vector search results |
| [03_hybrid_retriever.ipynb](03_hybrid_retriever.ipynb) | Hybrid Retriever | Full-text keyword search plus `HybridRetriever` / `HybridCypherRetriever`, fusing vector and keyword signals with the `NAIVE` and `LINEAR` re-rankers |

> **The other strategies:** these notebooks build **Vector Search**, **Graph-Enriched Search**, **Full-text Search**, and **Hybrid Search**. The same patterns are also shown as raw Cypher in the [Lab 3 sample queries](https://neo4j-partners.github.io/neo4j-bedrock-graphrag-workshop/workshop/neo4j-bedrock-graphrag-workshop/1.0/lab3-sample-queries.html). GraphRAG also uses **Text2Cypher** for counts and lookups (covered in Lab 6). All build on the same patterns.

## Next Steps

After completing this lab, continue to [Lab 4 - Strands GraphRAG Agent](../Lab_4_GraphRAG_Agent) to wrap these retrievers as agent tools, or to [Lab 6 - Neo4j MCP Server](../Lab_6_MCP_Server) to connect agents to Neo4j via MCP.
