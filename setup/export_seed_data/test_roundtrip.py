"""Round-trip test: load seed-data/ files to Neo4j, read back, verify.

Uses the empty test database from .env.gold. Tests the full load path:
chunks.jsonl + chunk_documents.csv + chunk_sequence.csv + entity_chunks.csv.

Usage:
    cd setup/export_seed_data
    uv run test_roundtrip.py
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
SEED_DIR = ROOT / "seed-data"
ENV_FILE = ROOT / ".env.gold"


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f]


def load_csv(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Write to Neo4j (mirrors what the notebook load cell would do)
# ---------------------------------------------------------------------------


def write_to_neo4j(  # noqa: C901
    driver,
    chunks: list[dict],
    chunk_documents: list[dict],
    chunk_sequence: list[dict],
    entity_chunks: list[dict],
    documents: list[dict],
    companies: list[dict],
    products: list[dict],
    risk_factors: list[dict],
    financial_metrics: list[dict],
) -> None:
    # ── Entity nodes ──────────────────────────────────────────────────
    driver.execute_query(
        """UNWIND $docs AS doc
           MERGE (d:Document {documentId: doc.documentId})
           SET d.accessionNumber = doc.accessionNumber,
               d.filingType = doc.filingType""",
        docs=documents,
    )
    driver.execute_query(
        """UNWIND $rows AS row
           CREATE (c:Company {companyId: row.companyId,
                              name: row.name,
                              ticker: row.ticker,
                              cik: row.cik,
                              cusip: row.cusip})""",
        rows=companies,
    )
    driver.execute_query(
        """UNWIND $rows AS row
           CREATE (p:Product {productId: row.productId,
                              name: row.name,
                              description: row.description})""",
        rows=products,
    )
    driver.execute_query(
        """UNWIND $rows AS row
           CREATE (r:RiskFactor {riskId: row.riskId,
                                 name: row.name,
                                 description: row.description})""",
        rows=risk_factors,
    )
    driver.execute_query(
        """UNWIND $rows AS row
           CREATE (m:FinancialMetric {metricId: row.metricId,
                                      name: row.name,
                                      value: row.value,
                                      period: row.period})""",
        rows=financial_metrics,
    )

    # ── Chunk nodes with embeddings ───────────────────────────────────
    driver.execute_query(
        """UNWIND $chunks AS chunk
           CREATE (c:Chunk {chunkId: chunk.chunkId,
                            index: chunk.index,
                            text: chunk.text,
                            embedding: chunk.embedding})""",
        chunks=chunks,
    )

    # ── Vector index ──────────────────────────────────────────────────
    driver.execute_query("""
        CREATE VECTOR INDEX chunkEmbeddings IF NOT EXISTS
        FOR (c:Chunk) ON (c.embedding)
        OPTIONS {indexConfig: {
            `vector.dimensions`: 1024,
            `vector.similarity_function`: 'cosine'
        }}
    """)

    # ── Chunk relationships ───────────────────────────────────────────
    driver.execute_query(
        """UNWIND $rels AS rel
           MATCH (c:Chunk {chunkId: rel.chunkId})
           MATCH (d:Document {documentId: rel.documentId})
           CREATE (c)-[:FROM_DOCUMENT]->(d)""",
        rels=chunk_documents,
    )
    driver.execute_query(
        """UNWIND $rels AS rel
           MATCH (curr:Chunk {chunkId: rel.chunkId})
           MATCH (next:Chunk {chunkId: rel.nextChunkId})
           CREATE (curr)-[:NEXT_CHUNK]->(next)""",
        rels=chunk_sequence,
    )

    # ── FROM_CHUNK (entity -> chunk) ──────────────────────────────────
    # Each entity type uses a different ID property, so one query per type.
    type_config = {
        "Company":         ("Company",         "companyId"),
        "Product":         ("Product",         "productId"),
        "RiskFactor":      ("RiskFactor",      "riskId"),
        "FinancialMetric": ("FinancialMetric", "metricId"),
    }
    for entity_type, (label, id_prop) in type_config.items():
        rels = [
            {"entityId": r["entityId"], "chunkId": r["chunkId"]}
            for r in entity_chunks if r["entityType"] == entity_type
        ]
        if rels:
            driver.execute_query(
                f"""UNWIND $rels AS rel
                    MATCH (e:{label} {{{id_prop}: rel.entityId}})
                    MATCH (c:Chunk {{chunkId: rel.chunkId}})
                    CREATE (e)-[:FROM_CHUNK]->(c)""",
                rels=rels,
            )


def clean(driver) -> None:
    driver.execute_query("MATCH (n) DETACH DELETE n")
    driver.execute_query("DROP INDEX chunkEmbeddings IF EXISTS")


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def verify_chunks(driver, original: list[dict]) -> None:
    """Verify chunk data round-trips exactly."""
    records, _, _ = driver.execute_query("""
        MATCH (c:Chunk)
        WHERE c.embedding IS NOT NULL
        RETURN c.chunkId AS chunkId,
               c.index AS index,
               c.text AS text,
               c.embedding AS embedding
        ORDER BY c.chunkId
    """)

    loaded_map = {}
    for r in records:
        embedding = r["embedding"]
        if hasattr(embedding, "to_native"):
            embedding = embedding.to_native()
        loaded_map[r["chunkId"]] = {
            "index": r["index"],
            "text": r["text"],
            "embedding": list(embedding),
        }

    errors = []
    if len(original) != len(loaded_map):
        errors.append(
            f"Count: expected {len(original)}, got {len(loaded_map)}"
        )

    text_mismatches = 0
    embedding_mismatches = 0
    for o in original:
        loaded = loaded_map.get(o["chunkId"])
        if not loaded:
            continue

        if o["text"] != loaded["text"]:
            text_mismatches += 1

        if len(o["embedding"]) != len(loaded["embedding"]):
            embedding_mismatches += 1
        else:
            for a, b in zip(o["embedding"], loaded["embedding"]):
                if abs(a - b) > 1e-10:
                    embedding_mismatches += 1
                    break

    if text_mismatches:
        errors.append(f"{text_mismatches} text mismatches")
    if embedding_mismatches:
        errors.append(f"{embedding_mismatches} embedding mismatches")

    if errors:
        for e in errors:
            print(f"  FAIL: {e}")
        sys.exit(1)
    print(f"  OK: {len(original)} chunks match")


def verify_from_document(driver, expected: list[dict]) -> None:
    records, _, _ = driver.execute_query(
        "MATCH (:Chunk)-[r:FROM_DOCUMENT]->(:Document) RETURN count(r) AS c"
    )
    actual = records[0]["c"]
    if actual != len(expected):
        print(f"  FAIL: FROM_DOCUMENT count: expected {len(expected)}, got {actual}")
        sys.exit(1)
    print(f"  OK: {actual} FROM_DOCUMENT relationships")


def verify_next_chunk(driver, expected: list[dict]) -> None:
    records, _, _ = driver.execute_query(
        "MATCH (:Chunk)-[r:NEXT_CHUNK]->(:Chunk) RETURN count(r) AS c"
    )
    actual = records[0]["c"]
    if actual != len(expected):
        print(f"  FAIL: NEXT_CHUNK count: expected {len(expected)}, got {actual}")
        sys.exit(1)

    # Verify specific links
    records, _, _ = driver.execute_query("""
        MATCH (curr:Chunk)-[:NEXT_CHUNK]->(next:Chunk)
        RETURN curr.chunkId AS chunkId, next.chunkId AS nextChunkId
        ORDER BY curr.chunkId
    """)
    actual_pairs = {(r["chunkId"], r["nextChunkId"]) for r in records}
    expected_pairs = {(r["chunkId"], r["nextChunkId"]) for r in expected}
    diff = expected_pairs - actual_pairs
    if diff:
        print(f"  FAIL: {len(diff)} NEXT_CHUNK pairs missing")
        sys.exit(1)
    print(f"  OK: {actual} NEXT_CHUNK relationships")


def verify_from_chunk(driver, expected: list[dict]) -> None:
    records, _, _ = driver.execute_query(
        "MATCH ()-[r:FROM_CHUNK]->(:Chunk) RETURN count(r) AS c"
    )
    actual = records[0]["c"]
    if actual != len(expected):
        print(f"  FAIL: FROM_CHUNK count: expected {len(expected)}, got {actual}")
        sys.exit(1)

    # Verify per entity type
    records, _, _ = driver.execute_query("""
        MATCH (e)-[:FROM_CHUNK]->(c:Chunk)
        RETURN labels(e)[0] AS entityType, count(*) AS cnt
        ORDER BY entityType
    """)
    actual_by_type = {r["entityType"]: r["cnt"] for r in records}
    expected_by_type: dict[str, int] = {}
    for r in expected:
        expected_by_type[r["entityType"]] = expected_by_type.get(r["entityType"], 0) + 1

    for etype, exp_count in sorted(expected_by_type.items()):
        act_count = actual_by_type.get(etype, 0)
        if act_count != exp_count:
            print(f"  FAIL: FROM_CHUNK {etype}: expected {exp_count}, got {act_count}")
            sys.exit(1)

    print(f"  OK: {actual} FROM_CHUNK relationships ({', '.join(f'{t}: {c}' for t, c in sorted(actual_by_type.items()))})")


def verify_vector_index(driver) -> None:
    records, _, _ = driver.execute_query(
        "SHOW INDEXES WHERE name = 'chunkEmbeddings'"
    )
    if not records:
        print("  FAIL: chunkEmbeddings index not found")
        sys.exit(1)
    if records[0]["state"] != "ONLINE":
        print(f"  FAIL: index state is {records[0]['state']}, expected ONLINE")
        sys.exit(1)
    print("  OK: vector index online")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    # Check files exist
    required = {
        "chunks.jsonl": SEED_DIR / "chunks.jsonl",
        "chunk_documents.csv": SEED_DIR / "chunk_documents.csv",
        "chunk_sequence.csv": SEED_DIR / "chunk_sequence.csv",
        "entity_chunks.csv": SEED_DIR / "entity_chunks.csv",
        "documents.csv": SEED_DIR / "documents.csv",
        "companies.csv": SEED_DIR / "companies.csv",
        "products.csv": SEED_DIR / "products.csv",
        "risk_factors.csv": SEED_DIR / "risk_factors.csv",
        "financial_metrics.csv": SEED_DIR / "financial_metrics.csv",
    }
    for name, path in required.items():
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

    # Load source files
    chunks = load_jsonl(required["chunks.jsonl"])
    chunk_documents = load_csv(required["chunk_documents.csv"])
    chunk_sequence = load_csv(required["chunk_sequence.csv"])
    entity_chunks = load_csv(required["entity_chunks.csv"])
    documents = load_csv(required["documents.csv"])
    companies = load_csv(required["companies.csv"])
    products = load_csv(required["products.csv"])
    risk_factors = load_csv(required["risk_factors.csv"])
    financial_metrics = load_csv(required["financial_metrics.csv"])

    print(f"Source data: {len(chunks)} chunks, {len(chunk_documents)} FROM_DOCUMENT, "
          f"{len(chunk_sequence)} NEXT_CHUNK, {len(entity_chunks)} FROM_CHUNK, "
          f"{len(documents)} documents")
    print(f"  Entities: {len(companies)} companies, {len(products)} products, "
          f"{len(risk_factors)} risk factors, {len(financial_metrics)} financial metrics")

    print(f"\nConnecting to {uri} ...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        print("Connected.\n")

        print("Cleaning test database ...")
        clean(driver)

        print("Writing to Neo4j ...")
        write_to_neo4j(
            driver, chunks, chunk_documents, chunk_sequence, entity_chunks,
            documents, companies, products, risk_factors, financial_metrics,
        )

        print("\nVerifying ...")
        verify_chunks(driver, chunks)
        verify_from_document(driver, chunk_documents)
        verify_next_chunk(driver, chunk_sequence)
        verify_from_chunk(driver, entity_chunks)
        verify_vector_index(driver)

        print("\nAll tests passed.")
    finally:
        print("\nCleaning up ...")
        clean(driver)
        driver.close()


if __name__ == "__main__":
    main()
