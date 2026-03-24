# Lab 4 - Graph-Enriched Search

Run three notebooks that explore graph-enriched search — retrieval strategies that take advantage of the knowledge graph's structure. You progress from basic vector search, to graph-enriched search that follows relationships to connected entities, to hybrid search that combines semantic and keyword matching.

## What You'll Learn

- **Vector Search**: Embed queries and find semantically similar chunks using Bedrock Nova embeddings
- **Graph-Enriched Search**: Follow relationships from matched chunks to documents, companies, products, and risk factors
- **Hybrid Search**: Combine fulltext keyword search with vector similarity using custom `@tool` wrappers

## Prerequisites

Before starting this lab, make sure you have:

- `CONFIG.txt` at the project root filled in with `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`
- A running environment (SageMaker Studio or GitHub Codespace)

> **Note:** This lab connects to Neo4j through a pre-deployed MCP server. The database, embeddings, and indexes are already set up by the workshop admin — you do not need to complete Lab 1 or load data yourself.

## Notebooks

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [01_vector_search_mcp.ipynb](01_vector_search_mcp.ipynb) | Vector Search | Semantic vector search with Bedrock Nova embeddings — the foundation for graph-enriched retrieval |
| [02_graph_enriched_search_mcp.ipynb](02_graph_enriched_search_mcp.ipynb) | Graph-Enriched Search | Vector search enriched with document metadata, neighboring chunks, and entity traversal |
| [03_fulltext_hybrid_search_mcp.ipynb](03_fulltext_hybrid_search_mcp.ipynb) | Fulltext and Hybrid Search | Keyword search with Lucene operators and agent-driven hybrid search via custom `@tool` wrappers |

## Next Steps

After completing this lab, continue to [Lab 5](../Lab_6_GraphRAG/) for direct library-based retrieval using the neo4j-graphrag Python package.
