"""Verify seed-data/ referential integrity, optionally against a live CloudFront copy.

Local mode (default) checks that every chunkId referenced by chunk_documents.csv,
chunk_sequence.csv, and entity_chunks.csv actually exists in chunks.csv. This
catches a truncated or partially-regenerated chunks.csv before it is uploaded.

With --live-base-url, also fetches every *.csv from that URL and compares it
byte-for-byte against the local file, then reports per-document chunk counts
from the live chunks.csv/chunk_documents.csv pair so a partial upload is caught
by exact numbers rather than a "some chunks exist" check.

Usage:
    python3 check_seed_data_integrity.py <seed_data_dir>
    python3 check_seed_data_integrity.py <seed_data_dir> --live-base-url https://<domain>/sec-filings
"""

from __future__ import annotations

import argparse
import csv
import sys
import urllib.request
from collections import Counter
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_chunk_references(seed_data_dir: Path, chunk_ids: set[str]) -> list[str]:
    """Return a list of error messages for chunk IDs referenced but not defined."""
    errors = []
    references = {
        "chunk_documents.csv": "chunkId",
        "chunk_sequence.csv": "chunkId",
        "entity_chunks.csv": "chunkId",
    }
    for filename, column in references.items():
        rows = read_csv(seed_data_dir / filename)
        missing = sorted({row[column] for row in rows} - chunk_ids)
        if missing:
            errors.append(
                f"{filename}: {len(missing)} chunkId(s) referenced but not in "
                f"chunks.csv, e.g. {missing[:5]}"
            )
    # chunk_sequence.csv also references nextChunkId
    rows = read_csv(seed_data_dir / "chunk_sequence.csv")
    missing_next = sorted(
        {row["nextChunkId"] for row in rows if row["nextChunkId"]} - chunk_ids
    )
    if missing_next:
        errors.append(
            f"chunk_sequence.csv: {len(missing_next)} nextChunkId(s) referenced "
            f"but not in chunks.csv, e.g. {missing_next[:5]}"
        )
    return errors


def per_document_chunk_counts(seed_data_dir: Path, chunk_ids: set[str]) -> dict[str, int]:
    """Count how many of chunks_ids' chunks belong to each documentId."""
    chunk_documents = read_csv(seed_data_dir / "chunk_documents.csv")
    counts: Counter[str] = Counter()
    for row in chunk_documents:
        if row["chunkId"] in chunk_ids:
            counts[row["documentId"]] += 1
    return dict(counts)


def document_labels(seed_data_dir: Path) -> dict[str, str]:
    """Map documentId -> "<company name> (<documentId>)" for readable output."""
    companies = {row["companyId"]: row["name"] for row in read_csv(seed_data_dir / "companies.csv")}
    company_documents = read_csv(seed_data_dir / "company_documents.csv")
    labels = {}
    for row in company_documents:
        company_name = companies.get(row["companyId"], row["companyId"])
        labels[row["documentId"]] = f"{company_name} ({row['documentId']})"
    return labels


def fetch_csv_ids(base_url: str, filename: str) -> tuple[bytes, list[dict[str, str]]]:
    with urllib.request.urlopen(f"{base_url}/{filename}", timeout=60) as response:
        content = response.read()
    rows = list(csv.DictReader(content.decode("utf-8").splitlines()))
    return content, rows


def run_local_check(seed_data_dir: Path) -> bool:
    chunks = read_csv(seed_data_dir / "chunks.csv")
    chunk_ids = {row["chunkId"] for row in chunks}
    print(f"  chunks.csv: {len(chunks)} rows, {len(chunk_ids)} unique chunkIds")

    errors = check_chunk_references(seed_data_dir, chunk_ids)
    if errors:
        print("  FAILED referential integrity check:")
        for error in errors:
            print(f"    - {error}")
        return False

    print("  OK: every chunkId referenced by chunk_documents.csv, chunk_sequence.csv, "
          "and entity_chunks.csv exists in chunks.csv.")
    return True


def run_live_check(seed_data_dir: Path, live_base_url: str) -> bool:
    all_ok = True
    for csv_file in sorted(seed_data_dir.glob("*.csv")):
        local_bytes = csv_file.read_bytes()
        try:
            live_bytes, _ = fetch_csv_ids(live_base_url, csv_file.name)
        except OSError as exc:
            print(f"  FAILED to fetch {csv_file.name}: {exc}")
            all_ok = False
            continue
        if live_bytes == local_bytes:
            print(f"  OK: {csv_file.name} matches local")
        else:
            print(f"  MISMATCH: {csv_file.name} (local {len(local_bytes)} bytes, "
                  f"live {len(live_bytes)} bytes)")
            all_ok = False

    live_chunks_bytes, live_chunk_rows = fetch_csv_ids(live_base_url, "chunks.csv")
    live_chunk_ids = {row["chunkId"] for row in live_chunk_rows}
    live_counts = per_document_chunk_counts(seed_data_dir, live_chunk_ids)
    local_chunk_ids = {row["chunkId"] for row in read_csv(seed_data_dir / "chunks.csv")}
    expected_counts = per_document_chunk_counts(seed_data_dir, local_chunk_ids)
    labels = document_labels(seed_data_dir)

    print("\n  Per-document chunk counts (live / expected):")
    mismatched_documents = []
    for document_id in sorted(expected_counts):
        live_count = live_counts.get(document_id, 0)
        expected_count = expected_counts[document_id]
        status = "OK" if live_count == expected_count else "MISMATCH"
        if status == "MISMATCH":
            mismatched_documents.append(document_id)
        print(f"    {labels.get(document_id, document_id)}: {live_count} / {expected_count} [{status}]")

    if mismatched_documents:
        all_ok = False

    return all_ok


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seed_data_dir", type=Path)
    parser.add_argument(
        "--live-base-url",
        default=None,
        help="Base URL (e.g. https://<domain>/sec-filings) to compare against local files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("Local referential integrity check:")
    local_ok = run_local_check(args.seed_data_dir)

    live_ok = True
    if args.live_base_url:
        print(f"\nLive comparison against {args.live_base_url}:")
        live_ok = run_live_check(args.seed_data_dir, args.live_base_url)

    if not (local_ok and live_ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
