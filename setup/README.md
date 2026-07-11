# Financial/SEC Workshop Setup Tools

CLI tools and admin scripts for the GraphRAG workshop.

See [Regenerating Seed Data](#regenerating-seed-data) for how the `seed-data/` files are produced from a live Neo4j graph.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Neo4j Aura instance (from Lab 1)
- AWS credentials configured with admin access
- `CONFIG.txt` at the repository root with Neo4j and Bedrock credentials

## Admin Setup (Run Before the Workshop)

These steps must be completed by the workshop admin before participants begin.

### 1. Enable Bedrock Model Access

In the AWS Console, navigate to **Amazon Bedrock > Model access** and enable:
- `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (or your preferred Claude model)
- `amazon.titan-embed-text-v2:0`

This is a manual console step and cannot be scripted.

### 2. Set Up AgentCore IAM & Resources (Lab 3 Deployment)

Lab 3's AgentCore deployment requires IAM roles, an S3 bucket, and a deployment policy. This is a **two-step process** because SageMaker execution roles are auto-created when participants set up their domains (Quick Setup), so the admin cannot attach policies to roles that don't exist yet.

**Step 2a — Run before the workshop:**

```bash
cd setup
./setup_agentcore.sh
```

This creates:
- **AgentCore execution role** — `AmazonBedrockAgentCoreLabRuntime-{region}`, the IAM role that deployed agents assume at runtime (Bedrock model access, CloudWatch, X-Ray)
- **S3 bucket** — `bedrock-agentcore-codebuild-sources-{account}-{region}`, used to upload agent code during deployment
- **Managed IAM policy** — `BedrockAgentCoreLabDeployPolicy`, a customer-managed policy granting AgentCore API access, IAM role management (scoped to `*BedrockAgentCore*` roles), `iam:PassRole`, and S3 access

To specify a different region:
```bash
./setup_agentcore.sh --region us-west-2
```

**Step 2b — Run after participants create their SageMaker domains:**

```bash
./grant_sagemaker_access.sh
```

This finds all `AmazonSageMaker-ExecutionRole-*` roles in the account and attaches the managed policy created in Step 2a. The script is idempotent — re-run it whenever new participants join. If a participant hits a permissions error in Lab 3, this is the fix.

See [sagemaker-roles.md](sagemaker-roles.md) for a detailed explanation of the timing issue.

### 3. Update CONFIG.txt

Ensure the following fields are set in `CONFIG.txt` before distributing to participants:

| Field | Source | Required By |
|-------|--------|-------------|
| `NEO4J_URI` | Lab 1 — Aura instance creation | Labs 1, 2, 4, 6 |
| `NEO4J_USERNAME` | Lab 1 — Aura instance creation | Labs 1, 2, 4, 6 |
| `NEO4J_PASSWORD` | Lab 1 — Aura instance creation | Labs 1, 2, 4, 6 |
| `MODEL_ID` | Pre-configured default | Labs 3, 4, 5, 6 |
| `EMBEDDING_DIMENSIONS` | Pre-configured default (1024) | Labs 4, 6 |
| `REGION` | Pre-configured default | Labs 3, 4, 5, 6 |
| `MCP_GATEWAY_URL` | MCP server deployment | Lab 5 |
| `MCP_ACCESS_TOKEN` | MCP server deployment | Lab 5 |

### 4. SageMaker Lifecycle Configuration (Optional)

If the admin pre-creates SageMaker domains for participants, a lifecycle configuration script can pre-install packages and tools so notebooks run faster. If participants create their own domains, this cannot be auto-attached — the `%pip install` cells in each notebook handle dependencies instead.

Example lifecycle config script for JupyterLab (attach to the Space's default app):
```bash
#!/bin/bash
set -eux
# Install zip (required by agentcore deploy)
apt-get update -qq && apt-get install -y -qq zip
# Pre-install common workshop packages
pip install -q langgraph langchain-aws langchain-mcp-adapters mcp nest-asyncio \
    bedrock-agentcore-starter-toolkit bedrock-agentcore pyyaml
```

### 5. Cleanup

To remove all resources created by the setup scripts:

```bash
./setup_agentcore.sh --cleanup
```

This detaches the deployment policy from all SageMaker roles, deletes the managed policy, deletes the execution role, and removes the S3 bucket.

---

## Regenerating Seed Data

The workshop's `seed-data/` files are the source of truth for the SEC 10-K knowledge graph. Participants load them in Lab 1 with `LOAD CSV` from the CloudFront-hosted copies — both the structured CSVs and `chunks.csv` (chunks with embeddings). The `export_seed_data/` directory holds the tooling that produces and verifies those files from a live Neo4j graph.

This is an admin-only workflow. Participants never run it; they only load the hosted `seed-data/` files via Lab 1's Cypher.

### `export.py` — Export the graph to `seed-data/`

Exports the full knowledge graph from a live Neo4j instance to `../seed-data/`:

- **Structured layer**: companies, products, risk factors, financial metrics, asset managers, and documents, plus their relationship and junction tables (OFFERS, FACES_RISK, REPORTS, OWNS, COMPETES_WITH, PARTNERS_WITH, FILED).
- **Unstructured layer**: chunks with Titan embeddings (`chunks.jsonl`) and their FROM_DOCUMENT, NEXT_CHUNK, and FROM_CHUNK relationships.

The export filters to filing companies, those with a `FILED` relationship to a `Document` node, and their directly connected entities. Stable string IDs are assigned per node (`C001`, `P001`, `CH001`, etc.) so the CSVs are portable across databases.

```bash
cd setup/export_seed_data
uv run export.py
```

Reads Neo4j credentials from `setup/.env` and writes all output to `setup/seed-data/`.

### `chunks_jsonl_to_csv.py` — Convert chunks to CSV for Lab 1

Lab 1 loads chunks via `LOAD CSV`, so the exported `chunks.jsonl` must be converted to `chunks.csv`. Each row carries its embedding as a semicolon-delimited float string, which the Lab 1 Cypher rebuilds with `split()`/`toFloat()` (no APOC required).

```bash
cd setup
python chunks_jsonl_to_csv.py
```

Writes `setup/seed-data/chunks.csv` (~9 MB, 346 rows). Re-run this whenever `chunks.jsonl` changes.

### Host seed data on S3/CloudFront

Lab 1's Cypher reads every seed file from CloudFront, so the CSVs must be uploaded. `setup_s3_seed_data.sh` creates a private S3 bucket fronted by CloudFront (OAC) and uploads every `*.csv` in `seed-data/` — including `chunks.csv` and the chunk-relationship files (`chunk_documents.csv`, `chunk_sequence.csv`, `entity_chunks.csv`).

```bash
cd setup
./setup_s3_seed_data.sh              # first-time: create bucket + CloudFront, upload CSVs
./setup_s3_seed_data.sh --refresh    # re-upload CSVs and invalidate the CloudFront cache
```

After regenerating any seed file (including `chunks.csv`), run `--refresh` so participants load the current data. The base URL it prints must match the `https://…cloudfront.net/sec-filings/` prefix used in `Lab_1_Aura_Setup/README.md`.

### `test_load.py` — Verify the structured load

Loads the structured CSVs into a clean database using the same Cypher pattern as Lab 1's README (constraints, nodes, relationships, fulltext index), reading local CSVs via `UNWIND` instead of `LOAD CSV` from CloudFront. Confirms the committed CSVs load cleanly before distribution.

```bash
cd setup/export_seed_data
uv run test_load.py
```

### `test_roundtrip.py` — Verify the full load path

Round-trip test that loads every seed file (`chunks.jsonl` + `chunk_documents.csv` + `chunk_sequence.csv` + `entity_chunks.csv`), reads the data back, and verifies it matches. Exercises the complete load path including embeddings.

```bash
cd setup/export_seed_data
uv run test_roundtrip.py
```

Both test scripts use the empty test database configured in `setup/.env.gold`, keeping the production Aura instance untouched.

---
