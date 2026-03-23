# Proposal: Unified CSV Data and S3-Based Loading for Labs 1 and 2

## The Problem

The repository has two disconnected data sources that produce incompatible graphs:

1. **`TransformedData/`** — Hand-curated CSVs with 5 tech companies, synthetic asset managers, and a schema (`OFFERS_PRODUCT`, `OFFERS_SERVICE`, `HAS_METRIC`) that no lab notebook actually hardcodes.
2. **`financial_data_load/`** — A real pipeline that processes SEC 10-K PDFs via LLM extraction and produces a different schema (`OFFERS`, `REPORTS`, `COMPETES_WITH`, `PARTNERS_WITH`). The gold database (`.env.gold`) contains the authoritative output.

Lab 1 restores a 50MB+ backup containing everything (entities, chunks, embeddings) when participants only need the structured entity layer. The backup is opaque: participants don't see how the graph was built. Lab 2's Aura Agent auto-discovers the schema, so it works against either, but the documentation references the wrong relationship types.

The proposal has two phases: first, extract real data from the gold database into CSVs that match the pipeline's actual schema. Second, host those CSVs on S3 and load them via `LOAD CSV` in Lab 1, replacing the backup restore.

## Phase 1: Extract Gold Database to CSVs

### Schema Alignment

The CSVs adopt the pipeline's schema directly. This eliminates the disconnect between what the pipeline produces and what the CSVs contain.

| Old CSV schema | Pipeline schema (adopted) | Change |
|---|---|---|
| `OFFERS_PRODUCT` | `OFFERS` | Products and services merge into `Product` with a single `OFFERS` relationship |
| `OFFERS_SERVICE` + `Service` node | `OFFERS` + `Product` node | `Service` node type removed; services become Products |
| `HAS_METRIC` | `REPORTS` | Renamed |
| (not present) | `COMPETES_WITH` | Added — Company-to-Company competitive relationships |
| (not present) | `PARTNERS_WITH` | Added — Company-to-Company partnership relationships |
| `FACES_RISK` | `FACES_RISK` | No change |
| `HAS_EXECUTIVE` | `HAS_EXECUTIVE` | No change |
| `OWNS` | `OWNS` | No change |

### Export Script

A Python script connects to the gold database using `.env.gold` credentials and exports each entity type and relationship to CSV. The script lives at `TransformedData/export_from_neo4j.py`.

