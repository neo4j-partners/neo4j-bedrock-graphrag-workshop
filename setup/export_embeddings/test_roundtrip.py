"""Round-trip test: write chunks.jsonl to Neo4j, read back, verify.

Uses the empty test database from .env.gold.

Usage:
    cd setup/export_embeddings
    uv run test_roundtrip.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent          # setup/
SEED_DIR = ROOT / "seed-data"
ENV_FILE = ROOT / ".env.gold"
JSONL_FILE = SEED_DIR / "chunks.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f]


def clean(driver) -> None:
    """Remove all Chunk and Document nodes from the test database."""
    driver.execute_query("MATCH (c:Chunk) DETACH DELETE c")
    driver.execute_query("MATCH (d:Document) DETACH DELETE d")
    # Drop vector index if it exists
    driver.execute_query(
        "DROP INDEX chunkEmbeddings IF EXISTS"
    )


def write_chunks(driver, chunks: list[dict]) -> None:
    """Write chunks to Neo4j — mirrors what the notebook load cell would do."""

    # Create vector index
    driver.execute_query("""
        CREATE VECTOR INDEX chunkEmbeddings IF NOT EXISTS
        FOR (c:Chunk) ON (c.embedding)
        OPTIONS {indexConfig: {
            `vector.dimensions`: 1024,
            `vector.similarity_function`: 'cosine'
        }}
    """)

    # Create Document nodes from distinct paths
    doc_paths = list({c["document_path"] for c in chunks})
    driver.execute_query(
        "UNWIND $paths AS path MERGE (d:Document {path: path})",
        paths=doc_paths,
    )

    # Create Chunk nodes with embeddings and link to Documents
    driver.execute_query("""
        UNWIND $chunks AS chunk
        CREATE (c:Chunk {index: chunk.index, text: chunk.text,
                         embedding: chunk.embedding})
        WITH c, chunk
        MATCH (d:Document {path: chunk.document_path})
        CREATE (c)-[:FROM_DOCUMENT]->(d)
    """, chunks=chunks)

    # Create NEXT_CHUNK relationships (ordered by document_path, index)
    driver.execute_query("""
        MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
        WITH d, c ORDER BY c.index
        WITH d, collect(c) AS ordered
        UNWIND range(0, size(ordered) - 2) AS i
        WITH ordered[i] AS curr, ordered[i + 1] AS next
        CREATE (curr)-[:NEXT_CHUNK]->(next)
    """)


def read_chunks(driver) -> list[dict]:
    """Read chunks back from Neo4j."""
    records, _, _ = driver.execute_query("""
        MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
        WHERE c.embedding IS NOT NULL
        RETURN c.index AS index,
               c.text AS text,
               c.embedding AS embedding,
               d.path AS document_path
        ORDER BY d.path, c.index
    """)
    result = []
    for r in records:
        embedding = r["embedding"]
        if hasattr(embedding, "to_native"):
            embedding = embedding.to_native()
        result.append({
            "index": r["index"],
            "text": r["text"],
            "embedding": list(embedding),
            "document_path": r["document_path"],
        })
    return result


def verify(original: list[dict], loaded: list[dict]) -> None:
    """Compare original JSONL data against round-tripped data."""
    errors = []

    if len(original) != len(loaded):
        errors.append(f"Count mismatch: {len(original)} original vs {len(loaded)} loaded")

    # Build lookup by (document_path, index) for comparison
    orig_map = {(c["document_path"], c["index"]): c for c in original}
    loaded_map = {(c["document_path"], c["index"]): c for c in loaded}

    missing = set(orig_map) - set(loaded_map)
    extra = set(loaded_map) - set(orig_map)

    if missing:
        errors.append(f"Missing {len(missing)} chunks after load")
    if extra:
        errors.append(f"Extra {len(extra)} chunks after load")

    # Compare matching chunks
    text_mismatches = 0
    embedding_mismatches = 0
    for key in sorted(set(orig_map) & set(loaded_map)):
        o = orig_map[key]
        l = loaded_map[key]

        if o["text"] != l["text"]:
            text_mismatches += 1

        if len(o["embedding"]) != len(l["embedding"]):
            embedding_mismatches += 1
        else:
            for a, b in zip(o["embedding"], l["embedding"]):
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


def verify_relationships(driver, original: list[dict]) -> None:
    """Verify FROM_DOCUMENT and NEXT_CHUNK relationships."""
    errors = []

    # Check FROM_DOCUMENT count
    records, _, _ = driver.execute_query(
        "MATCH (:Chunk)-[r:FROM_DOCUMENT]->(:Document) RETURN count(r) AS c"
    )
    from_doc_count = records[0]["c"]
    if from_doc_count != len(original):
        errors.append(
            f"FROM_DOCUMENT count: expected {len(original)}, got {from_doc_count}"
        )

    # Check NEXT_CHUNK count — should be (chunks_per_doc - 1) summed across docs
    docs: dict[str, int] = {}
    for c in original:
        docs[c["document_path"]] = docs.get(c["document_path"], 0) + 1
    expected_next = sum(n - 1 for n in docs.values())

    records, _, _ = driver.execute_query(
        "MATCH (:Chunk)-[r:NEXT_CHUNK]->(:Chunk) RETURN count(r) AS c"
    )
    next_count = records[0]["c"]
    if next_count != expected_next:
        errors.append(
            f"NEXT_CHUNK count: expected {expected_next}, got {next_count}"
        )

    # Check Document node count
    records, _, _ = driver.execute_query(
        "MATCH (d:Document) RETURN count(d) AS c"
    )
    doc_count = records[0]["c"]
    expected_docs = len(docs)
    if doc_count != expected_docs:
        errors.append(
            f"Document count: expected {expected_docs}, got {doc_count}"
        )

    if errors:
        for e in errors:
            print(f"  FAIL: {e}")
        sys.exit(1)


def verify_vector_index(driver) -> None:
    """Verify the vector index exists and is populated."""
    records, _, _ = driver.execute_query(
        "SHOW INDEXES WHERE name = 'chunkEmbeddings'"
    )
    if not records:
        print("  FAIL: chunkEmbeddings index not found")
        sys.exit(1)

    idx = records[0]
    if idx["state"] != "ONLINE":
        print(f"  FAIL: index state is {idx['state']}, expected ONLINE")
        sys.exit(1)


def main() -> None:
    if not ENV_FILE.exists():
        print(f"Error: {ENV_FILE} not found", file=sys.stderr)
        sys.exit(1)
    if not JSONL_FILE.exists():
        print(f"Error: {JSONL_FILE} not found — run export.py first", file=sys.stderr)
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

        # Load source data
        original = load_jsonl(JSONL_FILE)
        print(f"Loaded {len(original)} chunks from {JSONL_FILE.name}")

        # Clean slate
        print("Cleaning test database ...")
        clean(driver)

        # Write
        print("Writing chunks to Neo4j ...")
        write_chunks(driver, original)

        # Read back
        print("Reading chunks back ...")
        loaded = read_chunks(driver)

        # Verify
        print(f"Verifying {len(loaded)} chunks ...")
        verify(original, loaded)
        print("  OK: all chunk data matches")

        verify_relationships(driver, original)
        print("  OK: all relationships correct")

        verify_vector_index(driver)
        print("  OK: vector index online")

        print("\nAll tests passed.")

    finally:
        # Clean up test data
        print("\nCleaning up ...")
        clean(driver)
        driver.close()


if __name__ == "__main__":
    main()
