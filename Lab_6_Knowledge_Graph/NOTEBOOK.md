# Running Jupyter Notebooks on AWS (2025)

This guide covers the latest AWS options for running Jupyter notebooks and provides recommendations for this workshop.

## Overview

AWS offers several options for running Jupyter notebooks. The two main platforms are:

1. **Amazon SageMaker AI** - The ML/AI-focused notebook environment
2. **Amazon SageMaker Unified Studio** - The new unified data + analytics + AI platform

---

## Option 1: Amazon SageMaker AI (JupyterLab in Studio) ⭐ RECOMMENDED

**What it is:** The core ML/AI-focused notebook environment within SageMaker Studio.

### Key Features

- Launches fully managed JupyterLab in **seconds**
- Pre-configured with PyTorch, TensorFlow, Keras, NumPy, pandas, scikit-learn
- Private and shared spaces for real-time collaboration
- Single EC2 instance + EBS volume per space (easy to understand pricing)
- Built-in Amazon Q Developer for code assistance
- Supports JupyterLab 4 (JupyterLab 1 and 3 deprecated as of June 30, 2025)

### Setup Complexity

**Low-Medium**

1. Create a SageMaker domain
2. Create a JupyterLab space
3. Clone your workshop repo

### Best For

ML/AI-focused workshops, model development, embeddings work

---

## Option 2: Amazon SageMaker Unified Studio

**What it is:** The new unified platform (GA March 2025) that combines data, analytics, and AI/ML services.

### Key Features

- Integrates EMR, Glue, Athena, Redshift, Bedrock, and SageMaker AI
- New notebook experience (November 2025) with built-in AI agent (Data Agent)
- Multi-service, poly-compute notebooks (switch between Python, Spark, SQL per cell)
- Project-based collaboration model
- One-click onboarding (November 2025)

### Drawbacks

- More complex domain/project setup
- 10,000-row SQL query limitation in JupyterLab (requires workarounds)
- Still relatively new (more potential rough edges)
- Overkill if you don't need data integration features

### Setup Complexity

**Medium-High** - Requires configuring domains, projects, and compute connections

### Best For

Teams needing unified data + analytics + ML in one place

---

## Option 3: SageMaker Studio Lab (Free)

**What it is:** A free, no-AWS-account-required notebook environment.

### Key Features

- **No AWS account or credit card required**
- Free CPU (T3.xlarge, 12hr sessions) and GPU (G4dn.xlarge, 4hr sessions)
- 15GB persistent storage
- JupyterLab 4

### Limitations

- 4hr GPU sessions / 8hr total GPU per day
- **Cannot easily access AWS services** (Bedrock, etc.) without manual credential setup
- Subset of Studio capabilities
- No SageMaker Pipelines, GroundTruth, etc.

### Best For

Individual learners - **not suitable for workshops using AWS services like Bedrock**

---

## Recommendation for This Workshop

For this **Knowledge Graph workshop**, we recommend **SageMaker AI (JupyterLab in Studio)**.

### Workshop Requirements

These notebooks use:
- **Neo4j** (external graph database)
- **Amazon Bedrock** (Titan Embeddings V2, Claude)
- Standard Python packages (neo4j driver, langchain)

They do **NOT** need: EMR, Glue, Athena, or Redshift data integration

### Comparison

| Factor | SageMaker AI | Unified Studio |
|--------|-------------|----------------|
| **Setup time** | 5-10 minutes | 30+ minutes |
| **Complexity** | Low | Medium-High |
| **Launch speed** | Seconds | Seconds |
| **Workshop readiness** | Battle-tested | Still maturing |
| **Documentation** | Extensive | Growing |
| **Features needed** | All covered | Overkill |
| **Cost transparency** | Simple EC2 pricing | More complex |

### Why NOT Unified Studio for This Workshop

1. **Overkill** - You don't need multi-service data integration
2. **Added complexity** - Project-based model adds setup overhead
3. **Still maturing** - GA only since March 2025
4. **10k row limitation** - SQL query limitations (though not critical here)

### When Unified Studio Would Make Sense

- Labs that pull data from Redshift/Athena for GraphRAG
- Attendees should experience the new Data Agent features
- Workshop is part of a larger data + analytics curriculum

---

## Quick Start: SageMaker AI Setup

### Recommended Configuration

| Setting | Value |
|---------|-------|
| **Instance type** | `ml.t3.medium` (minimum cost, sufficient for this workshop) |
| **Platform** | `notebook-al2023-v1` (Amazon Linux 2023, JupyterLab 4) |
| **Storage** | 20GB EBS (default) |
| **Region** | `us-east-1` or `us-west-2` (best Bedrock model availability) |

### Step-by-Step Setup

1. **Open SageMaker Console**
   - Navigate to [Amazon SageMaker](https://console.aws.amazon.com/sagemaker/)
   - Select your preferred region (us-east-1 recommended)

2. **Create a Domain** (if you don't have one)
   - Click "Domains" in the left navigation
   - Click "Create domain"
   - Choose "Quick setup" for fastest configuration
   - Wait for domain creation (2-5 minutes)

3. **Launch Studio**
   - Click on your domain
   - Click "Launch" → "Studio"

4. **Create a JupyterLab Space**
   - In Studio, click "JupyterLab" in the left navigation
   - Click "Create JupyterLab space"
   - Name it (e.g., "neo4j-workshop")
   - Select instance type: `ml.t3.medium`
   - Click "Run space"

5. **Clone the Workshop Repository**
   ```bash
   # In JupyterLab terminal
   git clone <your-workshop-repo-url>
   cd lab-neo4j-aws/Lab_6_Knowledge_Graph
   ```

6. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

7. **Configure Environment**
   - Create a `.env` file with your Neo4j and AWS credentials
   - Ensure Bedrock model access is enabled in your account

### Cost Estimates

| Instance | Hourly Cost | 4-Hour Workshop |
|----------|-------------|-----------------|
| ml.t3.medium | ~$0.05/hr | ~$0.20 |
| ml.t3.large | ~$0.10/hr | ~$0.40 |
| ml.m5.large | ~$0.12/hr | ~$0.48 |

> **Tip:** Remember to stop your JupyterLab space when not in use to avoid charges.

---

## References

### SageMaker AI Documentation
- [SageMaker AI Notebooks Overview](https://aws.amazon.com/sagemaker/ai/notebooks/)
- [SageMaker JupyterLab Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-jl.html)
- [JupyterLab User Guide](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-jl-user-guide.html)

### SageMaker Unified Studio Documentation
- [Unified Studio Overview](https://aws.amazon.com/sagemaker/unified-studio/)
- [What is SageMaker Unified Studio](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/what-is-sagemaker-unified-studio.html)
- [Unified Studio Notebooks](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/notebooks.html)
- [Unified Studio JupyterLab](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/jupyterlab.html)

### Additional Resources
- [SageMaker Studio Lab](https://studiolab.sagemaker.aws/)
- [Studio vs Notebook Instances Comparison](https://docs.aws.amazon.com/sagemaker/latest/dg/notebooks-comparison.html)
- [SageMaker Workshop Repository](https://github.com/aws-samples/amazon-sagemaker-from-idea-to-production)
