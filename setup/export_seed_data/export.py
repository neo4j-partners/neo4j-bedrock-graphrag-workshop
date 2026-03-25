"""Export Neo4j graph data to setup/seed-data/.

Exports the full knowledge graph: structured layer (companies, products,
risk factors, asset managers, documents, financial metrics, and all their
relationships) plus unstructured layer (chunks with embeddings, and their
FROM_DOCUMENT, NEXT_CHUNK, FROM_CHUNK relationships).

Filters to filing companies (those with a FILED relationship to a Document
node) and their directly-connected entities.

Usage:
    cd setup/export_seed_data
    uv run export.py

Reads credentials from ../setup/.env
Writes all output to ../setup/seed-data/
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
# Export: Structured Layer
# ---------------------------------------------------------------------------


def export(driver) -> dict:  # noqa: C901
    """Export structured layer. Returns id_maps for use by export_chunks."""
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
            c["companyId"] = cid
        write_csv(
            "companies.csv",
            ["companyId", "name", "ticker", "cik", "cusip"],
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
            p["productId"] = pid
        write_csv(
            "products.csv",
            ["productId", "name", "description"],
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
            r["riskId"] = rid
        write_csv(
            "risk_factors.csv",
            ["riskId", "name", "description"],
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
            m["metricId"] = mid
        write_csv(
            "financial_metrics.csv",
            ["metricId", "name", "value", "period"],
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
            m["managerId"] = mid
        write_csv(
            "asset_managers.csv",
            ["managerId", "name"],
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
            d["documentId"] = did
            d["accessionNumber"] = accession
            d["filingType"] = "10-K"
        write_csv(
            "documents.csv",
            ["documentId", "accessionNumber", "filingType"],
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
                rows.append({"companyId": cid, "productId": pid})
        write_csv("company_products.csv", ["companyId", "productId"], rows)

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
                rows.append({"companyId": cid, "riskId": rid})
        write_csv("company_risk_factors.csv", ["companyId", "riskId"], rows)

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
                rows.append({"companyId": cid, "metricId": mid})
        write_csv(
            "company_financial_metrics.csv",
            ["companyId", "metricId"],
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
                    "managerId": mid,
                    "companyId": cid,
                    "shares": r["shares"],
                })
        write_csv(
            "asset_manager_companies.csv",
            ["managerId", "companyId", "shares"],
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
                    "sourceCompanyId": sid,
                    "targetCompanyId": tid or "",
                    "targetCompanyName": r["target"],
                })
        write_csv(
            "company_competitors.csv",
            ["sourceCompanyId", "targetCompanyId", "targetCompanyName"],
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
                    "sourceCompanyId": sid,
                    "targetCompanyId": tid or "",
                    "targetCompanyName": r["target"],
                })
        write_csv(
            "company_partners.csv",
            ["sourceCompanyId", "targetCompanyId", "targetCompanyName"],
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
                rows.append({"companyId": cid, "documentId": did})
        write_csv("company_documents.csv", ["companyId", "documentId"], rows)

    return {
        "company_names": company_names,
        "doc_id_map": doc_id_map,
        "product_id_map": product_id_map,
        "risk_id_map": risk_id_map,
        "metric_id_map": metric_id_map,
        "company_id_map": company_id_map,
    }


# ---------------------------------------------------------------------------
# Export: Unstructured Layer (chunks with embeddings)
# ---------------------------------------------------------------------------


def export_chunks(driver, id_maps: dict) -> None:
    """Export chunks, embeddings, and chunk relationships to seed-data/."""

    company_names = id_maps["company_names"]
    doc_id_map = id_maps["doc_id_map"]
    product_id_map = id_maps["product_id_map"]
    risk_id_map = id_maps["risk_id_map"]
    metric_id_map = id_maps["metric_id_map"]
    company_id_map = id_maps["company_id_map"]

    with driver.session() as session:
        params = {"filing_companies": company_names}

        # ── Chunks with embeddings (JSONL) ───────────────────────────
        result = session.run("""
            MATCH (c:Company)-[:FILED]->(d:Document)<-[:FROM_DOCUMENT]-(chunk:Chunk)
            WHERE c.name IN $filing_companies
              AND chunk.embedding IS NOT NULL
            RETURN chunk.index AS index,
                   chunk.text AS text,
                   chunk.embedding AS embedding,
                   d.path AS document_path
            ORDER BY d.path, chunk.index
        """, **params)
        chunks = [dict(r) for r in result]

        # Assign chunk IDs and build map keyed by (document_path, index)
        chunk_id_map: dict[tuple[str, int], str] = {}
        for i, c in enumerate(chunks, 1):
            cid = f"CH{i:03d}"
            chunk_id_map[(c["document_path"], c["index"])] = cid

        # Write JSONL — embedding stored as native JSON array
        jsonl_path = EXPORT_DIR / "chunks.jsonl"
        with open(jsonl_path, "w") as f:
            for c in chunks:
                embedding = c["embedding"]
                if hasattr(embedding, "to_native"):
                    embedding = embedding.to_native()
                obj = {
                    "chunkId": chunk_id_map[(c["document_path"], c["index"])],
                    "index": c["index"],
                    "text": c["text"],
                    "embedding": embedding,
                }
                f.write(json.dumps(obj) + "\n")
        file_size = jsonl_path.stat().st_size
        print(f"  chunks.jsonl: {len(chunks)} chunks ({file_size / 1024 / 1024:.1f} MB)")

        # ── chunk_documents.csv (FROM_DOCUMENT) ─────────────────────
        rows = []
        for c in chunks:
            chid = chunk_id_map.get((c["document_path"], c["index"]))
            did = doc_id_map.get(c["document_path"])
            if chid and did:
                rows.append({"chunkId": chid, "documentId": did})
        write_csv(
            "chunk_documents.csv", ["chunkId", "documentId"], rows,
        )

        # ── chunk_sequence.csv (NEXT_CHUNK) ──────────────────────────
        result = session.run("""
            MATCH (c:Company)-[:FILED]->(d:Document)<-[:FROM_DOCUMENT]-(curr:Chunk)
                  -[:NEXT_CHUNK]->(next:Chunk)-[:FROM_DOCUMENT]->(d)
            WHERE c.name IN $filing_companies
            RETURN curr.index AS curr_index, next.index AS next_index,
                   d.path AS document_path
            ORDER BY d.path, curr.index
        """, **params)
        rows = []
        for r in result:
            curr_id = chunk_id_map.get((r["document_path"], r["curr_index"]))
            next_id = chunk_id_map.get((r["document_path"], r["next_index"]))
            if curr_id and next_id:
                rows.append({"chunkId": curr_id, "nextChunkId": next_id})
        write_csv(
            "chunk_sequence.csv", ["chunkId", "nextChunkId"], rows,
        )

        # ── entity_chunks.csv (FROM_CHUNK) ───────────────────────────
        # Map entity label → (id_map, id_field_name)
        entity_configs = [
            ("Product", product_id_map),
            ("RiskFactor", risk_id_map),
            ("FinancialMetric", metric_id_map),
            ("Company", company_id_map),
        ]

        rows = []
        for label, id_map in entity_configs:
            result = session.run(f"""
                MATCH (e:{label})-[:FROM_CHUNK]->(chunk:Chunk)
                      -[:FROM_DOCUMENT]->(d:Document)<-[:FILED]-(c:Company)
                WHERE c.name IN $filing_companies
                RETURN e.name AS entity_name, chunk.index AS chunk_index,
                       d.path AS document_path
                ORDER BY d.path, chunk.index, e.name
            """, **params)
            for r in result:
                eid = id_map.get(r["entity_name"])
                chid = chunk_id_map.get(
                    (r["document_path"], r["chunk_index"]),
                )
                if eid and chid:
                    rows.append({
                        "entityType": label,
                        "entityId": eid,
                        "chunkId": chid,
                    })

        write_csv(
            "entity_chunks.csv",
            ["entityType", "entityId", "chunkId"],
            rows,
        )


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
        print(f"\nExporting structured data to {EXPORT_DIR}/ ...\n")
        id_maps = export(driver)
        print(f"\nExporting chunks to {EXPORT_DIR}/ ...\n")
        export_chunks(driver, id_maps)
        print("\nDone.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
