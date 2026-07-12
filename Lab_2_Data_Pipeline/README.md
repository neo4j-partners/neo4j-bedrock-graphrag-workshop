# Lab 2 - Building a GraphRAG Data Pipeline

Build a GraphRAG data pipeline from scratch using SEC 10-K financial filing data. Two notebooks progress from loading raw data into a knowledge graph to generating the embeddings and vector index that power semantic search.

## What You'll Learn

- **Data Loading**: Build a two-layer knowledge graph — structured entities (Company, Product, RiskFactor) and unstructured document chunks — connected by cross-links
- **Embeddings**: Generate vector embeddings with Amazon Titan Text Embeddings V2 and create a vector index for semantic search

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 1** (Neo4j Aura instance created and running)
- Filled in your credentials in `CONFIG.txt` at the project root
- A running environment (SageMaker Studio or GitHub Codespace)

**Note:** This lab wipes and rebuilds the graph from scratch using `financial_data.json`. It does not depend on data from previous labs.

## Notebooks

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [01_data_loading.ipynb](01_data_loading.ipynb) | Data Loading | Company, Product, RiskFactor, Document, and Chunk nodes linked by `OFFERS`, `FACES_RISK`, `FILED`, `FROM_DOCUMENT`, `NEXT_CHUNK`, and `FROM_CHUNK` relationships |
| [02_embeddings.ipynb](02_embeddings.ipynb) | Embeddings | Vector embeddings on every Chunk node, plus a `chunkEmbeddings` vector index |

## Next Steps

After completing this lab, continue to [Lab 3 - Semantic Search and GraphRAG](../Lab_3_GraphRAG_Search) to build vector and graph-enriched retrieval over the knowledge graph.
