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
- `amazon.nova-2-multimodal-embeddings-v1:0`

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
| `NEO4J_URI` | Lab 1 — Aura instance creation | Labs 2, 5, 6 |
| `NEO4J_USERNAME` | Lab 1 — Aura instance creation | Labs 2, 5, 6 |
| `NEO4J_PASSWORD` | Lab 1 — Aura instance creation | Labs 2, 5, 6 |
| `MODEL_ID` | Pre-configured default | Labs 3, 4, 5, 6 |
| `EMBEDDING_DIMENSIONS` | Pre-configured default (1024) | Labs 4, 5 |
| `REGION` | Pre-configured default | Labs 3, 4, 5, 6 |
| `MCP_GATEWAY_URL` | MCP server deployment | Labs 4, 6 |
| `MCP_ACCESS_TOKEN` | MCP server deployment | Labs 4, 6 |

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
