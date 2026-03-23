# Lab 6 - Consolidated GraphRAG

Build a complete GraphRAG pipeline over SEC 10-K financial filing data using Neo4j and Amazon Bedrock. This lab walks through six notebooks that progress from loading raw text into a knowledge graph to running hybrid retrieval queries that combine vector similarity, keyword matching, and graph traversal.

The six notebooks form a single arc: create the graph, generate embeddings, then layer increasingly sophisticated retrieval strategies on top. By the end, you will have built four different retriever configurations and understand when each one applies.

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

## How the Notebooks Connect

Notebooks 01 and 02 build the foundation: a graph of Document and Chunk nodes with vector embeddings and a searchable index. Every notebook from 03 onward queries that same graph using different retrieval strategies.

Notebook 03 introduces the simplest retriever (pure vector similarity). Notebook 04 adds graph traversal to pull in surrounding context. Notebook 05 steps back from vectors entirely to show keyword-based fulltext search. Notebook 06 combines both approaches and shows how the alpha parameter controls the balance.

## Retriever Selection Guide

Each retriever fits a different query shape. The right choice depends on whether the query contains specific terms, needs graph context, or is purely semantic.

| Scenario | Retriever | Why |
|----------|-----------|-----|
| Simple semantic Q&A ("What are the main risk factors?") | `VectorRetriever` | Finds chunks by meaning without requiring exact keyword matches |
| Need company or filing context ("What risks does Apple face and what document are they from?") | `VectorCypherRetriever` | Traverses from matched chunks to related Document nodes, neighboring chunks, and entity relationships |
| Specific terms, tickers, or CIK numbers ("AAPL", "CIK 0000320193") | `HybridRetriever` | Fulltext component catches exact terms that vector search may rank lower |
| Best of all approaches | `HybridCypherRetriever` | Combines vector similarity, keyword matching, and graph traversal in a single query |

## Next Steps

After completing this lab, continue to [Lab 7](../Lab_7_Neo4j_MCP_Agent/) to build MCP agents that use these retrieval patterns as tools.
