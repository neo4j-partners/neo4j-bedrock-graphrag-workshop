"""Test the Lab 1 structured data load process against a clean database.

Mirrors the Cypher from Lab_1_Aura_Setup/README.md Part 3 (constraints,
nodes, relationships, fulltext index) but reads local CSVs via UNWIND
instead of LOAD CSV from CloudFront URLs.

Uses the empty test database from .env.gold.

Usage:
    cd setup/export_seed_data
    uv run test_load.py
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent          # setup/
SEED_DIR = ROOT / "seed-data"
ENV_FILE = ROOT / ".env.gold"


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------


def load_csv(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------


def clean(driver) -> None:
    driver.execute_query("MATCH (n) DETACH DELETE n")
    for idx in ["companyId", "companyName", "productId", "riskId",
                "managerId", "documentId", "metricId"]:
        driver.execute_query(f"DROP CONSTRAINT {idx} IF EXISTS")
    driver.execute_query("DROP INDEX search_entities IF EXISTS")


# ---------------------------------------------------------------------------
# Load — mirrors Lab 1 README Part 3 Cypher
# ---------------------------------------------------------------------------


def create_constraints(driver) -> None:
    """Step 1: Create Constraints."""
    constraints = [
        "CREATE CONSTRAINT companyId IF NOT EXISTS FOR (c:Company) REQUIRE c.companyId IS UNIQUE",
        "CREATE CONSTRAINT companyName IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT productId IF NOT EXISTS FOR (p:Product) REQUIRE p.productId IS UNIQUE",
        "CREATE CONSTRAINT riskId IF NOT EXISTS FOR (r:RiskFactor) REQUIRE r.riskId IS UNIQUE",
        "CREATE CONSTRAINT managerId IF NOT EXISTS FOR (m:AssetManager) REQUIRE m.managerId IS UNIQUE",
        "CREATE CONSTRAINT documentId IF NOT EXISTS FOR (d:Document) REQUIRE d.documentId IS UNIQUE",
        "CREATE CONSTRAINT metricId IF NOT EXISTS FOR (fm:FinancialMetric) REQUIRE fm.metricId IS UNIQUE",
    ]
    for stmt in constraints:
        driver.execute_query(stmt)
    print("  Created 7 constraints")


def load_nodes(driver, data: dict) -> None:
    """Step 2: Load Nodes (mirrors LOAD CSV + MERGE for each entity type)."""
    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (c:Company {companyId: row.companyId})
           SET c.name = row.name, c.ticker = row.ticker,
               c.cik = row.cik, c.cusip = row.cusip""",
        rows=data["companies"],
    )
    print(f"    Companies: {len(data['companies'])}")

    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (p:Product {productId: row.productId})
           SET p.name = row.name, p.description = row.description""",
        rows=data["products"],
    )
    print(f"    Products: {len(data['products'])}")

    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (r:RiskFactor {riskId: row.riskId})
           SET r.name = row.name, r.description = row.description""",
        rows=data["risk_factors"],
    )
    print(f"    RiskFactors: {len(data['risk_factors'])}")

    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (m:AssetManager {managerId: row.managerId})
           SET m.name = row.name""",
        rows=data["asset_managers"],
    )
    print(f"    AssetManagers: {len(data['asset_managers'])}")

    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (d:Document {documentId: row.documentId})
           SET d.accessionNumber = row.accessionNumber,
               d.filingType = row.filingType""",
        rows=data["documents"],
    )
    print(f"    Documents: {len(data['documents'])}")

    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (fm:FinancialMetric {metricId: row.metricId})
           SET fm.name = row.name, fm.value = row.value,
               fm.period = row.period""",
        rows=data["financial_metrics"],
    )
    print(f"    FinancialMetrics: {len(data['financial_metrics'])}")


def load_relationships(driver, data: dict) -> None:
    """Step 3: Load Relationships (mirrors LOAD CSV + MATCH/MERGE patterns)."""
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (c:Company {companyId: row.companyId})
           MATCH (p:Product {productId: row.productId})
           MERGE (c)-[:OFFERS]->(p)""",
        rows=data["company_products"],
    )
    print(f"    OFFERS: {len(data['company_products'])}")

    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (c:Company {companyId: row.companyId})
           MATCH (r:RiskFactor {riskId: row.riskId})
           MERGE (c)-[:FACES_RISK]->(r)""",
        rows=data["company_risk_factors"],
    )
    print(f"    FACES_RISK: {len(data['company_risk_factors'])}")

    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (m:AssetManager {managerId: row.managerId})
           MATCH (c:Company {companyId: row.companyId})
           MERGE (m)-[:OWNS {shares: toInteger(row.shares)}]->(c)""",
        rows=data["asset_manager_companies"],
    )
    print(f"    OWNS: {len(data['asset_manager_companies'])}")

    # COMPETES_WITH — MERGE on target company name (creates non-filing companies)
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (a:Company {companyId: row.sourceCompanyId})
           MERGE (b:Company {name: row.targetCompanyName})
           MERGE (a)-[:COMPETES_WITH]->(b)""",
        rows=data["company_competitors"],
    )
    print(f"    COMPETES_WITH: {len(data['company_competitors'])}")

    # PARTNERS_WITH — MERGE on target company name (creates non-filing companies)
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (a:Company {companyId: row.sourceCompanyId})
           MERGE (b:Company {name: row.targetCompanyName})
           MERGE (a)-[:PARTNERS_WITH]->(b)""",
        rows=data["company_partners"],
    )
    print(f"    PARTNERS_WITH: {len(data['company_partners'])}")

    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (c:Company {companyId: row.companyId})
           MATCH (d:Document {documentId: row.documentId})
           MERGE (c)-[:FILED]->(d)""",
        rows=data["company_documents"],
    )
    print(f"    FILED: {len(data['company_documents'])}")

    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (c:Company {companyId: row.companyId})
           MATCH (fm:FinancialMetric {metricId: row.metricId})
           MERGE (c)-[:REPORTS]->(fm)""",
        rows=data["company_financial_metrics"],
    )
    print(f"    REPORTS: {len(data['company_financial_metrics'])}")


