# Lab 1: Neo4j Aura Setup and Exploration

In this lab, you will set up your Neo4j Aura database through the AWS Marketplace, load a financial knowledge graph using Cypher, and explore your graph visually.

## Prerequisites

- Completed **Lab 0** (AWS sign-in)
- Access to AWS Console
- AWS Marketplace purchasing permissions

## Part 1: Neo4j Aura Signup

Follow the instructions in [Neo4j_Aura_Signup.md](Neo4j_Aura_Signup.md) to:

1. Subscribe to Neo4j Aura through AWS Marketplace
2. Create your Neo4j Aura account
3. Configure and provision your database instance
4. Save your connection credentials

## Part 2: Load the Knowledge Graph

After your Aura instance is running, open **Query** from the left sidebar in the [Aura Console](https://console.neo4j.io) and run the following Cypher statements in order.

### Step 1: Create Constraints

These ensure each node has a unique identifier and speed up MERGE lookups during loading.

```cypher
CREATE CONSTRAINT company_id IF NOT EXISTS
FOR (c:Company) REQUIRE c.companyId IS UNIQUE;

CREATE CONSTRAINT company_name IF NOT EXISTS
FOR (c:Company) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT product_id IF NOT EXISTS
FOR (p:Product) REQUIRE p.productId IS UNIQUE;

CREATE CONSTRAINT risk_id IF NOT EXISTS
FOR (r:RiskFactor) REQUIRE r.riskId IS UNIQUE;

CREATE CONSTRAINT manager_id IF NOT EXISTS
FOR (m:AssetManager) REQUIRE m.managerId IS UNIQUE;
```

### Step 2: Load Nodes

Each statement reads a CSV file from S3 and creates (or updates) the corresponding nodes.

```cypher
// Companies
LOAD CSV WITH HEADERS FROM 'https://dhoj7jltw73ew.cloudfront.net/sec-filings/companies.csv' AS row
MERGE (c:Company {companyId: row.company_id})
SET c.name = row.name, c.ticker = row.ticker,
    c.cik = row.cik, c.cusip = row.cusip;
```

```cypher
// Products
LOAD CSV WITH HEADERS FROM 'https://dhoj7jltw73ew.cloudfront.net/sec-filings/products.csv' AS row
MERGE (p:Product {productId: row.product_id})
SET p.name = row.name, p.description = row.description;
```

```cypher
// Risk Factors
LOAD CSV WITH HEADERS FROM 'https://dhoj7jltw73ew.cloudfront.net/sec-filings/risk_factors.csv' AS row
MERGE (r:RiskFactor {riskId: row.risk_id})
SET r.name = row.name, r.description = row.description;
```

```cypher
// Asset Managers
LOAD CSV WITH HEADERS FROM 'https://dhoj7jltw73ew.cloudfront.net/sec-filings/asset_managers.csv' AS row
MERGE (m:AssetManager {managerId: row.manager_id})
SET m.name = row.name;
```

### Step 3: Load Relationships

These statements read junction CSVs and create relationships between the nodes loaded above.

```cypher
// Company -[:OFFERS]-> Product
LOAD CSV WITH HEADERS FROM 'https://dhoj7jltw73ew.cloudfront.net/sec-filings/company_products.csv' AS row
MATCH (c:Company {companyId: row.company_id})
MATCH (p:Product {productId: row.product_id})
MERGE (c)-[:OFFERS]->(p);
```

```cypher
// Company -[:FACES_RISK]-> RiskFactor
LOAD CSV WITH HEADERS FROM 'https://dhoj7jltw73ew.cloudfront.net/sec-filings/company_risk_factors.csv' AS row
MATCH (c:Company {companyId: row.company_id})
MATCH (r:RiskFactor {riskId: row.risk_id})
MERGE (c)-[:FACES_RISK]->(r);
```

```cypher
// AssetManager -[:OWNS]-> Company
LOAD CSV WITH HEADERS FROM 'https://dhoj7jltw73ew.cloudfront.net/sec-filings/asset_manager_companies.csv' AS row
MATCH (m:AssetManager {managerId: row.manager_id})
MATCH (c:Company {companyId: row.company_id})
MERGE (m)-[:OWNS {shares: toInteger(row.shares)}]->(c);
```

```cypher
// Company -[:COMPETES_WITH]-> Company
LOAD CSV WITH HEADERS FROM 'https://dhoj7jltw73ew.cloudfront.net/sec-filings/company_competitors.csv' AS row
MATCH (a:Company {companyId: row.source_company_id})
MATCH (b:Company {companyId: row.target_company_id})
MERGE (a)-[:COMPETES_WITH]->(b);
```

```cypher
// Company -[:PARTNERS_WITH]-> Company
LOAD CSV WITH HEADERS FROM 'https://dhoj7jltw73ew.cloudfront.net/sec-filings/company_partners.csv' AS row
MATCH (a:Company {companyId: row.source_company_id})
MATCH (b:Company {companyId: row.target_company_id})
MERGE (a)-[:PARTNERS_WITH]->(b);
```

### Step 4: Create Fulltext Index

This enables keyword search across entity names and descriptions.

```cypher
CREATE FULLTEXT INDEX search_entities IF NOT EXISTS
FOR (n:Company|Product|RiskFactor)
ON EACH [n.name, n.description];
```

### Step 5: Verify the Load

Run this query to confirm your node counts:

```cypher
CALL db.labels() YIELD label
CALL db.stats.retrieve("GRAPH COUNTS") YIELD nodeCount
WITH label, nodeCount
MATCH (n) WHERE label IN labels(n)
WITH label, count(n) AS count
RETURN label, count ORDER BY label;
```

You should see approximately:
| Label | Count |
|---|---|
| AssetManager | 15 |
| Company | 9 |
| Product | 274 |
| RiskFactor | 203 |

## Part 3: Explore the Knowledge Graph

Follow [EXPLORE.md](EXPLORE.md) to:

1. Use Neo4j Explore to visually navigate your graph
2. Search for patterns between asset managers, companies, and risk factors
3. Apply graph algorithms like Degree Centrality
4. Identify key entities through visual analysis

## Next Steps

After completing this lab, continue to [Lab 2 - Aura Agents](../Lab_2_Aura_Agents) to build an AI-powered agent using the Neo4j Aura Agent no-code platform.
