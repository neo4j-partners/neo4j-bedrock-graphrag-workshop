# Lab 4 - GraphRAG Retrievers

Run four notebooks that build a GraphRAG search pipeline using the neo4j-graphrag Python library. You start by loading pre-computed chunk embeddings into the knowledge graph from Labs 1-2, build retrieval pipelines that progress from pure vector search to graph-enriched search, then wrap both retrievers as agent tools so the model picks the right strategy per question.

## What You'll Learn

- **Data Loading**: Add document chunks with pre-computed embeddings to an existing knowledge graph
- **Vector Search**: Use `VectorRetriever` to find semantically similar chunks and generate answers with `GraphRAG`
- **Graph-Enriched Search**: Use `VectorCypherRetriever` to combine vector search with Cypher graph traversal for richer context
- **Agent-Driven Retrieval**: Wrap both retrievers as Strands `@tool` functions and let the agent choose the right strategy per question

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 1** (Aura instance created and knowledge graph loaded)
- `CONFIG.txt` at the project root filled in with `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `MODEL_ID`, and `REGION`
- A running environment (SageMaker Studio or GitHub Codespace)

> **Note:** This lab uses the same Neo4j Aura instance from Labs 1-2. The structured graph (companies, products, risk factors, asset managers) must already be loaded.

## Notebooks

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [01_load_and_query.ipynb](01_load_and_query.ipynb) | Load Data and Query | Load chunk embeddings into the graph, create a vector index, link entities to chunks, and run test queries |
| [02_vector_retriever.ipynb](02_vector_retriever.ipynb) | Vector Retriever | Semantic search with `VectorRetriever` and end-to-end question answering with `GraphRAG` |
| [03_vector_cypher_retriever.ipynb](03_vector_cypher_retriever.ipynb) | VectorCypher Retriever | Graph-enriched retrieval that adds companies, products, and risk factors to vector search results |
| [04_strands_graphrag_agent.ipynb](04_strands_graphrag_agent.ipynb) | Strands GraphRAG Agent | A Strands agent that decides which retriever to use based on the question |

## Next Steps

After completing this lab, continue to [Lab 5](../Lab_5_MCP_Server/) to connect agents to Neo4j via MCP, or to [Lab 6](../Lab_6_GraphRAG_Pipeline/) to build the data pipeline from scratch.
