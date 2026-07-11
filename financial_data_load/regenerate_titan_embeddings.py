#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "boto3",
# ]
# ///
"""Regenerate seed chunk embeddings with Amazon Titan Text Embeddings V2.

The seed vectors in ``seed-data/chunks.jsonl`` were originally generated with
Amazon Nova. The workshop standardized on Titan Text Embeddings V2, so the
stored vectors must be regenerated with Titan to stay in the same vector space
as the query-time embedder. Run this once after the Nova to Titan code swap.

Usage:
    uv run financial_data_load/regenerate_titan_embeddings.py [--region us-east-1]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import boto3

MODEL_ID = "amazon.titan-embed-text-v2:0"
DIMENSIONS = 1024
DEFAULT_PATH = Path(__file__).parent / "seed-data" / "chunks.jsonl"


def embed(client, text: str) -> list[float]:
    """Return the Titan Text Embeddings V2 vector for ``text``."""
    body = {"inputText": text, "dimensions": DIMENSIONS, "normalize": True}
    response = client.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
    return json.loads(response["body"].read())["embedding"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    lines = [line for line in args.path.read_text().splitlines() if line.strip()]
    records = [json.loads(line) for line in lines]
    client = boto3.client("bedrock-runtime", region_name=args.region)

    tmp = args.path.with_suffix(".jsonl.tmp")
    with tmp.open("w") as out:
        for i, record in enumerate(records, start=1):
            record["embedding"] = embed(client, record["text"])
            out.write(json.dumps(record) + "\n")
            if i % 25 == 0 or i == len(records):
                print(f"  embedded {i}/{len(records)}")
    tmp.replace(args.path)
    print(f"Regenerated {len(records)} embeddings with {MODEL_ID} ({DIMENSIONS} dims)")


if __name__ == "__main__":
    main()
