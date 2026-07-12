# Lab 2 - Chunking and Embeddings (Optional)

See how a GraphRAG data pipeline turns raw filing text into a searchable knowledge graph. One notebook walks through chunking, embedding generation, graph construction, and semantic search using SEC 10-K financial filing data.

**This lab is optional.** Lab 1 already loaded the complete knowledge graph, so every downstream lab is ready without it. Lab 2 exists to show *how* that pipeline works.

## What You'll Learn

- **Chunking**: Split filing text into overlapping passages sized for embedding
- **Embeddings**: Generate 1024-dimensional vectors with Amazon Titan Text Embeddings V2
- **Graph pipeline**: Store chunks, embeddings, and their relationships alongside structured Company, Product, and Document entities
- **Vector search**: Create a vector index and run a semantic query with `VectorRetriever`

## Non-Destructive by Design

The notebook builds everything in an isolated sandbox. Every demo node carries a `:Demo` label plus its own `Demo*` label, and the vector index is named `demoChunkEmbeddings`. Nothing touches the `:Company`, `:Chunk`, or `chunkEmbeddings` data that Lab 1 loaded. The final cell tears the sandbox down, so the notebook is safe to run as many times as you like.

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 1** (Neo4j Aura instance created and the knowledge graph loaded)
- Filled in your credentials in `CONFIG.txt` at the project root
- A running environment (SageMaker Studio or GitHub Codespace)

## Notebook

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [01_chunking_and_embeddings.ipynb](01_chunking_and_embeddings.ipynb) | Chunking and Embeddings | A sandboxed `Demo*` subgraph: Company, Product, Document, and Chunk nodes with embeddings, a `demoChunkEmbeddings` vector index, and a semantic search over it |

## Next Steps

After completing this lab, continue to [Lab 3 - Semantic Search and GraphRAG](../Lab_3_GraphRAG_Search) to build vector and graph-enriched retrieval over the full knowledge graph.
