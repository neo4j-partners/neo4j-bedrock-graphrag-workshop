"""Standalone loader: build the full SEC 10-K knowledge graph from seed-data/.

Loads everything the workshop needs into a Neo4j instance and keeps it:
the structured layer (companies, products, risk factors, asset managers,
documents, financial metrics and their relationships) plus the unstructured
layer (document chunks with Titan Text Embeddings V2, the vector index, and the
chunk-to-graph links).

Mirrors the Cypher in Lab_1_Aura_Setup/README.md, but reads the local CSV /
JSONL files in seed-data/ via UNWIND instead of LOAD CSV from CloudFront.

Reads Neo4j credentials from financial_data_load/.env by default (override
with --env). The target database is cleared first unless --no-clear is given;
clearing prompts for confirmation unless --yes is passed.

Usage:
    cd financial_data_load/export_seed_data
    uv run load-data.py                    # load into .env target (confirm clear)
    uv run load-data.py --yes              # skip the clear confirmation
    uv run load-data.py --no-clear         # load without wiping first
    uv run load-data.py --env ../.env.gold # load into a different instance
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

ROOT = Path(__file__).resolve().parent.parent          # financial_data_load/
SEED_DIR = ROOT / "seed-data"
DEFAULT_ENV = ROOT / ".env"


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------


def load_csv(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f]


def load_seed_data() -> dict[str, list[dict]]:
    """Read every seed-data file used by the load."""
    csv_files = {
        "companies": "companies.csv",
        "products": "products.csv",
        "risk_factors": "risk_factors.csv",
        "asset_managers": "asset_managers.csv",
        "documents": "documents.csv",
        "financial_metrics": "financial_metrics.csv",
        "company_products": "company_products.csv",
        "company_risk_factors": "company_risk_factors.csv",
        "asset_manager_companies": "asset_manager_companies.csv",
        "company_competitors": "company_competitors.csv",
        "company_partners": "company_partners.csv",
        "company_documents": "company_documents.csv",
        "company_financial_metrics": "company_financial_metrics.csv",
        "chunk_documents": "chunk_documents.csv",
        "chunk_sequence": "chunk_sequence.csv",
        "entity_chunks": "entity_chunks.csv",
    }
    missing = [name for name in [*csv_files.values(), "chunks.jsonl"]
               if not (SEED_DIR / name).exists()]
    if missing:
        print(f"Error: missing seed files: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    data = {key: load_csv(SEED_DIR / name) for key, name in csv_files.items()}
    data["chunks"] = load_jsonl(SEED_DIR / "chunks.jsonl")
    return data


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------


def clear_database(driver: Driver) -> None:
    """Remove all nodes, relationships, and the load's indexes."""
    driver.execute_query("MATCH (n) DETACH DELETE n")
    driver.execute_query("DROP INDEX chunkEmbeddings IF EXISTS")
    driver.execute_query("DROP INDEX search_entities IF EXISTS")
    print("  Cleared existing data")


# ---------------------------------------------------------------------------
# Load — mirrors Lab 1 README Cypher (LOAD CSV -> UNWIND on local files)
# ---------------------------------------------------------------------------


def create_constraints(driver: Driver) -> None:
    """Step 1: uniqueness constraints (also back MERGE lookups during load)."""
    constraints = [
        "CREATE CONSTRAINT companyId IF NOT EXISTS FOR (c:Company) REQUIRE c.companyId IS UNIQUE",
        "CREATE CONSTRAINT companyName IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT productId IF NOT EXISTS FOR (p:Product) REQUIRE p.productId IS UNIQUE",
        "CREATE CONSTRAINT riskId IF NOT EXISTS FOR (r:RiskFactor) REQUIRE r.riskId IS UNIQUE",
        "CREATE CONSTRAINT managerId IF NOT EXISTS FOR (m:AssetManager) REQUIRE m.managerId IS UNIQUE",
        "CREATE CONSTRAINT documentId IF NOT EXISTS FOR (d:Document) REQUIRE d.documentId IS UNIQUE",
        "CREATE CONSTRAINT metricId IF NOT EXISTS FOR (fm:FinancialMetric) REQUIRE fm.metricId IS UNIQUE",
        "CREATE CONSTRAINT chunkId IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunkId IS UNIQUE",
    ]
    for stmt in constraints:
        driver.execute_query(stmt)
    print(f"  Created {len(constraints)} constraints")