```python
"""Export the gold Neo4j database to TransformedData/ CSVs."""

import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

EXPORT_DIR = Path(__file__).parent

# Load gold credentials
load_dotenv(Path(__file__).parent.parent / "financial_data_load" / ".env.gold")

URI = os.environ["NEO4J_URI"]
USER = os.environ["NEO4J_USERNAME"]
PASSWORD = os.environ["NEO4J_PASSWORD"]


def write_csv(filename: str, headers: list[str], rows: list[dict]):
    path = EXPORT_DIR / filename
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {filename}: {len(rows)} rows")


def export(driver):
    with driver.session() as session:

        # -- Companies --
        result = session.run("""
            MATCH (c:Company)
            WHERE c.name IS NOT NULL
            RETURN c.name AS name, c.ticker AS ticker,
                   c.cik AS cik, c.cusip AS cusip
            ORDER BY c.name
        """)
        companies = [dict(r) for r in result]
        # Assign stable IDs
        company_id_map = {}
        for i, c in enumerate(companies, 1):
            cid = f"C{i:03d}"
            company_id_map[c["name"]] = cid
            c["company_id"] = cid
        write_csv("companies.csv",
                   ["company_id", "name", "ticker", "cik", "cusip"],
                   companies)

        # -- Products (includes former Services) --
        result = session.run("""
            MATCH (p:Product)
            WHERE p.name IS NOT NULL
            RETURN p.name AS name,
                   coalesce(p.description, '') AS description
            ORDER BY p.name
        """)
        products = [dict(r) for r in result]
        product_id_map = {}
        for i, p in enumerate(products, 1):
            pid = f"P{i:03d}"
            product_id_map[p["name"]] = pid
            p["product_id"] = pid
        write_csv("products.csv",
                   ["product_id", "name", "description"],
                   products)

        # -- Risk Factors --
        result = session.run("""
            MATCH (r:RiskFactor)
            WHERE r.name IS NOT NULL
            RETURN r.name AS name,
                   coalesce(r.description, '') AS description
            ORDER BY r.name
        """)
        risks = [dict(r) for r in result]
        risk_id_map = {}
        for i, r in enumerate(risks, 1):
            rid = f"R{i:03d}"
            risk_id_map[r["name"]] = rid
            r["risk_id"] = rid
        write_csv("risk_factors.csv",
                   ["risk_id", "name", "description"],
                   risks)

        # -- Executives --
        result = session.run("""
            MATCH (c:Company)-[:HAS_EXECUTIVE]->(e:Executive)
            WHERE e.name IS NOT NULL
            RETURN e.name AS name,
                   coalesce(e.title, '') AS title,
                   c.name AS company_name
            ORDER BY c.name, e.name
        """)
        executives = [dict(r) for r in result]
        exec_id_map = {}
        for i, e in enumerate(executives, 1):
            eid = f"E{i:03d}"
            exec_id_map[e["name"]] = eid
            e["executive_id"] = eid
            e["company_id"] = company_id_map.get(e["company_name"], "")
        write_csv("executives.csv",
                   ["executive_id", "name", "title", "company_id"],
                   [{k: v for k, v in e.items() if k != "company_name"}
                    for e in executives])

        # -- Financial Metrics --
        result = session.run("""
            MATCH (c:Company)-[:REPORTS]->(m:FinancialMetric)
            WHERE m.name IS NOT NULL
            RETURN m.name AS metric_name,
                   coalesce(m.value, '') AS value,
                   coalesce(m.period, '') AS period,
                   c.name AS company_name
            ORDER BY c.name, m.name
        """)
        metrics = [dict(r) for r in result]
        for i, m in enumerate(metrics, 1):
            m["metric_id"] = f"FM{i:03d}"
            m["company_id"] = company_id_map.get(m["company_name"], "")
        write_csv("financial_metrics.csv",
                   ["metric_id", "company_id", "metric_name", "value", "period"],
                   [{k: v for k, v in m.items() if k != "company_name"}
                    for m in metrics])

        # -- Asset Managers --
        result = session.run("""
            MATCH (a:AssetManager)
            WHERE a.managerName IS NOT NULL
            RETURN a.managerName AS name
            ORDER BY a.managerName
        """)
        managers = [dict(r) for r in result]
        manager_id_map = {}
        for i, m in enumerate(managers, 1):
            mid = f"AM{i:03d}"
            manager_id_map[m["name"]] = mid
            m["manager_id"] = mid
        write_csv("asset_managers.csv",
                   ["manager_id", "name"],
                   managers)

        # -- Junction: Company -> Product (OFFERS) --
        result = session.run("""
            MATCH (c:Company)-[:OFFERS]->(p:Product)
            RETURN c.name AS company_name, p.name AS product_name
            ORDER BY c.name, p.name
        """)
        rows = []
        for r in result:
            cid = company_id_map.get(r["company_name"])
            pid = product_id_map.get(r["product_name"])
            if cid and pid:
                rows.append({"company_id": cid, "product_id": pid})
        write_csv("company_products.csv",
                   ["company_id", "product_id"], rows)

        # -- Junction: Company -> RiskFactor (FACES_RISK) --
        result = session.run("""
            MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
            RETURN c.name AS company_name, r.name AS risk_name
            ORDER BY c.name, r.name
        """)
        rows = []
        for r in result:
            cid = company_id_map.get(r["company_name"])
            rid = risk_id_map.get(r["risk_name"])
            if cid and rid:
                rows.append({"company_id": cid, "risk_id": rid})
        write_csv("company_risk_factors.csv",
                   ["company_id", "risk_id"], rows)

        # -- Junction: AssetManager -> Company (OWNS) --
        result = session.run("""
            MATCH (a:AssetManager)-[r:OWNS]->(c:Company)
            RETURN a.managerName AS manager_name, c.name AS company_name,
                   r.shares AS shares
            ORDER BY a.managerName, c.name
        """)
        rows = []
        for r in result:
            mid = manager_id_map.get(r["manager_name"])
            cid = company_id_map.get(r["company_name"])
            if mid and cid:
                rows.append({
                    "manager_id": mid, "company_id": cid,
                    "shares": r["shares"]
                })
        write_csv("asset_manager_companies.csv",
                   ["manager_id", "company_id", "shares"], rows)

        # -- Junction: Company -> Company (COMPETES_WITH) --
        result = session.run("""
            MATCH (a:Company)-[:COMPETES_WITH]->(b:Company)
            RETURN a.name AS source, b.name AS target
            ORDER BY a.name, b.name
        """)
        rows = []
        for r in result:
            sid = company_id_map.get(r["source"])
            tid = company_id_map.get(r["target"])
            if sid and tid:
                rows.append({"source_company_id": sid, "target_company_id": tid})
        write_csv("company_competitors.csv",
                   ["source_company_id", "target_company_id"], rows)

        # -- Junction: Company -> Company (PARTNERS_WITH) --
        result = session.run("""
            MATCH (a:Company)-[:PARTNERS_WITH]->(b:Company)
            RETURN a.name AS source, b.name AS target
            ORDER BY a.name, b.name
        """)
        rows = []
        for r in result:
            sid = company_id_map.get(r["source"])
            tid = company_id_map.get(r["target"])
            if sid and tid:
                rows.append({"source_company_id": sid, "target_company_id": tid})
        write_csv("company_partners.csv",
                   ["source_company_id", "target_company_id"], rows)


if __name__ == "__main__":
    print("Connecting to gold database...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
    print("Exporting to CSVs...")
    export(driver)
    driver.close()
    print("Done.")
```

