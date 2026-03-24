# High-Quality Seed Data Tools

Scripts for exporting a curated slice of the financial knowledge graph from the live Neo4j database and verifying it against the Lab 1 sample queries.

## Quick Start

```bash
cd highquality

# 1. Review what's in the database
uv run export_slice.py --discover

# 2. Export curated CSVs to setup/seed-data/
uv run export_slice.py

# 3. Verify Lab 1 sample queries against the live database
uv run verify_queries.py

# 4. Upload refreshed CSVs to S3/CloudFront
../setup/setup_s3_seed_data.sh --refresh
```

## Scripts

### `export_slice.py`

Exports a curated subset of the knowledge graph to `setup/seed-data/` CSVs. Connects to Neo4j via `financial_data_load/.env`.

**`--discover` mode** prints all products and risk factors grouped by company for human review before populating the curated lists.

**Default (export) mode** writes 9 CSV files using hardcoded curated lists, then runs verification:

- Referential integrity across all junction tables
- Count summary (filing companies, mentioned companies, products, risk factors, edges)
- Lab 1 query smoke tests (NVIDIA products, shared risks, Microsoft competitors, NVIDIA partners, asset manager holdings)

### `verify_queries.py`

Runs all 7 Lab 1 sample queries against the live database and reports pass/fail:

| # | Query | Verifies |
|---|-------|----------|
| 1 | Node counts | Database has AssetManager, Company, Product, RiskFactor nodes |
| 2 | NVIDIA products | `Company-OFFERS->Product` pattern returns results |
| 3 | Shared risk factors | Risk factors connected to 2+ companies exist |
| 4 | Top asset managers | `AssetManager-OWNS->Company` with share counts works |
| 5 | Microsoft competitors | `Company-COMPETES_WITH->Company` returns clean competitor list |
| 6 | Portfolio risk exposure | `AssetManager-OWNS->Company-FACES_RISK->RiskFactor` traversal works |
| 7 | NVIDIA partners | `Company-PARTNERS_WITH->Company` (expected empty on live DB — partners are in CSV only) |

## Prerequisites

- `financial_data_load/.env` with `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
- [uv](https://docs.astral.sh/uv/) (dependencies are declared inline via PEP 723)
