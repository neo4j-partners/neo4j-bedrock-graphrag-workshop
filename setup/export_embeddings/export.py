"""Export Neo4j Chunk nodes with embeddings to JSONL.

Each line is a JSON object with: index, text, embedding, document_path.
The NEXT_CHUNK ordering is implicit (sort by document_path, index).

Usage:
    cd setup/export_embeddings
    uv run export.py

Reads credentials from ../setup/.env
Writes to ../setup/seed-data/chunks.jsonl
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent          # setup/
EXPORT_DIR = ROOT / "seed-data"
ENV_FILE = ROOT / ".env"


def export(driver) -> None:
    records, _, _ = driver.execute_query("""
        MATCH (c:Chunk)-[:FROM_DOCUMENT]->(d:Document)
        WHERE c.embedding IS NOT NULL
        RETURN c.index AS index,
               c.text AS text,
               c.embedding AS embedding,
               d.path AS document_path
        ORDER BY d.path, c.index
    """)

    output_path = EXPORT_DIR / "chunks.jsonl"
    with open(output_path, "w") as f:
        for r in records:
            embedding = r["embedding"]
            if hasattr(embedding, "to_native"):
                embedding = embedding.to_native()

            obj = {
                "index": r["index"],
                "text": r["text"],
                "embedding": embedding,
                "document_path": r["document_path"],
            }
            f.write(json.dumps(obj) + "\n")

    print(f"Exported {len(records)} chunks to {output_path}")

    # Quick sanity check
    sample = records[0] if records else None
    if sample:
        emb = sample["embedding"]
        if hasattr(emb, "to_native"):
            emb = emb.to_native()
        print(f"  Dimensions: {len(emb)}")
        print(f"  Sample embedding[:5]: {emb[:5]}")
        file_size = output_path.stat().st_size
        print(f"  File size: {file_size / 1024 / 1024:.1f} MB")


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
        export(driver)
        print("\nDone.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
