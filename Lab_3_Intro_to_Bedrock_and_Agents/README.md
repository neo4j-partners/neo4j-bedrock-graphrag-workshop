# Lab 3 - Building AI Agents with Amazon Bedrock and SageMaker

This lab sets up your SageMaker development environment and walks through building a basic AI agent with LangGraph and Amazon Bedrock, then deploys it to AgentCore Runtime.

## What You'll Learn

- How to configure and invoke Amazon Bedrock models from SageMaker notebooks
- The basics of LangGraph agent architecture (nodes, edges, and state)
- How to define tools that an LLM can call
- The ReAct pattern: reasoning and acting in a loop
- How to package and deploy an agent to AgentCore Runtime
- How to invoke a deployed agent via CLI and boto3

## SageMaker Studio Setup

### Step 1: Navigate to SageMaker AI

1. In the AWS Management Console, click the **region selector** in the upper right corner and select **US East (N. Virginia)** / `us-east-1`
2. In the search bar at the top, type `SageMaker`
3. **Important:** Select **Amazon SageMaker AI** from the results (not "Amazon SageMaker" - they are different services!)

![Navigate to SageMaker AI](images/01-naviagte-to-sagemaker-ai.png)

### Step 2: Set up a Domain

1. Verify you see **Amazon SageMaker AI** in the left sidebar (not just "Amazon SageMaker")
2. In the left panel under "Environment configuration", click on **Domains**, then click the **Create domain** button in the top right corner.

   ![SageMaker AI Domains page showing Domains menu and Create domain button](images/A1-Create-Domain.png)

3. Select **Set up for single user (Quick setup)** on the left, then click the **Set up** button. This creates a domain with default settings perfect for getting started.

   ![Set up SageMaker Domain page showing Set up for single user option](images/A2-Setup-Single-User.png)

### Step 3: Open SageMaker Studio

1. Wait while your environment is being set up (this takes 1-2 minutes)
2. You'll see progress indicators for IAM role creation, internet access, encryption, and storage
3. Once setup completes, click **Open Studio** at the bottom of the page

![Open Studio](images/03_Amazon_SageMaker_Studio.png)

### Step 4: Launch JupyterLab

1. In SageMaker Studio Home, you'll see the Overview tab with different workflow options
2. Click on the **JupyterLab** card - this lets you create and run Jupyter notebooks in a dedicated environment

![Open JupyterLab](images/04_Open_JupyterLab.png)

### Step 5: Create a JupyterLab Space

1. Under **Space templates**, find the **Quick start** option (ml.t3.medium - 5 GB - 4 GiB RAM)
2. Click **Launch now** to create a lightweight development environment perfect for this lab

![Quick Start Launch](images/05_Quick_Start_Launch_Now.png)

### Step 6: Open Your Space

1. Wait for the **Status** column to show **Running** (this may take 1-2 minutes)
2. Once running, click on the space name (e.g., **quickstart-default-t...**) in the Name column to open JupyterLab

![JupyterLab spaces list showing Running status and space name to click](images/06_Click_Quick_start_space.png)

### Step 7: Create a Labs Folder

1. In the JupyterLab file browser on the left, click the **Create New Folder** icon (folder with a + sign)
2. Name the folder `labs` and press Enter
3. Double-click the **labs** folder to open it

![Create Folder](images/08_create_folder.png)

### Step 8: Clone the Git Repository

1. With the `labs` folder open, click on the **Git icon** in the left sidebar (it looks like a diamond/branch symbol)
2. If a **Clone a Repository** button is visible, click it and enter the repository URL:
   ```
   https://github.com/neo4j-partners/lab-neo4j-aws.git
   ```
   If the clone button is not available, open a terminal instead:
   1. In the JupyterLab Launcher, click **Terminal** under the **Other** section
   2. Run these commands to clone the repository into your labs folder:
      ```bash
      cd labs
      git clone https://github.com/neo4j-partners/lab-neo4j-aws.git
      ```
3. Once the clone completes, click the **file browser icon** (folder icon) in the left sidebar to navigate into the `labs/lab-neo4j-aws` directory

## Run the Agent Notebook

1. Open [basic_langgraph_agent.ipynb](basic_langgraph_agent.ipynb) in this lab folder
2. The notebook loads configuration from `../CONFIG.txt` (MODEL_ID and REGION)
3. Run through the cells to:
   - Install required packages
   - Define simple tools (get_current_time, add_numbers)
   - Build and compile the LangGraph agent
   - Test the agent with sample queries
   - Ask questions about sample SEC financial filing data
   - Package and deploy the agent to AgentCore Runtime
   - Invoke the deployed agent via CLI and boto3

## Next Steps

Continue to [Lab 4 - MCP-Based Retrieval](../Lab_4_MCP_Retrieval) to learn how to connect an agent to a Neo4j knowledge graph through the Model Context Protocol (MCP) and perform semantic vector search and graph-enriched retrieval.
