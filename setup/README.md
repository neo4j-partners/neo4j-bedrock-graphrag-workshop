# Financial/SEC Workshop Setup Tools

CLI tools for loading the SEC 10-K financial knowledge graph into Neo4j and validating GraphRAG retrievers against it.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Neo4j Aura instance (from Lab 1)
- AWS credentials configured for Bedrock access (solutions_bedrock only)
- `CONFIG.txt` at the repository root with Neo4j and Bedrock credentials

## Tools

### populate -- Load the Financial Knowledge Graph

Loads structured CSV data from `TransformedData/` into Neo4j as a knowledge graph with companies, products, services, risk factors, financial metrics, executives, asset managers, and SEC filings.

```bash
cd setup/populate
uv run populate-financial-db load        # Full pipeline: constraints, indexes, nodes, relationships, verify
uv run populate-financial-db verify      # Print node and relationship counts
uv run populate-financial-db clean       # Delete all nodes and relationships
uv run populate-financial-db samples     # Run sample Cypher queries
```

### solutions_bedrock -- Validate GraphRAG Retrievers

Runs a 6-phase validation of the Lab 6 GraphRAG pipeline: data loading, embeddings, vector retriever, vector-cypher retriever, fulltext search, and hybrid search.

```bash
cd setup/solutions_bedrock
uv run graphrag-validator test           # Run full 6-phase validation
uv run graphrag-validator chat           # Interactive GraphRAG chat (HybridCypherRetriever)
```

## Configuration

Both tools read credentials from `CONFIG.txt` at the repository root (two levels up from each tool directory). The file uses dotenv format:

```
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
REGION=us-east-1
```

## Graph Schema

```
(:Company) -[:OFFERS_PRODUCT]-> (:Product)
(:Company) -[:OFFERS_SERVICE]-> (:Service)
(:Company) -[:FACES_RISK]-> (:RiskFactor)
(:Company) -[:HAS_METRIC]-> (:FinancialMetric)
(:Company) -[:HAS_EXECUTIVE]-> (:Executive)
(:AssetManager) -[:OWNS]-> (:Company)
(:Company) -[:FILED]-> (:Document) <-[:FROM_DOCUMENT]- (:Chunk) -[:NEXT_CHUNK]-> (:Chunk)
```
