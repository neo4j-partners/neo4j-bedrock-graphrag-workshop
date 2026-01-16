# Lab 5 - Start Codespace

In this lab, you will spin up a GitHub Codespace instance to use as your development environment for the coding labs in Part 2 of the workshop.

## Prerequisites

Before starting, make sure you have:
- Your **AWS credentials** (Access Key ID, Secret Access Key) from Lab 0
- Your **Neo4j Aura credentials** (URI, username, password) from Lab 1
- Model access enabled in **Amazon Bedrock** from Lab 3

## Launch the Codespace

Click the button below to start your development environment:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/your-org/lab-neo4j-aws)

## What is a GitHub Codespace?

A GitHub Codespace is a cloud-hosted development environment that runs in your browser. When you launch a Codespace, GitHub provisions a virtual machine with:

- A pre-configured VS Code editor
- All required tools and dependencies already installed (Python, AWS CLI, AWS CDK)
- Extensions for AWS development, Python, and Jupyter notebooks
- A terminal with access to run commands

This means you don't need to install anything on your local machine—everything is ready to go in the cloud.

## Setup

Once your Codespace has started, follow these steps to configure your environment.

### Step 1: Configure AWS Credentials

Open a terminal and run:

```bash
aws configure
```

Enter the following when prompted:

| Prompt | Value |
|--------|-------|
| AWS Access Key ID | Your access key from Lab 0 |
| AWS Secret Access Key | Your secret key from Lab 0 |
| Default region name | `us-east-1` |
| Default output format | `json` |

### Step 2: Verify AWS Access

Test your AWS credentials:

```bash
aws sts get-caller-identity
```

You should see output with your AWS account ID and user ARN.

### Step 3: Verify Bedrock Access

Test that you can access Amazon Bedrock:

```bash
aws bedrock list-foundation-models --query "modelSummaries[?contains(modelId, 'titan-embed')].modelId" --output table
```

You should see the Titan embedding models listed.

### Step 4: Configure Neo4j Credentials

1. Copy the sample environment file:

```bash
cp .env.sample .env
```

2. Edit the `.env` file with your Neo4j credentials:

```bash
code .env
```

Update the following values with your credentials from Lab 1:

```
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password-here
```

### Step 5: Install Python Dependencies

The Codespace should automatically install dependencies, but if needed:

```bash
pip install -e .
```

### Step 6: Verify Neo4j Connection

Test your Neo4j connection by running:

```bash
python -c "
from config import get_neo4j_driver
driver = get_neo4j_driver()
driver.verify_connectivity()
print('Connected to Neo4j successfully!')
driver.close()
"
```

---

## (Optional) Deploy AWS Infrastructure with CDK

For advanced users, you can deploy the AWS infrastructure using CDK.

### Deploy the Stacks

```bash
cd infra/cdk
npm install
cdk bootstrap  # Only needed once per account/region
cdk deploy --all
```

### Sync CDK Outputs to Environment

After deployment, sync the outputs to your `.env` file:

```bash
cd ../..
python setup_env.py
```

---

## Running the Notebooks

To run the Jupyter notebooks in the labs:

### Step 1: Select the Python Kernel

1. Open a notebook file (e.g., `Lab_6_Knowledge_Graph/01_data_loading.ipynb`)
2. Click **Select Kernel** in the top right of the notebook
3. Select **Python Environments...**

![Select Kernel](images/select_kernel.png)

4. Choose the **lab-neo4j-aws** environment (or `.venv` if using uv)

![Select Environment](images/select_environment.png)

### Step 2: Run Notebook Cells

- Press `Shift+Enter` to run a cell and move to the next
- Press `Ctrl+Enter` to run a cell without moving
- Use the **Run All** button to run all cells

---

## Alternative: Run GitHub Codespace in VS Code

If you prefer to run the Codespace in VS Code on your local machine:

1. Install [Visual Studio Code](https://code.visualstudio.com/)
2. Install the [GitHub Codespaces extension](https://marketplace.visualstudio.com/items?itemName=GitHub.codespaces)
3. Sign in to GitHub from VS Code
4. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
5. Run "Codespaces: Connect to Codespace"
6. Select your running Codespace

For detailed instructions, see GitHub's official documentation: [Using GitHub Codespaces in Visual Studio Code](https://docs.github.com/en/codespaces/developing-in-a-codespace/using-github-codespaces-in-visual-studio-code)

---

## Running Locally (Without a Codespace)

If you prefer to run the workshop on your local machine:

### Prerequisites

- Windows 10/11, macOS, or Linux
- Administrator access on your machine
- An AWS account with Bedrock access
- Neo4j Aura credentials from Lab 1

### Step 1: Install Required Tools

**Python 3.11+:**
- Download from https://www.python.org/downloads/
- Verify: `python --version`

**AWS CLI v2:**
- Windows: `winget install Amazon.AWSCLI`
- macOS: `brew install awscli`
- Linux: See [AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

**Node.js (for CDK, optional):**
- Download from https://nodejs.org/

### Step 2: Clone the Repository

```bash
git clone https://github.com/your-org/lab-neo4j-aws.git
cd lab-neo4j-aws
```

### Step 3: Create Python Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Step 4: Configure Environment Variables

```bash
cp .env.sample .env
# Edit .env with your credentials
```

### Step 5: Configure AWS

```bash
aws configure
```

### Step 6: Run the Notebooks

1. Start Jupyter:
```bash
jupyter notebook
```

2. Open a browser to the URL shown in the terminal
3. Navigate to the lab folder and open a notebook

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `aws: command not found` | AWS CLI not installed or not in PATH |
| `boto3.exceptions.NoCredentialsError` | Run `aws configure` to set credentials |
| `Neo4j connection refused` | Check URI format and password in `.env` |
| `Bedrock access denied` | Verify model access is enabled in Bedrock console |
| `Jupyter kernel not found` | Run `pip install -e .` and restart VS Code |
| `Import errors in notebooks` | Ensure you selected the correct Python interpreter |
| `CDK bootstrap failed` | Check AWS credentials and region |

### Common AWS Issues

**"UnauthorizedAccessException" when calling Bedrock:**
- Verify your IAM user has `bedrock:InvokeModel` permissions
- Check that model access is enabled in the Bedrock console

**"ResourceNotFoundException" for models:**
- Ensure you're in a supported region (us-east-1 recommended)
- Verify the model ID matches an enabled model

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` |
| `AWS_BEDROCK_MODEL_ID` | Claude model for LLM tasks | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `AWS_BEDROCK_EMBEDDING_MODEL_ID` | Titan model for embeddings | `amazon.titan-embed-text-v2:0` |
| `EMBEDDING_DIMENSIONS` | Vector dimensions (256, 512, 1024) | `1024` |
| `NEO4J_URI` | Neo4j Aura connection string | `neo4j+s://xxx.databases.neo4j.io` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `your-password` |
| `NEO4J_VECTOR_INDEX_NAME` | Vector index name | `chunkEmbeddings` |

---

## Next Steps

After completing this lab, continue to [Lab 6 - Building a Knowledge Graph](../Lab_6_Knowledge_Graph/) to build your knowledge graph from SEC filings using entity extraction and embeddings.
