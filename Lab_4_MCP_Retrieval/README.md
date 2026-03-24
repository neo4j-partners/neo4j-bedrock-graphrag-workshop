# Lab 4 - MCP Retrieval

Run three notebooks that search a Neo4j knowledge graph through the Model Context Protocol (MCP), progressing from vector search to graph-enriched retrieval to hybrid search.

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 1** (Neo4j Aura instance created and running)
- Data loaded into Neo4j with embeddings, entity nodes, and fulltext indexes (from the data loading pipeline)
- Filled in your credentials in `CONFIG.txt` at the project root, including `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`
- A running environment (SageMaker Studio or GitHub Codespace)

## Notebooks

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [01_vector_search_mcp.ipynb](01_vector_search_mcp.ipynb) | Vector Search via MCP | Semantic vector search with Bedrock Nova embeddings through an MCP agent |
| [02_graph_enriched_search_mcp.ipynb](02_graph_enriched_search_mcp.ipynb) | Graph-Enriched Search via MCP | Vector search enriched with document metadata, neighboring chunks, and entity traversal (companies, products, risk factors) |
| [03_fulltext_hybrid_search_mcp.ipynb](03_fulltext_hybrid_search_mcp.ipynb) | Fulltext and Hybrid Search via MCP | Keyword search with Lucene operators and agent-driven hybrid search combining vector and fulltext via custom `@tool` wrappers |

## Next Steps

After completing this lab, continue to [Lab 6](../Lab_6_GraphRAG/) for direct library-based retrieval, or to [Lab 7](../Lab_7_Neo4j_MCP_Agent/) to build full MCP agents.
