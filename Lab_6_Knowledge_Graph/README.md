# Lab 6 - Building a Knowledge Graph

In this lab, you will build a knowledge graph from SEC 10-K filings using Amazon Bedrock for embeddings and entity extraction.

## Prerequisites

Before starting, make sure you have:
- Completed **Lab 5** (Codespace setup with AWS credentials configured)
- Your `.env` file configured with Neo4j and AWS credentials

## What You'll Learn

1. **Data Loading** - Load SEC 10-K filing documents into Neo4j
2. **Embeddings** - Generate vector embeddings using Amazon Titan Text Embeddings V2
3. **Entity Extraction** - Extract entities (companies, products, risks) using Claude
4. **Full Pipeline** - Process the complete dataset

## Notebooks

| Notebook | Description |
|----------|-------------|
| [01_data_loading.ipynb](01_data_loading.ipynb) | Load sample SEC filing data into Neo4j |
| [02_embeddings.ipynb](02_embeddings.ipynb) | Generate embeddings with Amazon Titan |
| [03_entity_extraction.ipynb](03_entity_extraction.ipynb) | Extract entities using Claude |
| [04_full_dataset.ipynb](04_full_dataset.ipynb) | Process the complete SEC filings dataset |

## Key Concepts

### Embeddings with Amazon Titan

Amazon Titan Text Embeddings V2 produces vectors with configurable dimensions:
- **1024 dimensions** (default) - Best quality
- **512 dimensions** - Balanced
- **256 dimensions** - Most efficient

```python
from config import get_embedder

embedder = get_embedder(dimensions=1024)
embedding = embedder.embed_query("Apple Inc. designs smartphones...")
# Returns a list of 1024 floating-point numbers
```

### Entity Extraction with Claude

Claude excels at extracting structured information from text:

```python
from config import get_llm

llm = get_llm()
response = llm.invoke("""
Extract company names from this text:
Apple Inc. reported strong sales while Microsoft Corp announced...
""")
```

### Graph Data Model

The knowledge graph uses this schema:

```
(:Document {path, name})
    ↑
    [:FROM_DOCUMENT]
    |
(:Chunk {text, embedding, index})
    ↑
    [:FROM_CHUNK]
    |
(:Company {name, ticker})
    |
    [:FACES_RISK]→(:RiskFactor {name})
    [:MENTIONS]→(:Product {name})
    [:HAS_METRIC]→(:FinancialMetric {name})
```

## Best Practices

### Titan Embeddings Best Practices

From [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html):

- **Segment documents** into paragraphs or logical chunks before embedding
- **Use normalization** (`normalize=True`) for cosine similarity searches
- **Max input**: 8,192 tokens per request
- **Batch processing**: Consider Bedrock batch inference for large datasets

### Vector Index Configuration

When creating vector indexes in Neo4j:

```python
create_vector_index(
    driver=driver,
    name="chunkEmbeddings",
    label="Chunk",
    embedding_property="embedding",
    dimensions=1024,  # Match Titan output
    similarity_fn="cosine"
)
```

## Next Steps

After completing this lab, continue to [Lab 7 - GraphRAG Retrievers](../Lab_7_Retrievers/) to implement different retrieval patterns.
