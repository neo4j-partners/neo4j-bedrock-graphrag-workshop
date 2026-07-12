# Financial/SEC Workshop Setup Tools

AWS infrastructure and admin scripts for the GraphRAG workshop (AgentCore IAM, SageMaker access, and seed-data hosting on S3/CloudFront).

The seed data itself and the tooling that regenerates it now live in [`../financial_data_load/`](../financial_data_load/README.md). See [Hosting Seed Data on S3/CloudFront](#hosting-seed-data-on-s3cloudfront) for uploading it.

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
- `us.anthropic.claude-sonnet-4-6` (or your preferred Claude model)
- `amazon.titan-embed-text-v2:0`

This is a manual console step and cannot be scripted.

### 2. Set Up AgentCore IAM & Resources (Lab 4 Deployment)

Lab 4's AgentCore deployment requires IAM roles, an S3 bucket, and a deployment policy. This is a **two-step process** because SageMaker execution roles are auto-created when participants set up their domains (Quick Setup), so the admin cannot attach policies to roles that don't exist yet.

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

This finds all `AmazonSageMaker-ExecutionRole-*` roles in the account and attaches the managed policy created in Step 2a. The script is idempotent — re-run it whenever new participants join. If a participant hits a permissions error in Lab 4, this is the fix.

See [sagemaker-roles.md](sagemaker-roles.md) for a detailed explanation of the timing issue.

### 3. Update CONFIG.txt

Ensure the following fields are set in `CONFIG.txt` before distributing to participants:

| Field | Source | Required By |
|-------|--------|-------------|
| `NEO4J_URI` | Lab 1 — Aura instance creation | Labs 1-5 |
| `NEO4J_USERNAME` | Lab 1 — Aura instance creation | Labs 1-5 |
| `NEO4J_PASSWORD` | Lab 1 — Aura instance creation | Labs 1-5 |
| `MODEL_ID` | Pre-configured default | Labs 3, 4, 5, 6 |
| `REGION` | Pre-configured default | Labs 3, 4, 5, 6 |
| `MCP_GATEWAY_URL` | MCP server deployment | Lab 6 |
| `MCP_ACCESS_TOKEN` | MCP server deployment | Lab 6 |

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

## Hosting Seed Data on S3/CloudFront

The workshop's seed data (`financial_data_load/seed-data/`) is the source of truth for the SEC 10-K knowledge graph. Participants load it in Lab 1 with `LOAD CSV` from the CloudFront-hosted copies — both the structured CSVs and `chunks.csv` (chunks with embeddings). Regenerating and exporting that data from a live Neo4j graph is an admin-only workflow documented in [`../financial_data_load/README.md`](../financial_data_load/README.md); participants never run it.

Lab 1's Cypher reads every seed file from CloudFront, so the CSVs must be uploaded. `setup_s3_seed_data.sh` creates a private S3 bucket fronted by CloudFront (OAC) and uploads every `*.csv` in `financial_data_load/seed-data/` — including `chunks.csv` and the chunk-relationship files (`chunk_documents.csv`, `chunk_sequence.csv`, `entity_chunks.csv`).

```bash
cd setup
./setup_s3_seed_data.sh              # first-time: create bucket + CloudFront, upload CSVs
./setup_s3_seed_data.sh --refresh    # re-upload CSVs and invalidate the CloudFront cache
```

After regenerating any seed file (including `chunks.csv`), run `--refresh` so participants load the current data. The base URL it prints must match the `https://…cloudfront.net/sec-filings/` prefix used in `Lab_1_Aura_Setup/README.md`.

---

## Validating Notebooks

`run_notebooks.py` executes the workshop notebooks against a live graph and reports a pass or fail per notebook. It is the local analog of a CI check: each notebook runs end to end under [papermill](https://papermill.readthedocs.io/), and a clean run (no cell raised) counts as a pass. Use it before a workshop to confirm the notebooks still work against the current Neo4j and Bedrock setup.

**The graph must already be loaded.** The runner does no data loading and skips the Lab 2 pipeline notebooks (which wipe and rebuild the graph). It validates only the read, retrieval, agent, and memory notebooks in Labs 3, 4, 5, and 6.

```bash
uv run setup/run_notebooks.py                  # all in-scope labs, default env
uv run setup/run_notebooks.py --labs 4         # a single lab
uv run setup/run_notebooks.py --labs 3,4,6     # a list
uv run setup/run_notebooks.py --labs 4-6       # a range
```

The script is a `uv run` PEP 723 script: `uv` builds and caches its dependency environment on first run, so no separate install step is needed. Every lab dependency is pre-provisioned, and the runner neutralizes each notebook's `%pip`/`!pip` cells in memory before execution. The original notebook files are never modified.

### Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--labs` | all in-scope | Labs to run: `4`, `3,4,6`, or `4-6`. |
| `--env` | root `.env`, else `CONFIG.txt` | Env file whose keys are injected into the environment before the kernel launches. Injected values take precedence over the notebooks' own `load_dotenv`, so no config file is rewritten. |
| `--include-deploy` | off | Also run the deploy notebook (Lab 4 `02`), which has AWS side effects. Off by default. |
| `--timeout` | 600 | Per-cell execution timeout in seconds. |
| `--keep-temp` | off | Keep the prepared and executed temp notebooks for inspection. |

### Behavior

- **MCP notebooks (Lab 6)** are skipped when `MCP_GATEWAY_URL` or `MCP_ACCESS_TOKEN` is missing or still a `your-...` placeholder.
- **Deploy notebooks** are skipped unless `--include-deploy` is passed.
- The runner prints a summary table and exits nonzero if any notebook fails, so it can gate a CI or pre-workshop check.

---
