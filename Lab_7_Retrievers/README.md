# Lab 7 - GraphRAG Retrievers

In this lab, you will implement different retrieval patterns using the neo4j-graphrag library and Amazon Bedrock.

## Prerequisites

Before starting, make sure you have:
- Completed **Lab 5** (Codespace setup with AWS credentials configured)
- Completed **Lab 6** (Knowledge Graph with full dataset loaded)
- Your `.env` file configured with Neo4j and AWS credentials

## What You'll Learn

1. **Vector Retriever** - Basic semantic search over text chunks
2. **VectorCypher Retriever** - Combine vector search with graph traversal
3. **Text2Cypher Retriever** - Natural language to Cypher query generation

## Notebooks

| Notebook | Description |
|----------|-------------|
| [01_vector_retriever.ipynb](01_vector_retriever.ipynb) | Basic vector similarity search |
| [02_vector_cypher_retriever.ipynb](02_vector_cypher_retriever.ipynb) | Enhanced retrieval with graph context |
| [03_text2cypher_retriever.ipynb](03_text2cypher_retriever.ipynb) | Natural language to Cypher conversion |

## Key Concepts

### Retriever Patterns

| Pattern | Best For | How It Works |
|---------|----------|--------------|
| **Vector** | Semantic similarity | Finds chunks with similar meaning to query |
| **VectorCypher** | Contextual answers | Vector search + graph traversal for rich context |
| **Text2Cypher** | Specific facts | LLM converts question to Cypher query |

### When to Use Each Pattern

**Vector Retriever:**
- "What are the main products mentioned?"
- "Tell me about risk factors"
- General semantic queries

**VectorCypher Retriever:**
- "What risks does Apple face and who else faces them?"
- "Which asset managers own companies mentioning AI?"
- Queries needing relationship context

**Text2Cypher Retriever:**
- "Which companies are owned by BlackRock?"
- "How many risk factors does Microsoft have?"
- Queries about specific entities or counts

### GraphRAG Pipeline

The `GraphRAG` class combines a retriever with an LLM:

```python
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.retrievers import VectorRetriever

retriever = VectorRetriever(
    driver=driver,
    index_name='chunkEmbeddings',
    embedder=embedder
)

rag = GraphRAG(llm=llm, retriever=retriever)
response = rag.search("What products does Apple make?")
```

## Best Practices

### Vector Retriever Tips
- Use `top_k` to control how many chunks to retrieve (5-10 is typical)
- Enable `return_context=True` to inspect retrieved chunks
- Adjust chunk size in Lab 6 if results are too granular or too broad

### VectorCypher Tips
- Start with the semantic anchor (`node`) then traverse relationships
- Use `COLLECT{}` subqueries to limit nested results
- Apply slice notation `[0..10]` on collected arrays

### Text2Cypher Tips
- Provide a custom prompt with modern Cypher requirements
- Use `elementId(node)` instead of deprecated `id(node)`
- Include `LIMIT` in generated queries to control result size
- Consider adding few-shot examples for better query generation

## Common Issues

| Problem | Solution |
|---------|----------|
| Empty vector search results | Check that embeddings index exists: `SHOW INDEXES` |
| VectorCypher returns too many rows | Add `LIMIT` and use `COLLECT{}` subqueries |
| Text2Cypher generates invalid Cypher | Customize the prompt with schema and modern syntax rules |
| LLM response doesn't use context | Increase `top_k` or check retriever is returning relevant chunks |

## Next Steps

After completing this lab, continue to [Lab 8 - GraphRAG Agents](../Lab_8_Agents/) to build agents that can select and combine these retrieval patterns.
