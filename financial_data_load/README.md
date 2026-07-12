# Financial Data Load Workshop

Build a GraphRAG knowledge graph from SEC 10-K financial filings using Neo4j, AWS Bedrock, and the neo4j-graphrag-python library.

## Prerequisites

- Neo4j Aura instance (or local Neo4j database)
- Python 3.12.x
- [uv](https://docs.astral.sh/uv/) package manager
- AWS account with Bedrock model access enabled
- AWS credentials configured (`~/.aws/credentials`, env vars, or IAM role)

## Quick Start

All commands below assume you are in the `financial_data_load/` directory:

```bash
cd financial_data_load
```

### 1. Install Dependencies

```bash
uv sync --prerelease=allow
```

### 2. Configure Neo4j

Edit the `.env` file (copy from `.env.sample` if needed) and set the Neo4j credentials:

```bash
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

### 3. Configure AWS Bedrock

Add the following to your `.env`:

```bash
AWS_REGION=us-east-1
MODEL_ID=us.anthropic.claude-sonnet-4-6
```

The LLM uses the model specified by `MODEL_ID` (required). Embeddings use Amazon Titan Text Embeddings V2 (1024 dimensions by default) — override with `EMBEDDING_DIMENSIONS` if needed.

AWS credentials are resolved by the standard boto3 credential chain (env vars, `~/.aws/credentials`, IAM role).

### 4. Test Connections

```bash
uv run python main.py test
```

### 5. Load PDFs and Create Backup (one-time)

This step processes PDFs through the LLM (~25 min for all 8) and creates a backup. You only need to do this once. The `load` command handles both CSV metadata and PDF processing.

```bash
# Test with 1 PDF first (optional)
uv run python main.py load --limit 1 --clear

# Load all 8 PDFs (~25 min)
uv run python main.py load --clear

# Back up the database — saves all nodes, relationships, and embeddings to JSON
uv run python main.py backup
```

The backup file is saved to `backups/` and contains the full database state after PDF processing. This is your checkpoint — you can always restore to this point without re-processing PDFs.

### 6. Run Cleanse Pipeline

Restore the database from backup, then cleanse (validate + deduplicate + normalize) and finalize. This is fast and can be repeated with different settings.

```bash
# Restore database to post-PDF-processing state
# (skip this on first run — your DB is already in the right state after step 5)
uv run python main.py restore

# Generate cleanse plan (validate + dedup all entity types — does not modify Neo4j)
uv run python main.py cleanse

# Review the plan (optional)
cat plans/cleanse_plan_*.json

# Apply plan: removals → merges → normalize
uv run python main.py apply-cleanse

# Create constraints, indexes, asset managers
uv run python main.py finalize

# Verify everything
uv run python main.py verify
```

The `cleanse` command generates a plan file covering all entity types (Company, Executive, Product, RiskFactor, FinancialMetric). It runs in two phases:

1. **Validation** — LLM checks each entity belongs to its label. Invalid entities are marked for removal.
2. **Deduplication** — Per-label entity resolution with label-specific pre-filters and LLM prompts. Produces merge groups.

The plan file is the review artifact. Nothing touches Neo4j until `apply-cleanse`.

The `apply-cleanse` command executes the plan in three steps:
1. Remove invalid entities (DETACH DELETE)
2. Merge duplicates (apoc.refactor.mergeNodes with property fill)
3. Normalize descriptions (LLM rewrites messy text in place)

You can skip normalization with `--skip-normalize` if you only want removals and merges.

### Entity Resolution Configuration

Entity resolution parameters are configured via `.env` with the `ER_` prefix. These apply to all entity types during the cleanse dedup phase, with per-label defaults for pre-filter strategy and threshold:

```bash
ER_PRE_FILTER_STRATEGY=fuzzy        # Pre-filter: "fuzzy", "prefix", or "honorific"
ER_PRE_FILTER_THRESHOLD=0.6         # Similarity threshold for candidate pairs
ER_BATCH_SIZE=10                     # Pairs per LLM batch
ER_CONFIDENCE_MODE=binary            # "binary" or "scored"
ER_CONFIDENCE_THRESHOLD=0.8          # Auto-merge threshold (scored mode only)
ER_MAX_GROUP_SIZE=10                 # Max entities in a merge group
```

Per-label defaults (used by the cleanse pipeline):

| Label | Strategy | Threshold |
|-------|----------|-----------|
| Company | prefix | 0.3 |
| Executive | honorific | 0.5 |
| Product | fuzzy | 0.6 |
| RiskFactor | fuzzy | 0.6 |
| FinancialMetric | fuzzy | 0.7 |

### All Commands

| Command | Description |
|---------|-------------|
| `main.py test` | Test Neo4j and AI provider connections |
| `main.py load [--limit N] [--files PDF ...] [--clear]` | Load CSV metadata + process PDFs |
| `main.py backup` | Back up full database to `backups/` |
| `main.py restore [--backup PATH]` | Restore database from backup |
| `main.py cleanse [--phase validate\|dedup]` | Generate cleanse plan (does not modify Neo4j) |
| `main.py apply-cleanse [--plan PATH] [--skip-normalize]` | Apply cleanse plan (removals, merges, normalize) |
| `main.py normalize` | Run normalization standalone (rewrite descriptions/fields via LLM) |
| `main.py fix-companies` | Merge known company name variants that dedup missed |
| `main.py finalize` | Constraints, indexes, asset managers, verify |
| `main.py verify` | Counts + enrichment checks + end-to-end search validation |
| `main.py clean` | Clear all data |
| `main.py samples [--limit N]` | Run sample queries showcasing the graph |
| `test_solutions.sh <env-file> [N\|N-M]` | Test solutions against a given `.env` file |
| `main.py snapshot` | Export Company entity snapshot (for standalone resolution testing) |
| `main.py resolve [--snapshot PATH] [--strategy ...] [--threshold ...]` | LLM entity resolution on snapshot (Company only) |
| `main.py compare` | Compare resolution runs, score against ground truth |
| `main.py apply-merges [--plan PATH]` | Apply merge plan from resolve |
| `main.py export-model <model>` | Export current graph state tagged by model name (for A/B extraction comparison) |
| `main.py compare-models [--a PATH --b PATH]` | Compare two model extraction snapshots |

### 7. Run Sample Queries

After loading and cleansing the data, run the built-in sample queries to explore the knowledge graph. These are read-only and don't modify the database.

```bash
# Run all 9 sample query sections (10 rows each)
uv run python main.py samples

# Limit rows per section
uv run python main.py samples --limit 5
```

The samples cover:
1. **Company Overview** — companies with entity counts
2. **Risk Factors** — risk factors from 10-K filings
3. **Products & Services** — products offered by companies
4. **Executives** — company executives and board members
5. **Financial Metrics** — key financial metrics
6. **Competitive Landscape** — competitor relationships
7. **Asset Manager Holdings** — top positions by share count
8. **Document-Chunk Structure** — documents, chunk counts, and chain preview
9. **Vector Similarity Search** — finds similar chunks via the vector index (uses stored embeddings, no API key needed)

Each section prints the Cypher query it runs followed by the results, making it useful for learning graph query patterns.

### 8. Run Workshop Solutions

```bash
# Interactive menu
uv run python main.py solutions

# Run specific solution
uv run python main.py solutions 4

# Run all (from option 4 onwards)
uv run python main.py solutions A
```

### 9. Test Solutions

Use the test script to validate all solutions against a given `.env` file:

```bash
# Run all safe solutions (4-22, skips destructive 1-3)
./test_solutions.sh .env.gold

# Run a specific solution
./test_solutions.sh .env.gold 8

# Run a range
./test_solutions.sh .env.gold 8-11
```

Each solution runs with a 5-minute timeout. `test_solutions.sh` uses its own solution numbering (1-22), separate from the `main.py solutions` menu (1-12). Solutions 9-11 (MCP) require `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN` in the env file; they are skipped if not configured. The env file is sourced into the shell environment; your `.env` is not modified.

## Workshop Solutions

Solution numbers below match the `main.py solutions` menu and the `SOLUTIONS` list in `main.py`. Files live in `solution_srcs/`.

### Lab 3: Intro to Bedrock and Agents (03_xx)

| # | Solution | Description |
|---|----------|-------------|
| 1 | `03_01_basic_strands_agent.py` | Basic Strands agent with tools |
| 2 | `03_02_deploy_to_agentcore.py` | Deploy agent to AgentCore |

### Lab 4: neo4j-graphrag Library (04_xx)

Data loading and GraphRAG retrieval patterns using neo4j-graphrag:

| # | Solution | Description |
|---|----------|-------------|
| 3 | `04_01_load_and_query.py` | Load data and query |
| 4 | `04_02_vector_retriever.py` | Vector retriever |
| 5 | `04_03_vector_cypher_retriever.py` | VectorCypher retriever |
| 6 | `04_04_strands_graphrag_agent.py` | Strands GraphRAG agent |

### Lab 5: MCP Server (05_xx)

Strands Agents SDK with MCP to search a Neo4j knowledge graph:

| # | Solution | Description |
|---|----------|-------------|
| 7 | `05_01_intro_strands_mcp.py` | Intro to Strands + MCP |
| 8 | `05_02_graph_enriched_search.py` | Graph-enriched search via MCP |
| 9 | `05_03_text2cypher_agent.py` | Text2Cypher agent |

### Lab 6: GraphRAG Pipeline (06_xx)

Data pipeline patterns using neo4j-graphrag. **Solution 10 deletes all data.**

| # | Solution | Description |
|---|----------|-------------|
| 10 | `06_01_data_loading.py` | Load financial documents into Neo4j |
| 11 | `06_02_embeddings.py` | Generate and store vector embeddings |
| 12 | `06_03_vector_cypher_retriever.py` | Vector search + custom Cypher |

## AI Provider

Uses `BedrockLLM` and `BedrockEmbeddings` from [neo4j-graphrag-python](https://github.com/neo4j-partners/neo4j-graphrag-python). AWS credentials are resolved by the standard boto3 credential chain (env vars, `~/.aws/credentials`, IAM role).

| Component | Default model | Override env var |
|-----------|---------------|------------------|
| LLM | (none — `MODEL_ID` required) | `MODEL_ID` |
| Embeddings | amazon.titan-embed-text-v2:0 | `EMBEDDING_DIMENSIONS` |

Embedding dimensions default to 1024. Titan Text Embeddings V2 supports 256, 512, or 1024; 1024 matches the existing vector indexes.

## Architecture

- **AWS Bedrock** — LLM (Claude) and embeddings (Titan)
- **neo4j-graphrag-python** — Graph retrieval capabilities
- **Neo4j** — Graph database with vector search

## File Structure

```
financial_data_load/
├── pyproject.toml          # Dependencies (uv sync)
├── main.py                 # CLI entry point (load, cleanse, apply-cleanse, finalize, etc.)
├── test_solutions.sh       # Test runner for workshop solutions
├── run_cleanse.sh          # Dev script: full load-to-finalize pipeline against an env file
├── run_all_configs.sh      # Dev script: run all entity-resolution configs and compare
├── financial-data/         # SEC 10-K data files
│   ├── Company_Filings.csv
│   ├── Asset_Manager_Holdings.csv
│   └── form10k-sample/     # PDF files (8 companies)
├── backups/               # Full database backups (JSON, git-ignored)
├── snapshots/              # Entity snapshots (JSON, git-ignored)
├── plans/                  # Cleanse plans, merge plans, normalization JSON
├── logs/                   # Data load text logs
├── src/                    # Data loader modules
│   ├── config.py           # Settings, Neo4j connection, Bedrock LLM/embedder factories
│   ├── models.py           # Shared Pydantic models (entities, plans, decisions)
│   ├── schema.py           # Graph schema, constraints, indexes
│   ├── loader.py           # CSV loading, company/asset manager nodes
│   ├── pipeline.py         # SimpleKGPipeline, PDF processing
│   ├── cleanse.py          # Cleanse orchestrator (plan generation + execution)
│   ├── validate.py         # LLM entity validation (marks invalid entities for removal)
│   ├── entity_resolution.py # LLM-based entity resolution (dedup with per-label configs)
│   ├── normalize.py        # LLM description normalization (cleans up text in place)
│   ├── snapshot.py         # Entity snapshot export (Neo4j → JSON)
│   ├── compare.py          # Compare resolution runs, ground truth scoring
│   ├── model_compare.py    # Export/compare graph extraction snapshots across LLMs
│   ├── backup.py           # Full database backup and restore
│   ├── samples.py          # Sample queries
│   └── embeddings/         # Embedding provider
│       ├── __init__.py     # get_embedder(), get_embedding_dimensions()
│       └── bedrock.py      # AWS Bedrock (Titan via neo4j-graphrag)
└── solution_srcs/          # Workshop solution + test scripts
    ├── config.py           # Shared config for solutions
    ├── test_connection.py  # Connection test helper
    └── ...                 # 01_/03_/04_/05_/06_ solution and test scripts
```

## Environment Variables

```bash
# Neo4j Database Connection
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# AWS Bedrock
AWS_REGION=us-east-1
MODEL_ID=us.anthropic.claude-sonnet-4-6
# EMBEDDING_DIMENSIONS=1024                               # optional (default: 1024)
```

### Env files

Several `.env` variants live at the project root:

| File | Tracked | Purpose |
|------|---------|---------|
| `.env` | No | Your active config, read by `main.py` and `src/config.py`. |
| `.env.sample` | Yes | Template. Copy to `.env` and fill in credentials. |
| `.env.gold` | No | Credentials fixture for `test_solutions.sh` (the "gold" workshop instance). |
| `.env.final` | No | Credentials fixture for the `run_cleanse.sh` end-to-end pipeline. |

Only `.env.sample` is committed. `.env`, `.env.gold`, and `.env.final` hold real credentials and are git-ignored. Passing an env file to `test_solutions.sh` or `run_cleanse.sh` sources it into that command's environment; it does not modify your `.env`.

## Entity Resolution Experimentation Results

We tested 10 entity resolution configs across 4 groups against a ground truth of 6 expected merges and 5 forbidden merges (11 checks total). The dataset is 618 Company entities (181 unique names) extracted from 8 SEC 10-K filings.

### Config Comparison

| Config | Strategy | Threshold | Confidence | Candidates | LLM Merges | Score |
|--------|----------|-----------|------------|----------:|----------:|---------:|
| baseline | fuzzy | 0.6 | binary | 914 | 29 | **11/11** |
| wide-net | fuzzy | 0.5 | binary | 1,689 | 34 | **11/11** |
| tight-filter | fuzzy | 0.7 | binary | 604 | 26 | **11/11** |
| scored-standard | fuzzy | 0.6 | scored@0.8 | 914 | 28 | **11/11** |
| wide-scored | fuzzy | 0.5 | scored@0.8 | 1,689 | 32 | **11/11** |
| **prefix-loose** | **prefix** | **0.3** | **binary** | **28** | **19** | **11/11** |
| scored-strict | fuzzy | 0.6 | scored@0.9 | 914 | 24 | 10/11 |
| prefix-standard | prefix | 0.5 | binary | 18 | 13 | 8/11 |
| very-wide | fuzzy | 0.4 | binary | 5,602 | 13 | 7/11 |

### Findings

**Winner: `prefix` strategy at threshold 0.3.** Scored 11/11 with only 28 candidate pairs — roughly 3% of what the baseline fuzzy config generates. This means ~30x fewer LLM calls for the same ground truth result. It found 14 LLM merge groups (vs 18 for fuzzy), so it misses 4 lower-value matches, but all 6 expected merges passed and all 5 forbidden merges were correctly avoided.

**Key observations:**

- **The LLM is the quality gate, not the pre-filter.** All fuzzy configs from 0.5-0.7 scored identically despite 3x difference in candidate volume. The LLM correctly rejected noise regardless of how much the pre-filter sent.
- **Too wide hurts.** Fuzzy at 0.4 generated 5,602 candidates and paradoxically found fewer merges (13 vs 29). The LLM appears to degrade when batches are dominated by obvious non-matches.
- **Scored mode at 0.9 is too strict.** It dropped Amazon (a correct merge the LLM confirmed with <0.9 confidence). The 0.8 threshold worked identically to binary mode.
- **Prefix at 0.5 is too strict.** "Microsoft" is a prefix of "Microsoft Corporation", but the length ratio (9/23 = 0.39) fails the 0.5 threshold. The 0.3 threshold captures these.

### Recommended Pipeline

```bash
uv run python main.py restore
uv run python main.py cleanse
uv run python main.py apply-cleanse
uv run python main.py finalize
uv run python main.py verify
```

## Pipeline Performance: Range Indexes

The `load` command creates temporary **range indexes** before processing PDFs. These are dropped during `finalize` when uniqueness constraints (which include their own backing indexes) take over.

### Why indexes speed up writes

Without an index, every `MERGE` does a full label scan — O(n) per write, and n grows with each PDF. With an index, each `MERGE` is an O(log n) lookup plus a small index update. The scan cost grows quadratically across the pipeline run; the index maintenance cost is near-constant.

The net effect is indexes make the pipeline significantly **faster** for writes, not slower. Index overhead only becomes a concern for bulk `LOAD CSV` or `UNWIND` batch imports where you already have a way to avoid `MERGE`, which isn't the case here — `SimpleKGPipeline` issues individual `MERGE` statements per entity.

### What is a range index?

In Neo4j, a **range index** (created with `CREATE INDEX ... FOR (n:Label) ON (n.property)`) is the standard B-tree index for property lookups. It speeds up equality checks (`WHERE n.name = $value`), range comparisons (`<`, `>`), prefix matching, and — critically — `MERGE` operations that need to find-or-create a node by property value.

A **uniqueness constraint** (`CREATE CONSTRAINT ... REQUIRE n.prop IS UNIQUE`) automatically creates a backing range index *plus* enforces that no two nodes share the same value. During the pipeline run we can't use uniqueness constraints because `SimpleKGPipeline` may create duplicate entities across chunks that get resolved later. So we use plain range indexes for the MERGE speedup without the uniqueness enforcement, then swap to constraints in the `finalize` step.

## Seed Data Export (Admin)

The pipeline above builds a live graph from the raw PDFs in `financial-data/`. The distributable **seed data** that participants load in Lab 1 lives in `seed-data/` — the filtered, exported snapshot of that graph. Regenerating it is an admin-only workflow; participants never run it, they only load the CloudFront-hosted copies. Uploading the seed data to S3/CloudFront is handled by `setup/setup_s3_seed_data.sh` (see [`../setup/README.md`](../setup/README.md)).

The `seed-data/` files are the source of truth for the SEC 10-K knowledge graph — both the structured CSVs and `chunks.csv`/`chunks.jsonl` (chunks with Titan embeddings).

### `export_seed_data/export.py` — Export the graph to `seed-data/`

Exports the full knowledge graph from a live Neo4j instance to `../seed-data/`:

- **Structured layer**: companies, products, risk factors, financial metrics, asset managers, and documents, plus their relationship and junction tables (OFFERS, FACES_RISK, REPORTS, OWNS, COMPETES_WITH, PARTNERS_WITH, FILED).
- **Unstructured layer**: chunks with Titan embeddings (`chunks.jsonl`) and their FROM_DOCUMENT, NEXT_CHUNK, and FROM_CHUNK relationships.

The export filters to filing companies, those with a `FILED` relationship to a `Document` node, and their directly connected entities. Stable string IDs are assigned per node (`C001`, `P001`, `CH001`, etc.) so the CSVs are portable across databases.

```bash
cd financial_data_load/export_seed_data
uv run export.py
```

Reads Neo4j credentials from `financial_data_load/.env` and writes all output to `financial_data_load/seed-data/`.

### `chunks_jsonl_to_csv.py` — Convert chunks to CSV for Lab 1

Lab 1 loads chunks via `LOAD CSV`, so the exported `chunks.jsonl` must be converted to `chunks.csv`. Each row carries its embedding as a semicolon-delimited float string, which the Lab 1 Cypher rebuilds with `split()`/`toFloat()` (no APOC required).

```bash
cd financial_data_load
python chunks_jsonl_to_csv.py
```

Writes `financial_data_load/seed-data/chunks.csv` (~9 MB, 346 rows). Re-run this whenever `chunks.jsonl` changes.

### `regenerate_titan_embeddings.py` — Regenerate seed embeddings with Titan

Regenerates the stored `seed-data/chunks.jsonl` vectors with Amazon Titan Text Embeddings V2 so they stay in the same vector space as the query-time embedder.

```bash
uv run financial_data_load/regenerate_titan_embeddings.py [--region us-east-1]
```

### `export_seed_data/load-data.py` — Load the full graph from `seed-data/`

Standalone loader that builds the complete knowledge graph from the local `seed-data/` files and keeps it. It mirrors the Cypher in Lab 1's README (constraints, nodes, relationships, chunks, vector index, chunk links, fulltext index), reading local CSV / JSONL via `UNWIND` instead of `LOAD CSV` from CloudFront:

- **Structured layer**: companies, products, risk factors, asset managers, documents, financial metrics, and their relationships (OFFERS, FACES_RISK, OWNS, COMPETES_WITH, PARTNERS_WITH, FILED, REPORTS).
- **Unstructured layer**: all chunks with Titan embeddings (`chunks.jsonl`), the `chunkEmbeddings` vector index, and the FROM_DOCUMENT, NEXT_CHUNK, and FROM_CHUNK links.

After loading it prints node/relationship counts and index states for verification.

```bash
cd financial_data_load/export_seed_data
uv run load-data.py                    # load into .env target (confirm before clearing)
uv run load-data.py --yes              # skip the clear confirmation
uv run load-data.py --no-clear         # load without wiping first (MERGE is idempotent)
uv run load-data.py --env ../.env.gold # load into a different instance
```

Reads Neo4j credentials from `financial_data_load/.env` by default (`--env` overrides). The target database is cleared first unless `--no-clear` is given; clearing prompts for confirmation unless `--yes` is passed.

## Cleanup

No infrastructure to tear down — Bedrock uses on-demand API access.
