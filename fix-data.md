# Bug: stale `chunks.csv` on CloudFront — most companies load with zero Chunks

## Symptom

Reported by a workshop attendee: `Document` nodes carry the correct PDF path,
but the text that actually gets chunked seems to come from only one filing.

## Root cause

`Lab_1_Aura_Setup/README.md` has every learner `LOAD CSV` from
`https://dhoj7jltw73ew.cloudfront.net/sec-filings/*.csv`. That CloudFront
distribution serves whatever was last pushed by
`setup/setup_s3_seed_data.sh --refresh`, sourced from
`financial_data_load/seed-data/*.csv`.

`chunks.csv` was regenerated locally (346 rows, all 7 companies) after the
last S3 refresh, so the refresh was never re-run for it. The live file is
stale: 109 rows instead of 346.

`documents.csv` and `chunk_documents.csv` on CloudFront are fully up to date
and identical to local, so every learner gets all 7 `Document` nodes with
correct `source` paths. But `chunk_documents.csv` references chunk IDs
(CH110–CH346) that don't exist in the truncated live `chunks.csv`, so
`MATCH (c:Chunk {chunkId: row.chunkId})` in Lab 1 Step 6 silently matches
nothing for those rows, and `FROM_DOCUMENT` never gets created for them.

Verified by diffing every file the live CloudFront endpoint serves against
the local `financial_data_load/seed-data/` copies (2026-09-06). Every file
matched except `chunks.csv`. Impact per document:

| Document | Company | Chunks live / total |
|---|---|---|
| D001 | Apple | 27/27 |
| D002 | Microsoft | 72/72 |
| D003 | PG&E | 10/99 |
| D004 | Amazon | 0/33 |
| D005 | NVIDIA | 0/49 |
| D006 | Apple (second filing) | 0/5 |
| D007 | PayPal | 0/61 |

Every other seed CSV (`companies.csv`, `products.csv`, `risk_factors.csv`,
`asset_managers.csv`, `financial_metrics.csv`, `company_products.csv`,
`company_risk_factors.csv`, `asset_manager_companies.csv`,
`company_competitors.csv`, `company_partners.csv`, `company_documents.csv`,
`company_financial_metrics.csv`, `chunk_documents.csv`,
`chunk_sequence.csv`, `entity_chunks.csv`) is byte-identical live vs. local.
This is a single-file staleness issue, not a broader drift problem.

## Fix

Re-upload the current local seed data and invalidate the CloudFront cache:

```bash
./setup/setup_s3_seed_data.sh --refresh
```

This uploads every `*.csv` in `financial_data_load/seed-data/` to
`s3://neo4j-aws-workshop-data/sec-filings/` and creates a CloudFront
invalidation for `/sec-filings/*`. All files except `chunks.csv` are already
identical, so the re-upload is a no-op for them; only `chunks.csv` actually
changes. Cache clears within a few minutes per the script's own output.

**Status: fixed 2026-09-06.** `./setup/setup_s3_seed_data.sh --refresh` was run
and the CloudFront cache invalidated. Verified: live `chunks.csv` is now
byte-identical to local (346 rows, CH001-CH346, all 7 companies).

## Verify after refresh

A "some chunks exist" check would have missed this bug too, since 109 of 346
rows still loaded fine. Assert the exact expected count per document instead:

```cypher
MATCH (d:Document)
OPTIONAL MATCH (d)<-[:FROM_DOCUMENT]-(c:Chunk)
WITH d.source AS source, count(c) AS chunks
RETURN source, chunks,
       CASE source
           WHEN 'form10k-sample/0000320193-23-000106.pdf' THEN 27  // D001 Apple
           WHEN 'form10k-sample/0000950170-23-035122.pdf' THEN 72  // D002 Microsoft
           WHEN 'form10k-sample/0001004980-23-000029.pdf' THEN 99  // D003 PG&E
           WHEN 'form10k-sample/0001018724-23-000004.pdf' THEN 33  // D004 Amazon
           WHEN 'form10k-sample/0001045810-23-000017.pdf' THEN 49  // D005 NVIDIA
           WHEN 'form10k-sample/0001096906-23-001489.pdf' THEN 5   // D006 Apple (2nd filing)
           WHEN 'form10k-sample/0001633917-23-000033.pdf' THEN 61  // D007 PayPal
       END AS expected
ORDER BY source;
```

Every row's `chunks` should equal its `expected`.

This same exact-count check, plus a byte-for-byte comparison of every seed
CSV against CloudFront, is now automated — see below.

## New tooling added after this bug

Two checks were added to `setup/setup_s3_seed_data.sh` so this class of bug
is caught automatically instead of relying on a manual audit like the one
that found it:

1. **Pre-deploy referential integrity check** (`setup/check_seed_data_integrity.py`,
   local only, no AWS calls). Runs automatically at the start of both
   `--refresh` and the first-time bucket setup. Verifies every chunkId
   referenced by `chunk_documents.csv`, `chunk_sequence.csv` (`chunkId` and
   `nextChunkId`), and `entity_chunks.csv` actually exists in `chunks.csv`.
   Aborts the upload if not.

2. **Post-upload S3 checksum verification**, added to `--refresh`. After
   uploading, compares each object's S3 ETag against the local file's MD5 and
   aborts before invalidating the CloudFront cache if any mismatch.

3. **`./setup/setup_s3_seed_data.sh --verify-live`** — standalone, run any
   time. Fetches every seed CSV from the live CloudFront URL, diffs it
   byte-for-byte against local, and prints the exact live/expected chunk
   count for every document (not just non-zero). This is what would have
   caught the original bug immediately, and is what confirmed the fix:

   ```
   Per-document chunk counts (live / expected):
     Apple Inc. (D001): 27 / 27 [OK]
     Microsoft Corporation (D002): 72 / 72 [OK]
     PG&E Corporation (D003): 99 / 99 [OK]
     Amazon.com, Inc. (D004): 33 / 33 [OK]
     NVIDIA Corporation (D005): 49 / 49 [OK]
     Apple Inc. (D006): 5 / 5 [OK]
     PayPal Holdings, Inc. (D007): 61 / 61 [OK]
   ```

None of these catch "someone forgot to run `--refresh` at all" (nothing
automated runs on a schedule), but they do catch a partial/corrupted upload
or a stale live copy the moment anyone runs `--refresh` or `--verify-live`.

## Note for anyone who already ran Lab 1 before the fix

Re-running Lab 1's Step 4 and Step 6 Cypher (`LOAD CSV ... chunks.csv` /
`LOAD CSV ... chunk_documents.csv`) after the refresh will backfill the
missing `Chunk` nodes and relationships via `MERGE` — no need to clear and
reload the whole database.