def create_fulltext_index(driver) -> None:
    """Step 4: Create Fulltext Index."""
    driver.execute_query("""
        CREATE FULLTEXT INDEX search_entities IF NOT EXISTS
        FOR (n:Company|Product|RiskFactor)
        ON EACH [n.name, n.description]
    """)
    print("  Created fulltext index search_entities")


# ---------------------------------------------------------------------------
# Verification — mirrors Lab 1 README Step 5 + extras
# ---------------------------------------------------------------------------


def verify_constraints(driver) -> None:
    records, _, _ = driver.execute_query("SHOW CONSTRAINTS")
    names = {r["name"] for r in records}
    expected = {
        "companyId", "companyName", "productId", "riskId",
        "managerId", "documentId", "metricId",
    }
    missing = expected - names
    if missing:
        print(f"  FAIL: missing constraints: {missing}")
        sys.exit(1)
    print(f"  OK: {len(expected)} constraints present")


def verify_fulltext_index(driver) -> None:
    records, _, _ = driver.execute_query(
        "SHOW INDEXES WHERE name = 'search_entities'"
    )
    if not records:
        print("  FAIL: search_entities fulltext index not found")
        sys.exit(1)
    if records[0]["state"] != "ONLINE":
        print(f"  FAIL: search_entities state is {records[0]['state']}")
        sys.exit(1)
    print("  OK: fulltext index search_entities online")


def verify_node_counts(driver, data: dict) -> None:
    """Verify node counts match CSV inputs (plus MERGE-created companies)."""
    records, _, _ = driver.execute_query("""
        MATCH (n)
        WITH labels(n)[0] AS label, count(n) AS count
        RETURN label, count ORDER BY label
    """)
    actual = {r["label"]: r["count"] for r in records}

    # Competitors/partners MERGE creates extra Company nodes for names not
    # already in the dataset.  Compute expected company count.
    filing_names = {r["name"] for r in data["companies"]}
    merged_names = set()
    for r in data["company_competitors"]:
        merged_names.add(r["targetCompanyName"])
    for r in data["company_partners"]:
        merged_names.add(r["targetCompanyName"])
    extra_companies = len(merged_names - filing_names)
    expected_companies = len(data["companies"]) + extra_companies

    expected = {
        "Company": expected_companies,
        "Product": len(data["products"]),
        "RiskFactor": len(data["risk_factors"]),
        "AssetManager": len(data["asset_managers"]),
        "Document": len(data["documents"]),
        "FinancialMetric": len(data["financial_metrics"]),
    }

    errors = []
    for label, exp in sorted(expected.items()):
        act = actual.get(label, 0)
        if act != exp:
            errors.append(f"{label}: expected {exp}, got {act}")

    if errors:
        for e in errors:
            print(f"  FAIL: {e}")
        sys.exit(1)

    for label, count in sorted(actual.items()):
        extra = ""
        if label == "Company":
            extra = f" ({len(data['companies'])} filing + {extra_companies} mentioned)"
        print(f"    {label}: {count}{extra}")
    print(f"  OK: all node counts match")


