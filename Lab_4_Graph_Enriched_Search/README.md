# Lab 4 - Graph-Enriched Search

Run three notebooks that explore graph-enriched search — retrieval strategies that take advantage of the knowledge graph's structure. You start with the basics of connecting a Strands Agent to Neo4j via MCP, then progress from vector search to graph-enriched search that follows relationships to connected entities.

## What You'll Learn

- **Strands + MCP Basics**: Connect an agent to Neo4j via MCP and query the knowledge graph using natural language (Text2Cypher)
- **Vector Search**: Embed queries and find semantically similar chunks using Bedrock Nova embeddings
- **Graph-Enriched Search**: Follow relationships from matched chunks to documents, companies, products, and risk factors

## Prerequisites

Before starting this lab, make sure you have:

- `CONFIG.txt` at the project root filled in with `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`
- A running environment (SageMaker Studio or GitHub Codespace)

> **Note:** This lab connects to Neo4j through a pre-deployed MCP server. The database, embeddings, and indexes are already set up by the workshop admin — you do not need to complete Lab 1 or load data yourself.

## Notebooks

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [00_intro_strands_mcp.ipynb](00_intro_strands_mcp.ipynb) | Introduction to Strands + MCP | Connect an agent to Neo4j via MCP — the agent discovers tools and writes its own Cypher |
| [01_vector_search_mcp.ipynb](01_vector_search_mcp.ipynb) | Vector Search | Semantic vector search with Bedrock Nova embeddings — the foundation for graph-enriched retrieval |
| [02_graph_enriched_search_mcp.ipynb](02_graph_enriched_search_mcp.ipynb) | Graph-Enriched Search | Vector search enriched with document metadata, neighboring chunks, and entity traversal |

## Next Steps

After completing this lab, continue to [Lab 5](../Lab_5_GraphRAG/) for direct library-based retrieval using the neo4j-graphrag Python package.