### CSV Files Produced

After running the export, `TransformedData/` contains:

| File | Content |
|------|---------|
| `companies.csv` | company_id, name, ticker, cik, cusip |
| `products.csv` | product_id, name, description (includes former services) |
| `risk_factors.csv` | risk_id, name, description |
| `executives.csv` | executive_id, name, title, company_id |
| `financial_metrics.csv` | metric_id, company_id, metric_name, value, period |
| `asset_managers.csv` | manager_id, name |
| `company_products.csv` | company_id, product_id (junction for OFFERS) |
| `company_risk_factors.csv` | company_id, risk_id (junction for FACES_RISK) |
| `asset_manager_companies.csv` | manager_id, company_id, shares (junction for OWNS) |
| `company_competitors.csv` | source_company_id, target_company_id (junction for COMPETES_WITH) |
| `company_partners.csv` | source_company_id, target_company_id (junction for PARTNERS_WITH) |

### Files Removed

These files from the old schema no longer apply:

- `services.csv` — Services are now Products
- `company_services.csv` — Replaced by `company_products.csv` with OFFERS
- `sec_filings.csv` — Document/filing metadata not needed for Labs 1-2

## Phase 2: S3-Based Loading for Lab 1

### Graph Schema

Aligned to the `financial_data_load/` pipeline schema:

```
(:Company)       -[:OFFERS]->         (:Product)
(:Company)       -[:FACES_RISK]->     (:RiskFactor)
(:Company)       -[:HAS_EXECUTIVE]->  (:Executive)
(:Company)       -[:REPORTS]->        (:FinancialMetric)
(:Company)       -[:COMPETES_WITH]->  (:Company)
(:Company)       -[:PARTNERS_WITH]->  (:Company)
(:AssetManager)  -[:OWNS {shares}]->  (:Company)
```

No Document or Chunk nodes. No embeddings. No vector index. No Service node type.

### S3 Bucket Structure

```
s3://neo4j-workshop-data/sec-filings/
  companies.csv
  products.csv
  risk_factors.csv
  executives.csv
  financial_metrics.csv
  asset_managers.csv
  company_products.csv
  company_risk_factors.csv
  asset_manager_companies.csv
  company_competitors.csv
  company_partners.csv
```

