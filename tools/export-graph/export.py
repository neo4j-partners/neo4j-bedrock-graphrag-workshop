"""Export the gold Neo4j database to TransformedData/ CSVs.

Filters to primary filing companies (those with a Document node) and their
directly-connected entities only. LLM-extracted "companies" that are really
competitors/partners mentioned in filings are excluded from the company list
but preserved in COMPETES_WITH / PARTNERS_WITH junction tables by name.

Usage:
    cd tools/export-graph
    uv run export.py

Reads credentials from ../../financial_data_load/.env.gold
Writes CSVs to ../../TransformedData/
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent.parent
EXPORT_DIR = ROOT / "TransformedData"
ENV_FILE = ROOT / "financial_data_load" / ".env.gold"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_csv(filename: str, headers: list[str], rows: list[dict]) -> None:
    path = EXPORT_DIR / filename
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {filename}: {len(rows)} rows")


def strip_keys(row: dict, exclude: set[str]) -> dict:
    return {k: v for k, v in row.items() if k not in exclude}


# ---------------------------------------------------------------------------
# Filing company filter
# ---------------------------------------------------------------------------

# Canonical names from financial_data_load/src/loader.py COMPANY_NAME_MAPPINGS.
# These are the 9 companies that actually filed 10-Ks in the dataset.
PRIMARY_COMPANIES = [
    "Amazon.com, Inc.",
    "NVIDIA Corporation",
    "Apple Inc.",
    "PayPal Holdings, Inc.",
    "Intel Corporation",
    "American International Group, Inc.",
    "PG&E Corporation",
    "McDonald's Corporation",
    "Microsoft Corporation",
]

FILING_COMPANY_FILTER = """
    WHERE c.name IN $primary_companies
