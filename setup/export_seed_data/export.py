"""Export Neo4j graph data to setup/seed-data/ CSVs and setup/seed-embeddings/.

Exports the structured layer of the knowledge graph: companies, products,
risk factors, asset managers, documents, financial metrics, and all their
relationships. Filters to filing companies (those with a FILED relationship
to a Document node) and their directly-connected entities.

Also exports the unstructured layer (chunks with embeddings) to JSONL and
their relationships (FROM_DOCUMENT, NEXT_CHUNK, FROM_CHUNK) to CSVs in
setup/seed-embeddings/.

Usage:
    cd setup/export_seed_data
    uv run export.py

Reads credentials from ../setup/.env
Writes CSVs to ../setup/seed-data/ and ../setup/seed-embeddings/
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent          # setup/
EXPORT_DIR = ROOT / "seed-data"
EMBEDDINGS_DIR = ROOT / "seed-embeddings"
ENV_FILE = ROOT / ".env"

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
# Export
# ---------------------------------------------------------------------------


def export(driver) -> None:  # noqa: C901
    with driver.session() as session:

        # ── Discover filing companies (those with FILED -> Document) ───
        result = session.run("""
            MATCH (c:Company)-[:FILED]->(d:Document)
            RETURN DISTINCT c.name AS name,
                   coalesce(c.ticker, '') AS ticker,
                   coalesce(c.cik, '') AS cik,
                   coalesce(c.cusip, '') AS cusip
            ORDER BY c.name
        """)
        companies = [dict(r) for r in result]
        company_id_map: dict[str, str] = {}
        company_names: list[str] = []
        for i, c in enumerate(companies, 1):
            cid = f"C{i:03d}"
            company_id_map[c["name"]] = cid
            company_names.append(c["name"])
            c["company_id"] = cid
        write_csv(
            "companies.csv",
            ["company_id", "name", "ticker", "cik", "cusip"],
            companies,
        )
        print(f"    -> Filing companies: {company_names}")

        params = {"filing_companies": company_names}

        # ── Products connected to filing companies ─────────────────────
        result = session.run("""
            MATCH (c:Company)-[:OFFERS]->(p:Product)
            WHERE c.name IN $filing_companies
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

        # ── Risk factors connected to filing companies ─────────────────
        result = session.run("""
            MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
            WHERE c.name IN $filing_companies
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

        # ── Financial metrics connected to filing companies ────────────
        result = session.run("""
            MATCH (c:Company)-[:REPORTS]->(m:FinancialMetric)
            WHERE c.name IN $filing_companies
              AND m.name IS NOT NULL AND m.name <> ''
            RETURN DISTINCT m.name AS name,
                   coalesce(m.value, '') AS value,
                   coalesce(m.period, '') AS period
            ORDER BY m.name
        """, **params)
        metrics = [dict(r) for r in result]
        metric_id_map: dict[str, str] = {}
        for i, m in enumerate(metrics, 1):
            mid = f"FM{i:03d}"
            metric_id_map[m["name"]] = mid
            m["metric_id"] = mid
        write_csv(
            "financial_metrics.csv",
            ["metric_id", "name", "value", "period"],
            metrics,
        )

        # ── Asset managers with OWNS to filing companies ───────────────
        result = session.run("""
            MATCH (a:AssetManager)-[:OWNS]->(c:Company)
            WHERE c.name IN $filing_companies
              AND a.name IS NOT NULL AND a.name <> ''
            RETURN DISTINCT a.name AS name
            ORDER BY a.name
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

        # ── Documents filed by filing companies ────────────────────────
        # Document nodes use 'path' (PDF filename contains accession number).
        # filing_type is not stored as a property; all docs are 10-K filings.
        result = session.run("""
            MATCH (c:Company)-[:FILED]->(d:Document)
            WHERE c.name IN $filing_companies
            RETURN DISTINCT d.path AS path
            ORDER BY d.path
        """, **params)
        documents = [dict(r) for r in result]
        doc_id_map: dict[str, str] = {}
        for i, d in enumerate(documents, 1):
            did = f"D{i:03d}"
            # Extract accession number from PDF filename
            accession = Path(d["path"]).stem if d["path"] else ""
            doc_id_map[d["path"]] = did
            d["document_id"] = did
            d["accession_number"] = accession
            d["filing_type"] = "10-K"
        write_csv(
            "documents.csv",
            ["document_id", "accession_number", "filing_type"],
            [strip_keys(d, {"path"}) for d in documents],
        )

        # ── Junction: OFFERS (company -> product) ──────────────────────
        result = session.run("""
            MATCH (c:Company)-[:OFFERS]->(p:Product)
            WHERE c.name IN $filing_companies
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

        # ── Junction: FACES_RISK (company -> risk) ─────────────────────
        result = session.run("""
            MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
            WHERE c.name IN $filing_companies
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

        # ── Junction: REPORTS (company -> financial metric) ────────────
        result = session.run("""
            MATCH (c:Company)-[:REPORTS]->(m:FinancialMetric)
            WHERE c.name IN $filing_companies
              AND m.name IS NOT NULL AND m.name <> ''
            RETURN c.name AS company_name, m.name AS metric_name
            ORDER BY c.name, m.name
        """, **params)
        rows = []
        for r in result:
            cid = company_id_map.get(r["company_name"])
            mid = metric_id_map.get(r["metric_name"])
            if cid and mid:
                rows.append({"company_id": cid, "metric_id": mid})
        write_csv(
            "company_financial_metrics.csv",
            ["company_id", "metric_id"],
            rows,
        )

        # ── Junction: OWNS (asset manager -> company) ──────────────────
        result = session.run("""
            MATCH (a:AssetManager)-[r:OWNS]->(c:Company)
            WHERE c.name IN $filing_companies
              AND a.name IS NOT NULL AND a.name <> ''
            RETURN a.name AS manager_name,
                   c.name AS company_name,
                   coalesce(r.shares, 0) AS shares
            ORDER BY a.name, c.name
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

        # ── Junction: COMPETES_WITH ────────────────────────────────────
        result = session.run("""
            MATCH (a:Company)-[:COMPETES_WITH]->(b:Company)
            WHERE a.name IN $filing_companies
              AND a.name IS NOT NULL AND b.name IS NOT NULL
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
            "company_competitors.csv",
            ["source_company_id", "target_company_id", "target_company_name"],
            rows,
        )

        # ── Junction: PARTNERS_WITH ────────────────────────────────────
        result = session.run("""
            MATCH (a:Company)-[:PARTNERS_WITH]->(b:Company)
            WHERE a.name IN $filing_companies
              AND a.name IS NOT NULL AND b.name IS NOT NULL
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

        # ── Junction: FILED (company -> document) ──────────────────────
        result = session.run("""
            MATCH (c:Company)-[:FILED]->(d:Document)
            WHERE c.name IN $filing_companies
            RETURN c.name AS company_name, d.path AS doc_path
            ORDER BY c.name, d.path
        """, **params)
        rows = []
        for r in result:
            cid = company_id_map.get(r["company_name"])
            did = doc_id_map.get(r["doc_path"])
            if cid and did:
                rows.append({"company_id": cid, "document_id": did})
        write_csv("company_documents.csv", ["company_id", "document_id"], rows)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def print_summary(driver) -> None:
    print("\n--- Database Summary ---")
    with driver.session() as session:
        for label in [
            "Company", "Product", "RiskFactor", "FinancialMetric",
            "AssetManager", "Document", "Chunk",
        ]:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
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
        print(f"\nExporting to {EXPORT_DIR}/ ...\n")
        export(driver)
        print("\nDone.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
