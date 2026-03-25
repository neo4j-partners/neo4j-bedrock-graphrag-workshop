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

To remove all resources created by the setup script:

```bash
./setup_agentcore.sh --cleanup
```

This deletes the execution role, S3 bucket, and removes the deployment policy from SageMaker roles.

---
