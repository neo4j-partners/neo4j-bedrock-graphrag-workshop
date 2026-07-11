# SEC 10-K Financial Data Architecture

This document describes the graph data model used for the SEC 10-K financial filing workshop. The data is extracted from real SEC 10-K filings by the `financial_data_load/` pipeline using LLM-powered entity extraction, then exported and filtered to the 6 primary filing companies and their directly-connected entities.

## Graph Schema

The graph has two layers connected by cross-link relationships:

- **Structured layer** — Company, Product, RiskFactor, AssetManager nodes loaded from CSV seed data
- **Unstructured layer** — Document and Chunk nodes created by the SimpleKGPipeline from PDF filings

The `FILED` relationship bridges these layers, connecting each Company to the Documents it filed.

### Node Types and Properties

| Node Label | Properties | Source |
|---|---|---|
| **Company** | name, ticker, cik, cusip | CSV seed data + LLM extraction |
| **Product** | name, description | CSV seed data + LLM extraction |
| **RiskFactor** | name, description | CSV seed data + LLM extraction |
| **Executive** | name, title | LLM extraction |
| **FinancialMetric** | name, value, period | LLM extraction |
| **AssetManager** | managerName, aum_billions | CSV seed data |
| **Document** | name, path, filing_type, filing_date | SimpleKGPipeline (PDF processing) |
| **Chunk** | text, index, embedding | SimpleKGPipeline (PDF chunking) |

### Relationships

| Relationship | From | To | Description |
|---|---|---|---|
| `FILED` | Company | Document | Company filed this SEC document (cross-link) |
| `FROM_DOCUMENT` | Chunk | Document | Chunk was split from this document |
| `NEXT_CHUNK` | Chunk | Chunk | Sequential reading order within a document |
| `FROM_CHUNK` | Entity | Chunk | Entity was extracted from this chunk (provenance) |
| `OFFERS` | Company | Product | Company offers this product/service |
| `FACES_RISK` | Company | RiskFactor | Company faces this risk factor |
| `HAS_EXECUTIVE` | Company | Executive | Company has this executive |
| `REPORTS` | Company | FinancialMetric | Company reports this metric |
| `COMPETES_WITH` | Company | Company | Competitive relationship |
| `OWNS` | AssetManager | Company | Asset manager holds shares |

### Schema Diagram

```
                                    Structured Layer
                                    ================

(:AssetManager)  -[:OWNS]->         (:Company)
(:Company)       -[:OFFERS]->       (:Product)
(:Company)       -[:FACES_RISK]->   (:RiskFactor)
(:Company)       -[:HAS_EXECUTIVE]->(:Executive)
(:Company)       -[:REPORTS]->      (:FinancialMetric)
(:Company)       -[:COMPETES_WITH]->(:Company)

                              Cross-Link (FILED)
                              ==================

(:Company)       -[:FILED]->        (:Document)

                                   Unstructured Layer
                                   ==================

(:Chunk)         -[:FROM_DOCUMENT]->(:Document)
(:Chunk)         -[:NEXT_CHUNK]->   (:Chunk)
(:Entity)        -[:FROM_CHUNK]->   (:Chunk)         (extraction provenance)
```

### Key Traversal Path: Chunk to Company

The primary path from unstructured text to structured entities:

```
(:Chunk)-[:FROM_DOCUMENT]->(:Document)<-[:FILED]-(:Company)
```

This deterministic path connects every chunk to the company that filed its source document. It replaces the less reliable `FROM_CHUNK` path, which only exists when the LLM happened to extract a Company entity from a specific chunk.

## Filing Companies

The dataset contains 6 companies that filed SEC 10-K reports:

| ID | Name | Ticker | Sector |
|----|------|--------|--------|
| C001 | Amazon.com, Inc. | AMZN | Consumer Discretionary |
| C002 | Apple Inc. | AAPL | Technology |
| C003 | Microsoft Corporation | MSFT | Technology |
| C004 | NVIDIA Corporation | NVDA | Technology |
| C005 | PG&E Corporation | PCG | Utilities |
| C006 | PayPal Holdings, Inc. | PYPL | Financial Services |

## Key Traversal Patterns

### 1. Graph-Enriched Retrieval (Chunk → Company)

The primary GraphRAG pattern: find similar chunks via vector search, then traverse to the filing company.

```cypher
CALL db.index.vector.queryNodes('chunkEmbeddings', 5, $embedding)
YIELD node, score
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)<-[:FILED]-(company:Company)
OPTIONAL MATCH (company)-[:FACES_RISK]->(risk:RiskFactor)
RETURN node.text AS text, score, company.name AS company,
       collect(DISTINCT risk.name)[0..5] AS risks
```

### 2. Company to Risk Analysis

Find all risk factors for a given company.

```cypher
MATCH (c:Company {ticker: 'AAPL'})-[:FACES_RISK]->(r:RiskFactor)
RETURN r.name, r.description
```

### 3. Cross-Company Risk Exposure

Identify risk factors shared across multiple companies.

```cypher
MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
WITH r, collect(c.ticker) AS affected_companies, count(c) AS company_count
WHERE company_count > 1
RETURN r.name, affected_companies, company_count
ORDER BY company_count DESC
```

### 4. Asset Manager Portfolio Analysis

Analyze an asset manager's holdings.

```cypher
MATCH (am:AssetManager)-[o:OWNS]->(c:Company)
WHERE am.managerName CONTAINS 'BlackRock'
RETURN c.name, c.ticker, o.shares
ORDER BY o.shares DESC
```

### 5. Portfolio Risk Aggregation

Determine aggregate risk exposure across an asset manager's portfolio.

```cypher
MATCH (am:AssetManager)-[:OWNS]->(c:Company)-[:FACES_RISK]->(r:RiskFactor)
WITH am, r, count(DISTINCT c) AS companies_exposed
RETURN am.managerName, r.name, companies_exposed
ORDER BY companies_exposed DESC
```

### 6. Competitive Landscape

Find competitors of a given company.

```cypher
MATCH (c:Company {ticker: 'MSFT'})-[:COMPETES_WITH]->(competitor:Company)
RETURN competitor.name
```

### 7. Document-Chunk Provenance

Trace from a company to its filing documents and chunks.

```cypher
MATCH (c:Company {ticker: 'AAPL'})-[:FILED]->(d:Document)<-[:FROM_DOCUMENT]-(chunk:Chunk)
RETURN d.path AS document, chunk.index AS chunk_index,
       left(chunk.text, 100) AS preview
ORDER BY chunk.index
```

## Data Provenance

The entity and relationship data was extracted from SEC 10-K filings using the `financial_data_load/` pipeline with `neo4j-graphrag`'s `SimpleKGPipeline`. The pipeline processes PDF filings through LLM-powered extraction, entity resolution, and graph construction. The CSVs in this directory were exported from the resulting graph, filtered to the 6 primary filing companies and their directly-connected entities.

The `FILED` relationship is created by the `link_to_existing_graph()` function in `financial_data_load/src/loader.py`, which matches Company nodes to Document nodes by normalized company name (with CIK fallback).

Asset manager holdings come from real SEC 13-F filings (Q3 2023) loaded from `financial_data_load/financial-data/Asset_Manager_Holdings.csv`.
