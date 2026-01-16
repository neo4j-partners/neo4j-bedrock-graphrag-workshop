# Development Environment Guide

This guide explains how to set up your development environment for the Neo4j and AWS Bedrock workshop using GitHub Codespaces.

## Option 1: GitHub Codespaces (Recommended)

GitHub Codespaces provides a cloud-based development environment with all tools pre-installed.

### Step 1: Launch Codespace

1. Navigate to this repository on GitHub
2. Click the green **Code** button
3. Select the **Codespaces** tab
4. Click **Create codespace on main**

The codespace will take a few minutes to build on first launch.

### Step 2: Configure Secrets (Recommended)

For a seamless experience, configure your secrets in GitHub before launching the codespace:

1. Go to your GitHub account **Settings** > **Codespaces** > **Secrets**
2. Add the following secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | `wJalrXU...` |
| `NEO4J_URI` | Neo4j Aura connection URI | `neo4j+s://abc123.databases.neo4j.io` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `your-password` |

These secrets will automatically populate your `.env` file when the codespace starts.

### Step 3: Verify Configuration

Once your codespace is running, verify your configuration:

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check Bedrock model access
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[?contains(modelId, `claude`)].modelId'

# Check Neo4j connection
python -c "from config import get_neo4j_driver; d = get_neo4j_driver(); print(d.verify_connectivity())"
```

## Option 2: Local Development

If you prefer to work locally, follow these steps:

### Prerequisites

- Python 3.11 or 3.12
- Node.js 18+ (for AWS CDK)
- AWS CLI v2
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/lab-neo4j-aws.git
cd lab-neo4j-aws
```

### Step 2: Install Dependencies

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv sync

# Install AWS CDK
npm install -g aws-cdk
```

### Step 3: Configure AWS Credentials

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `us-east-1` (recommended)
- Output format: `json`

### Step 4: Configure Environment

```bash
# Copy sample environment file
cp .env.sample .env

# Edit .env with your Neo4j credentials
# NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
# NEO4J_USERNAME=neo4j
# NEO4J_PASSWORD=your-password
```

### Step 5: Verify Setup

```bash
# Verify AWS access
aws sts get-caller-identity

# Run setup script
python setup_env.py
```

## AWS Credentials

### Option A: IAM User Credentials

For workshop participants, you may receive IAM user credentials:

1. Sign in to AWS Console with provided credentials
2. Navigate to **IAM** > **Users** > **Your User** > **Security credentials**
3. Create access keys for CLI access
4. Configure with `aws configure`

### Option B: AWS SSO (For organizations)

If your organization uses AWS SSO:

```bash
aws configure sso
# Follow the prompts to authenticate
```

### Option C: Environment Variables

Set credentials directly in your environment:

```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1
```

## Enabling Bedrock Model Access

Before using Bedrock models, you must enable access:

1. Sign in to AWS Console
2. Navigate to **Amazon Bedrock**
3. Click **Model access** in the left sidebar
4. Click **Manage model access**
5. Enable the following models:
   - **Amazon Titan Text Embeddings V2** (usually instant)
   - **Anthropic Claude 3.5 Sonnet** (may take a few minutes)
6. Click **Save changes**

## Troubleshooting

### "Access Denied" when calling Bedrock

- Verify model access is enabled in Bedrock console
- Check your IAM user has `bedrock:InvokeModel` permission
- Confirm you're using the correct region

### "Connection refused" for Neo4j

- Verify your Neo4j Aura instance is running
- Check the connection URI format: `neo4j+s://xxx.databases.neo4j.io`
- Confirm username and password are correct

### CDK deployment fails

- Run `cdk bootstrap` first (one-time setup)
- Verify your AWS credentials have CloudFormation permissions
- Check the AWS region matches your configuration

## Next Steps

Once your environment is configured:

1. **Lab 4**: Review this guide and verify your setup
2. **Lab 5**: Start building the knowledge graph
3. **Lab 6**: Explore GraphRAG retrievers
4. **Lab 7**: Build AI agents with Strands SDK
