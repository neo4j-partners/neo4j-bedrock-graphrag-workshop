# Lab 9 - Hybrid Search (Optional)

This optional lab demonstrates how to combine vector and fulltext search for improved retrieval accuracy.

## Prerequisites

Before starting, make sure you have:
- Completed **Lab 5** (Codespace setup)
- Completed **Lab 6** (Knowledge Graph with full dataset loaded)
- Your `.env` file configured with Neo4j and AWS credentials

## What You'll Learn

1. **Fulltext Search** - Keyword-based search with fuzzy matching and boolean operators
2. **Hybrid Search** - Combining vector and fulltext search for better results

## Notebooks

| Notebook | Description |
|----------|-------------|
| [01_fulltext_search.ipynb](01_fulltext_search.ipynb) | Neo4j fulltext indexes and search patterns |
| [02_hybrid_search.ipynb](02_hybrid_search.ipynb) | HybridRetriever and HybridCypherRetriever |

## Key Concepts

### Why Hybrid Search?

| Search Type | Strengths | Weaknesses |
|-------------|-----------|------------|
| **Vector** | Semantic similarity, concept matching | Misses exact terms, names, dates |
| **Fulltext** | Exact keyword matching, specific terms | No semantic understanding |
| **Hybrid** | Combines both for better precision and recall | Slightly more complex |

### Fulltext Search Syntax

| Feature | Syntax | Example |
|---------|--------|---------|
| Basic search | `term` | `Apple` |
| Fuzzy search | `term~` | `Aplle~` |
| Wildcard | `term*` | `Micro*` |
| Boolean AND | `term1 AND term2` | `supply AND chain` |
| Boolean OR | `term1 OR term2` | `Apple OR Microsoft` |
| Boolean NOT | `term1 NOT term2` | `risk NOT financial` |
| Phrase | `"term1 term2"` | `"supply chain"` |

### The Alpha Parameter

Hybrid search uses an `alpha` parameter to balance vector and fulltext scores:

```
combined_score = alpha * vector_score + (1 - alpha) * fulltext_score
```

| Alpha | Effect |
|-------|--------|
| 1.0 | Pure vector (semantic) search |
| 0.7 | Favor vector, some fulltext |
| 0.5 | Equal weight (good starting point) |
| 0.3 | Favor fulltext, some vector |
| 0.0 | Pure fulltext (keyword) search |

### Retriever Classes

```python
from neo4j_graphrag.retrievers import HybridRetriever, HybridCypherRetriever

# Basic hybrid search
retriever = HybridRetriever(
    driver=driver,
    vector_index_name="chunkEmbeddings",
    fulltext_index_name="search_chunks",
    embedder=embedder,
)

# Hybrid search with graph traversal
cypher_retriever = HybridCypherRetriever(
    driver=driver,
    vector_index_name="chunkEmbeddings",
    fulltext_index_name="search_chunks",
    embedder=embedder,
    retrieval_query="MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)..."
)
```

## When to Use Each Approach

| Query Type | Recommended Approach |
|------------|---------------------|
| Natural language questions | Vector or Hybrid (high alpha) |
| Specific entity names | Fulltext or Hybrid (low alpha) |
| Concepts + specific names | Hybrid (balanced alpha) |
| Exact term matching | Fulltext only |

## Common Issues

| Problem | Solution |
|---------|----------|
| Fulltext index not found | Check index exists with `SHOW FULLTEXT INDEXES` |
| No results from hybrid | Verify both indexes are ONLINE |
| Wrong results ranking | Adjust alpha parameter |
| Missing exact matches | Lower alpha toward 0.0 |

## References

- [Neo4j GraphRAG Python Documentation](https://neo4j.com/docs/neo4j-graphrag-python/current/)
- [Neo4j Fulltext Indexes](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/full-text-indexes/)
- [Hybrid Retrieval Blog](https://neo4j.com/blog/developer/hybrid-retrieval-graphrag-python-package/)
