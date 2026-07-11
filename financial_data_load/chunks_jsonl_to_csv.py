#!/usr/bin/env python3
"""Convert seed-data/chunks.jsonl into chunks.csv for the Lab 1 Cypher LOAD CSV.

Each JSONL record ({chunkId, index, text, embedding[1024]}) becomes one CSV row
with the embedding serialized as a ';'-delimited float string so the Lab 1
Cypher can rebuild the vector with split()/toFloat() — no APOC required.

Usage:
    python chunks_jsonl_to_csv.py
    python chunks_jsonl_to_csv.py --jsonl path/to/chunks.jsonl --csv path/to/chunks.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SEED_DIR = Path(__file__).parent / "seed-data"
FIELDNAMES = ["chunkId", "index", "text", "embedding"]


def convert(jsonl_path: Path, csv_path: Path) -> int:
    """Convert a chunks JSONL file to CSV. Returns the number of rows written."""
    rows_written = 0
    with (
        jsonl_path.open(encoding="utf-8") as src,
        csv_path.open("w", encoding="utf-8", newline="") as dst,
    ):
        writer = csv.DictWriter(dst, fieldnames=FIELDNAMES)
        writer.writeheader()
        for line_number, line in enumerate(src, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            embedding = record["embedding"]
            if len(embedding) != 1024:
                raise ValueError(
                    f"line {line_number}: expected 1024-dim embedding, "
                    f"got {len(embedding)}"
                )
            writer.writerow(
                {
                    "chunkId": record["chunkId"],
                    "index": record["index"],
                    "text": record["text"],
                    "embedding": ";".join(repr(value) for value in embedding),
                }
            )
            rows_written += 1
    return rows_written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", type=Path, default=SEED_DIR / "chunks.jsonl")
    parser.add_argument("--csv", type=Path, default=SEED_DIR / "chunks.csv")
    args = parser.parse_args()

    count = convert(args.jsonl, args.csv)
    print(f"Wrote {count} chunk rows to {args.csv}")


if __name__ == "__main__":
    main()