### Cypher Load Statements

#### Step 1: Constraints

```cypher
CREATE CONSTRAINT company_id IF NOT EXISTS
FOR (c:Company) REQUIRE c.companyId IS UNIQUE;

CREATE CONSTRAINT company_name IF NOT EXISTS
FOR (c:Company) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT product_id IF NOT EXISTS
FOR (p:Product) REQUIRE p.productId IS UNIQUE;

CREATE CONSTRAINT risk_id IF NOT EXISTS
FOR (r:RiskFactor) REQUIRE r.riskId IS UNIQUE;

CREATE CONSTRAINT exec_id IF NOT EXISTS
FOR (e:Executive) REQUIRE e.executiveId IS UNIQUE;

CREATE CONSTRAINT manager_id IF NOT EXISTS
FOR (m:AssetManager) REQUIRE m.managerId IS UNIQUE;

CREATE CONSTRAINT metric_id IF NOT EXISTS
FOR (f:FinancialMetric) REQUIRE f.metricId IS UNIQUE;
```

#### Step 2: Load Nodes

```cypher
// Companies
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/companies.csv' AS row
MERGE (c:Company {companyId: row.company_id})
SET c.name = row.name, c.ticker = row.ticker,
    c.cik = row.cik, c.cusip = row.cusip;

// Products (includes former services)
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/products.csv' AS row
MERGE (p:Product {productId: row.product_id})
SET p.name = row.name, p.description = row.description;

// Risk Factors
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/risk_factors.csv' AS row
MERGE (r:RiskFactor {riskId: row.risk_id})
SET r.name = row.name, r.description = row.description;

// Executives
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/executives.csv' AS row
MERGE (e:Executive {executiveId: row.executive_id})
SET e.name = row.name, e.title = row.title;

// Asset Managers
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/asset_managers.csv' AS row
MERGE (m:AssetManager {managerId: row.manager_id})
SET m.name = row.name;

// Financial Metrics
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/financial_metrics.csv' AS row
MERGE (f:FinancialMetric {metricId: row.metric_id})
SET f.metricName = row.metric_name, f.value = row.value,
    f.period = row.period;
```

#### Step 3: Load Relationships

```cypher
// Company -[:OFFERS]-> Product
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/company_products.csv' AS row
MATCH (c:Company {companyId: row.company_id})
MATCH (p:Product {productId: row.product_id})
MERGE (c)-[:OFFERS]->(p);

// Company -[:FACES_RISK]-> RiskFactor
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/company_risk_factors.csv' AS row
MATCH (c:Company {companyId: row.company_id})
MATCH (r:RiskFactor {riskId: row.risk_id})
MERGE (c)-[:FACES_RISK]->(r);

// Company -[:HAS_EXECUTIVE]-> Executive
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/executives.csv' AS row
MATCH (c:Company {companyId: row.company_id})
MATCH (e:Executive {executiveId: row.executive_id})
MERGE (c)-[:HAS_EXECUTIVE]->(e);

// Company -[:REPORTS]-> FinancialMetric
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/financial_metrics.csv' AS row
MATCH (c:Company {companyId: row.company_id})
MATCH (f:FinancialMetric {metricId: row.metric_id})
MERGE (c)-[:REPORTS]->(f);

// AssetManager -[:OWNS]-> Company
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/asset_manager_companies.csv' AS row
MATCH (m:AssetManager {managerId: row.manager_id})
MATCH (c:Company {companyId: row.company_id})
MERGE (m)-[:OWNS {shares: toInteger(row.shares)}]->(c);

// Company -[:COMPETES_WITH]-> Company
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/company_competitors.csv' AS row
MATCH (a:Company {companyId: row.source_company_id})
MATCH (b:Company {companyId: row.target_company_id})
MERGE (a)-[:COMPETES_WITH]->(b);

// Company -[:PARTNERS_WITH]-> Company
LOAD CSV WITH HEADERS FROM 'https://neo4j-workshop-data.s3.amazonaws.com/sec-filings/company_partners.csv' AS row
MATCH (a:Company {companyId: row.source_company_id})
MATCH (b:Company {companyId: row.target_company_id})
MERGE (a)-[:PARTNERS_WITH]->(b);
```