def load_nodes(driver: Driver, data: dict) -> None:
    """Step 2: structured entity nodes."""
    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (c:Company {companyId: row.companyId})
           SET c.name = row.name, c.ticker = row.ticker,
               c.cik = row.cik, c.cusip = row.cusip""",
        rows=data["companies"],
    )
    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (p:Product {productId: row.productId})
           SET p.name = row.name, p.description = row.description""",
        rows=data["products"],
    )
    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (r:RiskFactor {riskId: row.riskId})
           SET r.name = row.name, r.description = row.description""",
        rows=data["risk_factors"],
    )
    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (m:AssetManager {managerId: row.managerId})
           SET m.name = row.name""",
        rows=data["asset_managers"],
    )
    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (d:Document {documentId: row.documentId})
           SET d.accessionNumber = row.accessionNumber,
               d.filingType = row.filingType, d.source = row.source""",
        rows=data["documents"],
    )
    driver.execute_query(
        """UNWIND $rows AS row
           MERGE (fm:FinancialMetric {metricId: row.metricId})
           SET fm.name = row.name, fm.value = row.value, fm.period = row.period""",
        rows=data["financial_metrics"],
    )
    print(
        f"    {len(data['companies'])} companies, {len(data['products'])} products, "
        f"{len(data['risk_factors'])} risk factors, {len(data['asset_managers'])} "
        f"asset managers, {len(data['documents'])} documents, "
        f"{len(data['financial_metrics'])} financial metrics"
    )


def load_relationships(driver: Driver, data: dict) -> None:
    """Step 3: structured relationships."""
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (c:Company {companyId: row.companyId})
           MATCH (p:Product {productId: row.productId})
           MERGE (c)-[:OFFERS]->(p)""",
        rows=data["company_products"],
    )
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (c:Company {companyId: row.companyId})
           MATCH (r:RiskFactor {riskId: row.riskId})
           MERGE (c)-[:FACES_RISK]->(r)""",
        rows=data["company_risk_factors"],
    )
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (m:AssetManager {managerId: row.managerId})
           MATCH (c:Company {companyId: row.companyId})
           MERGE (m)-[:OWNS {shares: toInteger(row.shares)}]->(c)""",
        rows=data["asset_manager_companies"],
    )
    # COMPETES_WITH / PARTNERS_WITH MERGE on target name, creating Company
    # nodes for competitors/partners not present in companies.csv.
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (a:Company {companyId: row.sourceCompanyId})
           MERGE (b:Company {name: row.targetCompanyName})
           MERGE (a)-[:COMPETES_WITH]->(b)""",
        rows=data["company_competitors"],
    )
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (a:Company {companyId: row.sourceCompanyId})
           MERGE (b:Company {name: row.targetCompanyName})
           MERGE (a)-[:PARTNERS_WITH]->(b)""",
        rows=data["company_partners"],
    )
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (c:Company {companyId: row.companyId})
           MATCH (d:Document {documentId: row.documentId})
           MERGE (c)-[:FILED]->(d)""",
        rows=data["company_documents"],
    )
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (c:Company {companyId: row.companyId})
           MATCH (fm:FinancialMetric {metricId: row.metricId})
           MERGE (c)-[:REPORTS]->(fm)""",
        rows=data["company_financial_metrics"],
    )
    print(
        f"    {len(data['company_products'])} OFFERS, "
        f"{len(data['company_risk_factors'])} FACES_RISK, "
        f"{len(data['asset_manager_companies'])} OWNS, "
        f"{len(data['company_competitors'])} COMPETES_WITH, "
        f"{len(data['company_partners'])} PARTNERS_WITH, "
        f"{len(data['company_documents'])} FILED, "
        f"{len(data['company_financial_metrics'])} REPORTS"
    )


def load_chunks(driver: Driver, data: dict) -> None:
    """Step 4: chunk nodes with pre-computed Titan Text Embeddings V2."""
    driver.execute_query(
        """UNWIND $chunks AS chunk
           MERGE (c:Chunk {chunkId: chunk.chunkId})
           SET c.index = chunk.index, c.text = chunk.text,
               c.embedding = chunk.embedding""",
        chunks=data["chunks"],
    )
    print(f"    {len(data['chunks'])} chunks")


def create_vector_index(driver: Driver) -> None:
    """Step 5: vector index for approximate nearest-neighbor search."""
    driver.execute_query("""
        CREATE VECTOR INDEX chunkEmbeddings IF NOT EXISTS
        FOR (c:Chunk) ON (c.embedding)
        OPTIONS {indexConfig: {
            `vector.dimensions`: 1024,
            `vector.similarity_function`: 'cosine'
        }}
    """)
    print("  Created vector index chunkEmbeddings")