def verify_relationship_counts(driver, data: dict) -> None:
    records, _, _ = driver.execute_query("""
        MATCH ()-[r]->()
        RETURN type(r) AS type, count(r) AS count
        ORDER BY type
    """)
    actual = {r["type"]: r["count"] for r in records}

    expected = {
        "OFFERS": len(data["company_products"]),
        "FACES_RISK": len(data["company_risk_factors"]),
        "OWNS": len(data["asset_manager_companies"]),
        "COMPETES_WITH": len(data["company_competitors"]),
        "PARTNERS_WITH": len(data["company_partners"]),
        "FILED": len(data["company_documents"]),
        "REPORTS": len(data["company_financial_metrics"]),
    }

    errors = []
    for rel_type, exp in sorted(expected.items()):
        act = actual.get(rel_type, 0)
        if act != exp:
            errors.append(f"{rel_type}: expected {exp}, got {act}")

    if errors:
        for e in errors:
            print(f"  FAIL: {e}")
        sys.exit(1)

    for rel_type, count in sorted(actual.items()):
        print(f"    {rel_type}: {count}")
    print(f"  OK: all relationship counts match")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    # Check files exist
    csv_files = [
        "companies.csv", "products.csv", "risk_factors.csv",
        "asset_managers.csv", "documents.csv", "financial_metrics.csv",
        "company_products.csv", "company_risk_factors.csv",
        "asset_manager_companies.csv", "company_competitors.csv",
        "company_partners.csv", "company_documents.csv",
        "company_financial_metrics.csv",
    ]
    for name in csv_files:
        path = SEED_DIR / name
        if not path.exists():
            print(f"Error: {path} not found", file=sys.stderr)
            sys.exit(1)
    if not ENV_FILE.exists():
        print(f"Error: {ENV_FILE} not found", file=sys.stderr)
        sys.exit(1)

    load_dotenv(ENV_FILE)
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USERNAME")
    password = os.environ.get("NEO4J_PASSWORD")
    if not all([uri, user, password]):
        print("Error: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD must be set",
              file=sys.stderr)
        sys.exit(1)

    # Load all CSVs
    data = {
        "companies": load_csv(SEED_DIR / "companies.csv"),
        "products": load_csv(SEED_DIR / "products.csv"),
        "risk_factors": load_csv(SEED_DIR / "risk_factors.csv"),
        "asset_managers": load_csv(SEED_DIR / "asset_managers.csv"),
        "documents": load_csv(SEED_DIR / "documents.csv"),
        "financial_metrics": load_csv(SEED_DIR / "financial_metrics.csv"),
        "company_products": load_csv(SEED_DIR / "company_products.csv"),
        "company_risk_factors": load_csv(SEED_DIR / "company_risk_factors.csv"),
        "asset_manager_companies": load_csv(SEED_DIR / "asset_manager_companies.csv"),
        "company_competitors": load_csv(SEED_DIR / "company_competitors.csv"),
        "company_partners": load_csv(SEED_DIR / "company_partners.csv"),
        "company_documents": load_csv(SEED_DIR / "company_documents.csv"),
        "company_financial_metrics": load_csv(SEED_DIR / "company_financial_metrics.csv"),
    }

    print("Source data:")
    print(f"  Nodes: {len(data['companies'])} companies, {len(data['products'])} products, "
          f"{len(data['risk_factors'])} risk factors, {len(data['financial_metrics'])} metrics, "
          f"{len(data['asset_managers'])} asset managers, {len(data['documents'])} documents")
    print(f"  Rels:  {len(data['company_products'])} OFFERS, "
          f"{len(data['company_risk_factors'])} FACES_RISK, "
          f"{len(data['asset_manager_companies'])} OWNS, "
          f"{len(data['company_competitors'])} COMPETES_WITH, "
          f"{len(data['company_partners'])} PARTNERS_WITH, "
          f"{len(data['company_documents'])} FILED, "
          f"{len(data['company_financial_metrics'])} REPORTS")

    print(f"\nConnecting to {uri} ...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        print("Connected.\n")

        print("Cleaning test database ...")
        clean(driver)

        print("\nStep 1: Create constraints ...")
        create_constraints(driver)

        print("\nStep 2: Load nodes ...")
        load_nodes(driver, data)

        print("\nStep 3: Load relationships ...")
        load_relationships(driver, data)

        print("\nStep 4: Create fulltext index ...")
        create_fulltext_index(driver)

        print("\nStep 5: Verify ...")
        verify_constraints(driver)
        verify_fulltext_index(driver)
        verify_node_counts(driver, data)
        verify_relationship_counts(driver, data)

        print("\nAll tests passed.")
    finally:
        print("\nCleaning up ...")
        clean(driver)
        driver.close()


if __name__ == "__main__":
    main()