"""


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def export(driver) -> None:  # noqa: C901
    params = {"primary_companies": PRIMARY_COMPANIES}

    with driver.session() as session:

        # ── Filing companies ─────────────────────────────────────────────
        result = session.run(f"""
            MATCH (c:Company)
            {FILING_COMPANY_FILTER}
            RETURN c.name AS name,
                   coalesce(c.ticker, '') AS ticker,
                   coalesce(c.cik, '') AS cik,
                   coalesce(c.cusip, '') AS cusip
            ORDER BY c.name
        """, **params)
        companies = [dict(r) for r in result]
        company_id_map: dict[str, str] = {}
        company_names: set[str] = set()
        for i, c in enumerate(companies, 1):
            cid = f"C{i:03d}"
            company_id_map[c["name"]] = cid
            company_names.add(c["name"])
            c["company_id"] = cid
        write_csv(
            "companies.csv",
            ["company_id", "name", "ticker", "cik", "cusip"],
            companies,
        )
        print(f"    -> Filing companies: {[c['name'] for c in companies]}")

        # ── Products connected to filing companies ───────────────────────
        result = session.run(f"""
            MATCH (c:Company)-[:OFFERS]->(p:Product)
            {FILING_COMPANY_FILTER}
            AND p.name IS NOT NULL AND p.name <> ''
            RETURN DISTINCT p.name AS name,
                   coalesce(p.description, '') AS description
            ORDER BY p.name
        """, **params)
        products = [dict(r) for r in result]
        product_id_map: dict[str, str] = {}
        for i, p in enumerate(products, 1):
            pid = f"P{i:03d}"
            product_id_map[p["name"]] = pid
            p["product_id"] = pid
        write_csv(
            "products.csv",
            ["product_id", "name", "description"],
            products,
        )

        # ── Risk factors connected to filing companies ───────────────────
        result = session.run(f"""
            MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
            {FILING_COMPANY_FILTER}
            AND r.name IS NOT NULL AND r.name <> ''
            RETURN DISTINCT r.name AS name,
                   coalesce(r.description, '') AS description
            ORDER BY r.name
        """, **params)
        risks = [dict(r) for r in result]
        risk_id_map: dict[str, str] = {}
        for i, r in enumerate(risks, 1):
            rid = f"R{i:03d}"
            risk_id_map[r["name"]] = rid
            r["risk_id"] = rid
        write_csv(
            "risk_factors.csv",
            ["risk_id", "name", "description"],
            risks,
        )

        # ── Executives connected to filing companies ─────────────────────
        result = session.run(f"""
            MATCH (c:Company)-[:HAS_EXECUTIVE]->(e:Executive)
            {FILING_COMPANY_FILTER}
            AND e.name IS NOT NULL AND e.name <> ''
            RETURN DISTINCT e.name AS name,
                   coalesce(e.title, '') AS title,
                   c.name AS company_name
            ORDER BY c.name, e.name
        """, **params)
        executives = [dict(r) for r in result]
        exec_id_map: dict[str, str] = {}
        for i, e in enumerate(executives, 1):
            eid = f"E{i:03d}"
            exec_id_map[e["name"]] = eid
            e["executive_id"] = eid
            e["company_id"] = company_id_map.get(e["company_name"], "")
        write_csv(
            "executives.csv",
            ["executive_id", "name", "title", "company_id"],
            [strip_keys(e, {"company_name"}) for e in executives],
        )

        # ── Financial metrics connected to filing companies ──────────────
        result = session.run(f"""
            MATCH (c:Company)-[:REPORTS]->(m:FinancialMetric)
            {FILING_COMPANY_FILTER}
            AND m.name IS NOT NULL AND m.name <> ''
            RETURN m.name AS metric_name,
                   coalesce(m.value, '') AS value,
                   coalesce(m.period, '') AS period,
                   c.name AS company_name
            ORDER BY c.name, m.name
        """, **params)
        metrics = [dict(r) for r in result]
        for i, m in enumerate(metrics, 1):
            m["metric_id"] = f"FM{i:03d}"
            m["company_id"] = company_id_map.get(m["company_name"], "")
        write_csv(
            "financial_metrics.csv",
            ["metric_id", "company_id", "metric_name", "value", "period"],
            [strip_keys(m, {"company_name"}) for m in metrics],
        )

        # ── Asset managers with OWNS to filing companies ─────────────────
        result = session.run(f"""
            MATCH (a:AssetManager)-[r:OWNS]->(c:Company)
            {FILING_COMPANY_FILTER}
            AND a.managerName IS NOT NULL AND a.managerName <> ''
            RETURN DISTINCT a.managerName AS name
            ORDER BY a.managerName
        """, **params)
        managers = [dict(r) for r in result]
        manager_id_map: dict[str, str] = {}
        for i, m in enumerate(managers, 1):
            mid = f"AM{i:03d}"
            manager_id_map[m["name"]] = mid
            m["manager_id"] = mid
        write_csv(
            "asset_managers.csv",
            ["manager_id", "name"],
            managers,
        )

        # ── Junction: OFFERS (filing company -> product) ─────────────────
        result = session.run(f"""
            MATCH (c:Company)-[:OFFERS]->(p:Product)
            {FILING_COMPANY_FILTER}
            AND p.name IS NOT NULL AND p.name <> ''
            RETURN c.name AS company_name, p.name AS product_name
            ORDER BY c.name, p.name
        """, **params)
        rows = []
        for r in result:
            cid = company_id_map.get(r["company_name"])
            pid = product_id_map.get(r["product_name"])
            if cid and pid:
                rows.append({"company_id": cid, "product_id": pid})
        write_csv("company_products.csv", ["company_id", "product_id"], rows)

        # ── Junction: FACES_RISK (filing company -> risk) ────────────────
        result = session.run(f"""
            MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
            {FILING_COMPANY_FILTER}
            AND r.name IS NOT NULL AND r.name <> ''
            RETURN c.name AS company_name, r.name AS risk_name
            ORDER BY c.name, r.name
        """, **params)
        rows = []
        for r in result:
            cid = company_id_map.get(r["company_name"])
            rid = risk_id_map.get(r["risk_name"])
            if cid and rid:
                rows.append({"company_id": cid, "risk_id": rid})
        write_csv("company_risk_factors.csv", ["company_id", "risk_id"], rows)

        # ── Junction: OWNS (asset manager -> filing company) ─────────────
        result = session.run(f"""
            MATCH (a:AssetManager)-[r:OWNS]->(c:Company)
            {FILING_COMPANY_FILTER}
            AND a.managerName IS NOT NULL AND a.managerName <> ''
            RETURN a.managerName AS manager_name,
                   c.name AS company_name,
                   coalesce(r.shares, 0) AS shares
            ORDER BY a.managerName, c.name
        """, **params)
        rows = []
        for r in result:
            mid = manager_id_map.get(r["manager_name"])
            cid = company_id_map.get(r["company_name"])
            if mid and cid:
                rows.append({
                    "manager_id": mid,
                    "company_id": cid,
                    "shares": r["shares"],
                })
        write_csv(
            "asset_manager_companies.csv",
            ["manager_id", "company_id", "shares"],
            rows,
        )

        # ── Junction: COMPETES_WITH ──────────────────────────────────────
        # Include if at least one side is a filing company.
        # The target may be a non-filing company (mentioned in the filing).
        result = session.run(f"""
            MATCH (a:Company)-[:COMPETES_WITH]->(b:Company)
            WHERE a.name IS NOT NULL AND b.name IS NOT NULL
              AND a.name IN $primary_companies
            RETURN a.name AS source, b.name AS target
            ORDER BY a.name, b.name
        """, **params)
        rows = []
        for r in result:
            sid = company_id_map.get(r["source"])
            if sid:
                # Target might not be a filing company — use name directly
                tid = company_id_map.get(r["target"])
                rows.append({
                    "source_company_id": sid,
                    "target_company_id": tid or "",
                    "target_company_name": r["target"],
                })
        write_csv(
            "company_competitors.csv",
            ["source_company_id", "target_company_id", "target_company_name"],
            rows,
        )

        # ── Junction: PARTNERS_WITH ──────────────────────────────────────
        result = session.run("""
            MATCH (a:Company)-[:PARTNERS_WITH]->(b:Company)
            WHERE a.name IS NOT NULL AND b.name IS NOT NULL
              AND a.name IN $primary_companies
            RETURN a.name AS source, b.name AS target
            ORDER BY a.name, b.name
        """, **params)
        rows = []
        for r in result:
            sid = company_id_map.get(r["source"])
            if sid:
                tid = company_id_map.get(r["target"])
                rows.append({
                    "source_company_id": sid,
                    "target_company_id": tid or "",
                    "target_company_name": r["target"],
                })
        write_csv(
            "company_partners.csv",
            ["source_company_id", "target_company_id", "target_company_name"],
            rows,
        )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def print_summary(driver) -> None:
    """Print node and relationship counts from the database for reference."""
    print("\n--- Full Database Summary ---")
    with driver.session() as session:
        for label in [
            "Company", "Product", "RiskFactor", "Executive",
            "FinancialMetric", "AssetManager", "Document", "Chunk",
        ]:
            result = session.run(
                f"MATCH (n:{label}) RETURN count(n) AS c"
            )
            count = result.single()["c"]
            if count > 0:
                print(f"  {label}: {count:,}")

        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(r) AS count
            ORDER BY count DESC
        """)
        print("  Relationships:")
        for r in result:
            print(f"    {r['type']}: {r['count']:,}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    import os

    if not ENV_FILE.exists():
        print(f"Error: {ENV_FILE} not found", file=sys.stderr)
        sys.exit(1)

    load_dotenv(ENV_FILE)

    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USERNAME")
    password = os.environ.get("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        print(
            "Error: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD must be set",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Connecting to {uri} ...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        print("Connected.\n")

        print_summary(driver)
        print(f"\nExporting filtered data to {EXPORT_DIR}/ ...\n")
        export(driver)
        print("\nDone.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