#### Step 4: Fulltext Indexes

```cypher
CREATE FULLTEXT INDEX search_entities IF NOT EXISTS
FOR (n:Company|Product|RiskFactor|Executive|FinancialMetric)
ON EACH [n.name, n.description];
```

## Code Updates Required

### `setup/populate/loader.py` — Remove

This script loads the old CSV schema (`OFFERS_PRODUCT`, `OFFERS_SERVICE`, `HAS_METRIC`). It is replaced by the `LOAD CSV` Cypher statements above.

### `setup/solutions_bedrock/src/graphrag_validator/retrievers.py` — Update

Two query constants need relationship type renames:

**`CONTEXT_QUERY`** (line 38-51):
```python
# Before
OPTIONAL MATCH (company)-[:OFFERS_PRODUCT]->(product:Product)

# After
OPTIONAL MATCH (company)-[:OFFERS]->(product:Product)
```

**`HYBRID_CONTEXT_QUERY`** (line 55-72):
```python
# Before
OPTIONAL MATCH (company)-[:OFFERS_PRODUCT]->(product:Product)
OPTIONAL MATCH (company)-[:OFFERS_SERVICE]->(service:Service)
...
     collect(DISTINCT service.name)[0..5] AS services
RETURN ...
       services

# After
OPTIONAL MATCH (company)-[:OFFERS]->(product:Product)
# Remove OFFERS_SERVICE match entirely
# Remove services from collect and RETURN
```

**`EXPECTED_NODE_COUNTS`** (line 24-34):
- Remove `"Service"` entry
- Counts will be updated to match the gold database export

### Documentation — Update

- `CLAUDE.md` graph schema section
- `TransformedData/DATA_ARCHITECTURE.md`
- `setup/README.md` schema section
- `Lab_1_Aura_Setup/README.md` (rewrite to use LOAD CSV)
- `Lab_2_Aura_Agents/README.md` (update test questions, remove similarity search references)

## Impact on Labs

### Lab notebooks (4, 6, 7, 8)

No hardcoded entity relationship types in any notebook. Lab 6 only references `FROM_DOCUMENT` and `NEXT_CHUNK`, which are chunk-layer relationships created by the pipeline (not by the CSV load). Labs 4, 7, 8 use natural language and auto-schema-discovery. No changes needed.

### Lab 1

Backup restore is replaced with the LOAD CSV walkthrough. The Explore section works unchanged since `AssetManager — OWNS → Company — FACES_RISK → RiskFactor` is the same in both schemas.

### Lab 2

Aura Agent auto-discovers the schema, so it adapts automatically. The agent gains `COMPETES_WITH` and `PARTNERS_WITH` relationships for richer query results. Fulltext search replaces vector similarity. Test questions in the README need updating.

## Tradeoffs

**What this gains:**
- Single source of truth: CSVs match what the pipeline actually produces
- Real data from LLM extraction rather than hand-curated approximations
- Real asset manager holdings from SEC 13-F filings
- `COMPETES_WITH` and `PARTNERS_WITH` relationships add depth
- Transparent graph construction via LOAD CSV
- `setup/populate/loader.py` can be deleted

**What this loses:**
- Service as a distinct node type (merged into Product)
- Synthetic clean IDs in the CSVs (now generated from database export order)
- No semantic/vector search in Labs 1-2 (deferred to Lab 6)

## Next Steps

1. Run `export_from_neo4j.py` against the gold database to generate updated CSVs
2. Review the exported data for completeness (how many companies, products, risks, etc.)
3. Delete `services.csv`, `company_services.csv`, `sec_filings.csv` from `TransformedData/`
4. Update `retrievers.py` (two query constants)
5. Delete `setup/populate/loader.py`
6. Upload CSVs to S3 bucket
7. Rewrite Lab 1 README with LOAD CSV walkthrough
8. Update Lab 2 README test questions
9. Update documentation (CLAUDE.md, DATA_ARCHITECTURE.md, setup/README.md)
