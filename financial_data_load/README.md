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

The LLM uses the model specified by `MODEL_ID` (required). Embeddings default to Titan Text Embeddings V2 (1024 dimensions) — override with `EMBEDDING_MODEL_ID` if needed.

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
cat logs/cleanse_plan_*.json

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
| `main.py finalize` | Constraints, indexes, asset managers, verify |
| `main.py verify` | Counts + enrichment checks + end-to-end search validation |
| `main.py clean` | Clear all data |
| `main.py samples [--limit N]` | Run sample queries showcasing the graph |
| `main.py snapshot` | Export Company entity snapshot (for standalone resolution testing) |
| `main.py resolve [--snapshot PATH] [--strategy ...] [--threshold ...]` | LLM entity resolution on snapshot (Company only) |
| `main.py compare` | Compare resolution runs, score against ground truth |
| `main.py apply-merges [--plan PATH]` | Apply merge plan from resolve |

### 7. Run Workshop Solutions

```bash
# Interactive menu
uv run python main.py solutions

# Run specific solution
uv run python main.py solutions 4

# Run all (from option 4 onwards)
uv run python main.py solutions A
```

## Workshop Solutions

### Data Pipeline (01_xx)

These solutions build the knowledge graph — **WARNING: they will delete existing data**:

| # | Solution | Description |
|---|----------|-------------|
| 1 | `01_01_data_loading.py` | Load financial documents into Neo4j |
| 2 | `01_02_embeddings.py` | Generate and store vector embeddings |
| 3 | `01_03_entity_extraction.py` | Extract entities and relationships |
| 4 | `01_04_full_dataset_queries.py` | Explore the loaded data |

### Retrievers (02_xx)

GraphRAG patterns using neo4j-graphrag:

| # | Solution | Description |
|---|----------|-------------|
| 5 | `02_01_vector_retriever.py` | Basic vector search |
| 6 | `02_02_vector_cypher_retriever.py` | Vector search + custom Cypher |
| 7 | `02_03_text2cypher_retriever.py` | Natural language to Cypher |

### Agents (03_xx / 05_xx)

Agent patterns:

| # | Solution | Description |
|---|----------|-------------|
| 8 | `05_01_simple_agent.py` | Basic agent with schema tool |
| 9 | `05_02_context_provider.py` | Context provider intro (user info memory) |
| 10 | `03_02_vector_graph_agent.py` | Agent with vector search + graph traversal |
| 11 | `03_03_text2cypher_agent.py` | Multi-tool agent with Text2Cypher |

### Search (05_xx)

Advanced search patterns:

| # | Solution | Description |
|---|----------|-------------|
| 12 | `05_01_fulltext_search.py` | Full-text search capabilities |
| 13 | `05_02_hybrid_search.py` | Hybrid vector + keyword search |

### Context Providers (06_xx)

Neo4j context providers using agent-framework-neo4j:

| # | Solution | Description |
|---|----------|-------------|
| 14 | `06_01_fulltext_context_provider.py` | Fulltext search context provider |
| 15 | `06_02_vector_context_provider.py` | Vector (semantic) search context provider |
| 16 | `06_03_graph_enriched_provider.py` | Vector search + graph traversal context provider |

### Agent Memory (07_xx)

Persistent agent memory using neo4j-agent-memory:

| # | Solution | Description |
|---|----------|-------------|
| 17 | `07_01_memory_context_provider.py` | Memory as a context provider |
| 18 | `07_02_entity_extraction.py` | Entity extraction pipeline |
| 19 | `07_03_memory_tools_agent.py` | Agent with explicit memory tools |
| 20 | `07_04_reasoning_memory.py` | Reasoning memory traces and tool stats |

## AI Provider

Uses `BedrockLLM` and `BedrockEmbeddings` from [neo4j-graphrag-python](https://github.com/neo4j/neo4j-graphrag-python). AWS credentials are resolved by the standard boto3 credential chain (env vars, `~/.aws/credentials`, IAM role).

| Component | Default model | Override env var |
|-----------|---------------|------------------|
| LLM | (none — `MODEL_ID` required) | `MODEL_ID` |
| Embeddings | amazon.titan-embed-text-v2:0 | `EMBEDDING_MODEL_ID` |

Embedding dimensions default to 1024 (Titan v2). Override with `EMBEDDING_DIMENSIONS` if using a different embedding model.

**Why Titan v2 for embeddings instead of Nova?** Amazon Nova Multimodal Embeddings (`amazon.nova-2-multimodal-embeddings-v1:0`) uses an async-only API (`StartAsyncInvoke`) that writes results to S3. This is designed for batch workloads, not real-time per-chunk embedding. The `SimpleKGPipeline` calls `embed_query()` synchronously per chunk, which requires the standard `invoke_model` API that Titan v2 supports.

## Architecture

- **AWS Bedrock** — LLM (Claude) and embeddings (Titan v2)
- **neo4j-graphrag-python** — Graph retrieval capabilities
- **Neo4j** — Graph database with vector search

## File Structure

```
financial_data_load/
├── pyproject.toml          # Dependencies (uv sync)
├── main.py                 # CLI entry point (load, cleanse, apply-cleanse, finalize, etc.)
├── financial-data/         # SEC 10-K data files
│   ├── Company_Filings.csv
│   ├── Asset_Manager_Holdings.csv
│   └── form10k-sample/     # PDF files (8 companies)
├── backups/               # Full database backups (JSON, git-ignored)
├── snapshots/              # Entity snapshots (JSON, git-ignored)
├── logs/                   # Cleanse plans, merge plans, normalization logs
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
│   ├── backup.py           # Full database backup and restore
│   ├── samples.py          # Sample queries
│   └── embeddings/         # Embedding provider
│       ├── __init__.py     # get_embedder(), get_embedding_dimensions()
│       └── bedrock.py      # AWS Bedrock (Titan v2 via neo4j-graphrag)
└── solution_srcs/          # Workshop solution files
    ├── config.py           # Shared config for solutions
    └── ...                 # 01_xx through 07_xx solution scripts
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
# EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0        # optional
# EMBEDDING_DIMENSIONS=1024                               # optional
```

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

## Cleanup

No infrastructure to tear down — Bedrock uses on-demand API access.
