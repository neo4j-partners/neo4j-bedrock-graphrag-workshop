# Financial/SEC Workshop Setup Tools

CLI tools and admin scripts for the GraphRAG workshop.

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

The `setup_agentcore.sh` script creates the IAM roles, S3 bucket, and permissions needed for Lab 3's AgentCore deployment notebook. Run it once per account:

```bash
cd setup
./setup_agentcore.sh
```

This creates:
- **AgentCore execution role** — `AmazonBedrockAgentCoreLabRuntime-{region}`, the IAM role that deployed agents assume at runtime (Bedrock model access, CloudWatch, X-Ray)
- **S3 bucket** — `bedrock-agentcore-codebuild-sources-{account}-{region}`, used to upload agent code during deployment
- **SageMaker role permissions** — Adds an inline policy to all `AmazonSageMaker-ExecutionRole-*` roles granting AgentCore API access, IAM role management (scoped to `*BedrockAgentCore*` roles), `iam:PassRole`, and S3 access. This allows the AgentCore toolkit to create its own execution roles during deployment.

To specify a different region:
```bash
./setup_agentcore.sh --region us-west-2
```

### 3. Update CONFIG.txt

Ensure the following fields are set in `CONFIG.txt` before distributing to participants:

| Field | Source | Required By |
|-------|--------|-------------|
| `NEO4J_URI` | Lab 1 — Aura instance creation | Labs 2, 6, 7, 8 |
| `NEO4J_USERNAME` | Lab 1 — Aura instance creation | Labs 2, 6, 7, 8 |
| `NEO4J_PASSWORD` | Lab 1 — Aura instance creation | Labs 2, 6, 7, 8 |
| `MODEL_ID` | Pre-configured default | Labs 3, 4, 6, 7 |
| `EMBEDDING_MODEL_ID` | Pre-configured default | Labs 4, 6 |
| `REGION` | Pre-configured default | Labs 3, 4, 6, 7 |
| `MCP_GATEWAY_URL` | MCP server deployment | Labs 4, 7 |
| `MCP_ACCESS_TOKEN` | MCP server deployment | Labs 4, 7 |
| `NEO4J_CLIENT_ID` | Lab 8 — Aura Agent setup | Lab 8 |
| `NEO4J_CLIENT_SECRET` | Lab 8 — Aura Agent setup | Lab 8 |
| `NEO4J_AGENT_ENDPOINT` | Lab 8 — Aura Agent setup | Lab 8 |

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

To remove all resources created by the setup script:

```bash
./setup_agentcore.sh --cleanup
```

This deletes the execution role, S3 bucket, and removes the deployment policy from SageMaker roles.

---

## Tools

### populate — Load the Financial Knowledge Graph

Loads structured CSV data from `TransformedData/` into Neo4j as a knowledge graph with companies, products, services, risk factors, financial metrics, executives, asset managers, and SEC filings.

```bash
cd setup/populate
uv run populate-financial-db load        # Full pipeline: constraints, indexes, nodes, relationships, verify
uv run populate-financial-db verify      # Print node and relationship counts
uv run populate-financial-db clean       # Delete all nodes and relationships
uv run populate-financial-db samples     # Run sample Cypher queries
```

### solutions_bedrock — Validate GraphRAG Retrievers

Runs a 6-phase validation of the Lab 6 GraphRAG pipeline: data loading, embeddings, vector retriever, vector-cypher retriever, fulltext search, and hybrid search.

```bash
cd setup/solutions_bedrock
uv run graphrag-validator test           # Run full 6-phase validation
uv run graphrag-validator chat           # Interactive GraphRAG chat (HybridCypherRetriever)
```

## Configuration

Both tools read credentials from `CONFIG.txt` at the repository root (two levels up from each tool directory). The file uses dotenv format:

```
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
REGION=us-east-1
```

## Graph Schema

```
(:Company) -[:OFFERS_PRODUCT]-> (:Product)
(:Company) -[:OFFERS_SERVICE]-> (:Service)
(:Company) -[:FACES_RISK]-> (:RiskFactor)
(:Company) -[:HAS_METRIC]-> (:FinancialMetric)
(:Company) -[:HAS_EXECUTIVE]-> (:Executive)
(:AssetManager) -[:OWNS]-> (:Company)
(:Company) -[:FILED]-> (:Document) <-[:FROM_DOCUMENT]- (:Chunk) -[:NEXT_CHUNK]-> (:Chunk)
```
