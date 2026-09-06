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
| D006 | Alphabet | 0/5 |
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

```bash
curl -s https://dhoj7jltw73ew.cloudfront.net/sec-filings/chunks.csv -o /tmp/cf_chunks.csv
diff /tmp/cf_chunks.csv financial_data_load/seed-data/chunks.csv && echo IDENTICAL
```

Then, on a freshly-loaded Aura instance (or any existing instance, by
re-running Lab 1 Step 4 and Step 6 to backfill), confirm all 7 documents
have chunks:

```cypher
MATCH (d:Document)
OPTIONAL MATCH (d)<-[:FROM_DOCUMENT]-(c:Chunk)
RETURN d.source, count(c) AS chunks
ORDER BY chunks;
```

Every row should show a non-zero count.

## Note for anyone who already ran Lab 1 before the fix

Re-running Lab 1's Step 4 and Step 6 Cypher (`LOAD CSV ... chunks.csv` /
`LOAD CSV ... chunk_documents.csv`) after the refresh will backfill the
missing `Chunk` nodes and relationships via `MERGE` — no need to clear and
reload the whole database.
