# SEC 10-K Financial Data Architecture

This document describes the graph data model used for the SEC 10-K financial filing workshop. The data is extracted from real SEC 10-K filings by the `financial_data_load/` pipeline using LLM-powered entity extraction, then exported and filtered to the 9 primary filing companies and their directly-connected entities.

## Graph Schema

### Node Types and Properties

| Node Label | Properties | Source File |
|---|---|---|
| **Company** | company_id, name, ticker, cik, cusip | `companies.csv` |
| **Product** | product_id, name, description | `products.csv` |
| **RiskFactor** | risk_id, name, description | `risk_factors.csv` |
| **AssetManager** | manager_id, name | `asset_managers.csv` |

### Relationships

| Relationship | From | To | Properties | Source File |
|---|---|---|---|---|
| `OFFERS` | Company | Product | - | `company_products.csv` |
| `FACES_RISK` | Company | RiskFactor | - | `company_risk_factors.csv` |
| `OWNS` | AssetManager | Company | shares | `asset_manager_companies.csv` |
| `COMPETES_WITH` | Company | Company | - | `company_competitors.csv` |
| `PARTNERS_WITH` | Company | Company | - | `company_partners.csv` |

### Schema Diagram

```
(:AssetManager)  -[:OWNS {shares}]->  (:Company)
(:Company)       -[:OFFERS]->         (:Product)
(:Company)       -[:FACES_RISK]->     (:RiskFactor)
(:Company)       -[:COMPETES_WITH]->  (:Company)
(:Company)       -[:PARTNERS_WITH]->  (:Company)
```

## Filing Companies

The dataset contains 9 companies that filed SEC 10-K reports:

| ID | Name | Ticker | Sector |
|----|------|--------|--------|
| C001 | Amazon.com, Inc. | AMZN | Consumer Discretionary |
| C002 | American International Group, Inc. | AIG | Financial Services |
| C003 | Apple Inc. | AAPL | Technology |
| C004 | Intel Corporation | INTC | Technology |
| C005 | McDonald's Corporation | MCD | Consumer Discretionary |
| C006 | Microsoft Corporation | MSFT | Technology |
| C007 | NVIDIA Corporation | NVDA | Technology |
| C008 | PG&E Corporation | PCG | Utilities |
| C009 | PayPal Holdings, Inc. | PYPL | Financial Services |

## Key Traversal Patterns

### 1. Company to Risk Analysis

Find all risk factors for a given company.

```cypher
MATCH (c:Company {ticker: 'AAPL'})-[:FACES_RISK]->(r:RiskFactor)
RETURN r.name, r.description
```

### 2. Cross-Company Risk Exposure

Identify risk factors shared across multiple companies.

```cypher
MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
WITH r, collect(c.ticker) AS affected_companies, count(c) AS company_count
WHERE company_count > 1
RETURN r.name, affected_companies, company_count
ORDER BY company_count DESC
```

### 3. Asset Manager Portfolio Analysis

Analyze an asset manager's holdings.

```cypher
MATCH (am:AssetManager)-[o:OWNS]->(c:Company)
WHERE am.name CONTAINS 'BlackRock'
RETURN c.name, c.ticker, o.shares
ORDER BY o.shares DESC
```

### 4. Portfolio Risk Aggregation

Determine aggregate risk exposure across an asset manager's portfolio.

```cypher
MATCH (am:AssetManager)-[:OWNS]->(c:Company)-[:FACES_RISK]->(r:RiskFactor)
WITH am, r, count(DISTINCT c) AS companies_exposed
RETURN am.name, r.name, companies_exposed
ORDER BY companies_exposed DESC
```

### 5. Competitive Landscape

Find competitors of a given company.

```cypher
MATCH (c:Company {ticker: 'MSFT'})-[:COMPETES_WITH]->(competitor:Company)
RETURN competitor.name
```

### 6. Partner Network

Explore partnership relationships.

```cypher
MATCH (c:Company {ticker: 'NVDA'})-[:PARTNERS_WITH]->(partner:Company)
RETURN partner.name
```

## Entity Counts

| Entity | Count |
|---|---|
| Company | 76 (9 filing + 67 mentioned) |
| Product | 274 |
| RiskFactor | 203 |
| AssetManager | 15 |
| **Total Nodes** | **~568** |

| Relationship | Count |
|---|---|
| OFFERS | 276 |
| FACES_RISK | 211 |
| OWNS | 103 |
| COMPETES_WITH | 37 |
| PARTNERS_WITH | 36 |
| **Total Relationships** | **~663** |

## Data Provenance

The entity and relationship data was extracted from SEC 10-K filings using the `financial_data_load/` pipeline with `neo4j-graphrag`'s `SimpleKGPipeline`. The pipeline processes PDF filings through LLM-powered extraction, entity resolution, and graph construction. The CSVs in this directory were exported from the resulting graph, filtered to the 9 primary filing companies and their directly-connected entities.

Asset manager holdings come from real SEC 13-F filings (Q3 2023) loaded from `financial_data_load/financial-data/Asset_Manager_Holdings.csv`.