def link_chunks(driver: Driver, data: dict) -> None:
    """Step 6: link chunks to documents, to each other, and to entities."""
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (c:Chunk {chunkId: row.chunkId})
           MATCH (d:Document {documentId: row.documentId})
           MERGE (c)-[:FROM_DOCUMENT]->(d)""",
        rows=data["chunk_documents"],
    )
    driver.execute_query(
        """UNWIND $rows AS row
           MATCH (curr:Chunk {chunkId: row.chunkId})
           MATCH (next:Chunk {chunkId: row.nextChunkId})
           MERGE (curr)-[:NEXT_CHUNK]->(next)""",
        rows=data["chunk_sequence"],
    )

    # FROM_CHUNK: each entity type keys on a different id property.
    type_config = {
        "Company": ("Company", "companyId"),
        "Product": ("Product", "productId"),
        "RiskFactor": ("RiskFactor", "riskId"),
        "FinancialMetric": ("FinancialMetric", "metricId"),
    }
    from_chunk_total = 0
    for entity_type, (label, id_prop) in type_config.items():
        rows = [
            {"entityId": r["entityId"], "chunkId": r["chunkId"]}
            for r in data["entity_chunks"] if r["entityType"] == entity_type
        ]
        if not rows:
            continue
        driver.execute_query(
            f"""UNWIND $rows AS row
                MATCH (e:{label} {{{id_prop}: row.entityId}})
                MATCH (c:Chunk {{chunkId: row.chunkId}})
                MERGE (e)-[:FROM_CHUNK]->(c)""",
            rows=rows,
        )
        from_chunk_total += len(rows)
    print(
        f"    {len(data['chunk_documents'])} FROM_DOCUMENT, "
        f"{len(data['chunk_sequence'])} NEXT_CHUNK, {from_chunk_total} FROM_CHUNK"
    )


def create_fulltext_index(driver: Driver) -> None:
    """Step 7: fulltext index over entity names and descriptions."""
    driver.execute_query("""
        CREATE FULLTEXT INDEX search_entities IF NOT EXISTS
        FOR (n:Company|Product|RiskFactor)
        ON EACH [n.name, n.description]
    """)
    print("  Created fulltext index search_entities")


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------


def verify(driver: Driver, data: dict) -> None:
    """Print node/relationship counts and index states after the load."""
    node_records, _, _ = driver.execute_query("""
        MATCH (n)
        WITH labels(n)[0] AS label, count(n) AS count
        RETURN label, count ORDER BY label
    """)
    print("  Nodes:")
    for r in node_records:
        print(f"    {r['label']}: {r['count']}")

    rel_records, _, _ = driver.execute_query("""
        MATCH ()-[r]->()
        WITH type(r) AS type, count(r) AS count
        RETURN type, count ORDER BY type
    """)
    print("  Relationships:")
    for r in rel_records:
        print(f"    {r['type']}: {r['count']}")

    index_records, _, _ = driver.execute_query(
        "SHOW INDEXES WHERE name IN ['chunkEmbeddings', 'search_entities']"
    )
    print("  Indexes:")
    for r in index_records:
        print(f"    {r['name']}: {r['state']}")

    # Sanity check chunk count against the source file.
    chunk_count = next(
        (r["count"] for r in node_records if r["label"] == "Chunk"), 0
    )
    if chunk_count != len(data["chunks"]):
        print(
            f"  WARNING: loaded {chunk_count} chunks, expected {len(data['chunks'])}",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load the full SEC 10-K knowledge graph from seed-data/ into Neo4j.",
    )
    parser.add_argument(
        "--env", type=Path, default=DEFAULT_ENV,
        help=f"Path to the .env file with Neo4j credentials (default: {DEFAULT_ENV})",
    )
    parser.add_argument(
        "--no-clear", dest="clear", action="store_false",
        help="Do not wipe the database first (MERGE makes the load idempotent)",
    )
    parser.add_argument(
        "--yes", action="store_true",
        help="Skip the confirmation prompt before clearing the database",
    )
    return parser.parse_args()


def connect(env_file: Path) -> Driver:
    if not env_file.exists():
        print(f"Error: {env_file} not found", file=sys.stderr)
        sys.exit(1)
    load_dotenv(env_file)

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
    driver.verify_connectivity()
    print("Connected.\n")
    return driver


def main() -> None:
    args = parse_args()
    data = load_seed_data()

    driver = connect(args.env)
    try:
        if args.clear:
            if not args.yes:
                reply = input(
                    f"This will DELETE all data in {args.env}'s target database. "
                    "Continue? [y/N] "
                ).strip().lower()
                if reply not in ("y", "yes"):
                    print("Aborted.")
                    return
            print("Clearing database ...")
            clear_database(driver)

        print("\nStep 1: Create constraints ...")
        create_constraints(driver)

        print("\nStep 2: Load nodes ...")
        load_nodes(driver, data)

        print("\nStep 3: Load relationships ...")
        load_relationships(driver, data)

        print("\nStep 4: Load chunks ...")
        load_chunks(driver, data)

        print("\nStep 5: Create vector index ...")
        create_vector_index(driver)

        print("\nStep 6: Link chunks to the graph ...")
        link_chunks(driver, data)

        print("\nStep 7: Create fulltext index ...")
        create_fulltext_index(driver)

        print("\nVerifying ...")
        verify(driver, data)

        print("\nLoad complete.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
