# Lab 4 - MCP Retrieval

Search a Neo4j knowledge graph through the Model Context Protocol (MCP). Instead of connecting to Neo4j with a driver and using retriever classes directly, an AI agent uses MCP tools to execute Cypher queries against the database. The three notebooks progress from basic vector search to graph-enriched retrieval to hybrid search combining keywords and semantics.

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 1** (Neo4j Aura instance created and running)
- Data loaded into Neo4j with embeddings, entity nodes, and fulltext indexes (from the data loading pipeline)
- Filled in your credentials in `CONFIG.txt` at the project root, including `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`
- A running environment (SageMaker Studio or GitHub Codespace)

## Notebooks

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [01_vector_search_mcp.ipynb](01_vector_search_mcp.ipynb) | Vector Search via MCP | Semantic vector search with Bedrock Titan embeddings through an MCP agent |
| [02_graph_enriched_search_mcp.ipynb](02_graph_enriched_search_mcp.ipynb) | Graph-Enriched Search via MCP | Vector search enriched with document metadata, neighboring chunks, and entity traversal (companies, products, risk factors) |
| [03_fulltext_hybrid_search_mcp.ipynb](03_fulltext_hybrid_search_mcp.ipynb) | Fulltext and Hybrid Search via MCP | Keyword search with Lucene operators and agent-driven hybrid search combining vector and fulltext via custom `@tool` wrappers |

## How the Notebooks Connect

Notebook 01 introduces the basic pattern: embed a query, pass the embedding to the agent, and let the agent execute vector search Cypher through MCP. Notebook 02 extends this by adding graph traversal that pulls in document metadata, neighboring chunks, and connected entities (companies, products, risk factors). Notebook 03 introduces an alternative search method (fulltext keyword search) and then combines both approaches for agent-driven hybrid search using custom `@tool` wrappers that encapsulate embedding generation.

## MCP Search vs Direct Library Search

All three notebooks use the same underlying Neo4j indexes and graph structure as Lab 6. The difference is in how the search is executed:

| Aspect | Lab 4 (MCP) | Lab 6 (neo4j-graphrag library) |
|--------|-------------|-------------------------------|
| Connection | MCP server via AgentCore Gateway | Direct Neo4j driver |
| Query execution | Agent calls `execute-query` MCP tool | Retriever class methods |
| Embedding | Client-side (Bedrock Titan), passed to agent or wrapped in `@tool` | Retriever calls embedder internally |
| Hybrid search | Agent runs both queries and combines results | `HybridRetriever` handles score normalization and alpha tuning |
| Graph traversal | Cypher in agent prompt | `retrieval_query` parameter on retriever classes |

## What's Not Covered Here

This lab focuses on MCP-based retrieval. For the following topics, see Lab 6:

- **Direct driver connections** — Lab 6 uses `neo4j.GraphDatabase.driver()` for direct access
- **neo4j-graphrag retriever classes** — `VectorRetriever`, `VectorCypherRetriever`, `HybridRetriever`, `HybridCypherRetriever`
- **Programmatic alpha tuning** — `HybridRetriever.search(alpha=0.5)` with automatic score normalization
- **GraphRAG pipeline** — `GraphRAG(llm=llm, retriever=retriever).search()` for end-to-end RAG
- **Data loading and embedding generation** — Building the graph from scratch

## Next Steps

After completing this lab, continue to [Lab 6](../Lab_6_GraphRAG/) for direct library-based retrieval, or to [Lab 7](../Lab_7_Neo4j_MCP_Agent/) to build full MCP agents.
