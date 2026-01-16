# Proposal: Neo4j and AWS Bedrock Hands-On Workshop

## Executive Summary

This document proposes adapting the existing "Neo4j and Azure Generative AI Workshop" for Amazon Web Services (AWS). The workshop teaches GraphRAG (Graph Retrieval-Augmented Generation) patterns using Neo4j Aura combined with cloud AI services. This AWS version would replace Microsoft Foundry with Amazon Bedrock and leverage the AWS ecosystem for infrastructure, monitoring, and deployment.

The adaptation maintains the workshop's educational value while introducing participants to AWS-native AI services, including the newly released Amazon Bedrock AgentCore platform for building and deploying AI agents.

---

## Service Mapping: Azure to AWS

| Azure Service | AWS Equivalent | Notes |
|--------------|----------------|-------|
| Microsoft Foundry (Azure AI Foundry) | Amazon Bedrock | Fully managed foundation model service |
| Azure OpenAI (gpt-4o-mini) | Amazon Bedrock (Claude, Titan, or Llama models) | Anthropic Claude recommended for agent tasks |
| text-embedding-ada-002 | Amazon Titan Text Embeddings V2 | 1024 dimensions (configurable: 256, 512, 1024) |
| Microsoft Agent Framework | Amazon Bedrock Agents + AgentCore | Built-in agent orchestration with MCP support |
| Azure Bicep | AWS CDK (TypeScript/Python) | Infrastructure as Code |
| Azure Developer CLI (azd) | AWS CDK CLI + AWS SAM CLI | Deployment orchestration |
| Azure Container Apps | AWS App Runner or Amazon ECS/Fargate | Serverless container hosting |
| Azure Monitor / Application Insights | Amazon CloudWatch + X-Ray | Observability and tracing |
| Azure Storage | Amazon S3 | Object storage |
| Azure Marketplace (Neo4j) | AWS Marketplace (Neo4j Aura) | Same Neo4j Aura offering available |
| GitHub Codespaces | GitHub Codespaces (unchanged) | Update devcontainer for AWS CLI/CDK |
| Microsoft Agent Framework | Strands Agents SDK | AWS open-source agent framework with native MCP support |

---

## High-Level Architecture

### Current Azure Architecture
```
User → Azure AI Foundry → GPT-4o-mini / Ada-002
              ↓
    Microsoft Agent Framework
              ↓
         Neo4j Aura (Azure Marketplace)
```

### Proposed AWS Architecture
```
User → Amazon Bedrock → Claude / Titan Embeddings
              ↓
    Strands Agents SDK (with LangChain tools)
              ↓
         Neo4j Aura (AWS Marketplace)
```

### Key Architectural Changes

1. **Model Provider Shift**: Replace OpenAI models hosted on Azure with Amazon's Titan models or Anthropic's Claude models hosted on Bedrock

2. **Agent Framework Change**: Replace Microsoft Agent Framework with Strands Agents SDK, AWS's open-source agent framework with native MCP support and LangChain tool compatibility

3. **Infrastructure as Code**: Convert Azure Bicep templates to AWS CDK constructs

4. **Authentication**: Replace Azure AD / Azure Identity with AWS IAM and Cognito

---

## Lab-by-Lab Adaptation Guide

### Part 1: No-Code Track (Labs 0-3)

#### Lab 0: Sign In
**Current**: Azure Portal authentication with provided credentials

**AWS Adaptation**:
- Replace with AWS Console sign-in
- Provide IAM user credentials or use AWS SSO
- Participants access their pre-provisioned AWS accounts
- Verify access to Bedrock service in the target region

**Changes Required**:
- New sign-in instructions for AWS Console
- Updated screenshots for AWS interface
- Region selection guidance (us-east-1 or us-west-2 recommended for Bedrock)

---

#### Lab 1: Neo4j Aura Setup
**Current**: Subscribe to Neo4j Aura through Azure Marketplace

**AWS Adaptation**:
- Subscribe to Neo4j Aura through AWS Marketplace (Pay-as-You-Go option)
- Same database creation and backup restore process
- Neo4j connection strings work identically across cloud providers

**Changes Required**:
- Updated Marketplace subscription screenshots for AWS
- AWS billing integration instructions
- Same backup file can be used (cloud-agnostic)
- Update navigation paths for AWS Marketplace interface

**AWS-Specific Notes**:
- Neo4j Aura is available as both annual and pay-as-you-go options on AWS Marketplace
- Billing consolidates with existing AWS spend
- AWS credits can be applied to Neo4j Aura usage

---

#### Lab 2: Aura Agents (No-Code)
**Current**: Uses Neo4j's Aura Agent platform (cloud-agnostic)

**AWS Adaptation**:
- No changes required - Aura Agents is Neo4j's own platform
- Works identically regardless of where Neo4j Aura is provisioned
- Cypher Template tools, Similarity Search, and Text2Cypher tools remain the same

**Changes Required**:
- None - this lab is fully cloud-agnostic

---

#### Lab 3: Foundry Agents → Bedrock Agents
**Current**:
- Set up Microsoft Foundry project
- Deploy gpt-4o-mini model
- Create agent using Neo4j MCP Server

**AWS Adaptation**:
- Set up Amazon Bedrock in the AWS Console
- Enable Claude (Anthropic) or Amazon Titan models through Bedrock model access
- Create a Bedrock Agent with the Neo4j MCP Server

**Changes Required**:

**New Content: Amazon Bedrock Setup**
- Navigate to Amazon Bedrock console
- Request model access for Claude Sonnet or Claude Haiku (recommended for agents)
- Enable Amazon Titan Text Embeddings V2 for embedding tasks
- Note: Model access requires one-time approval (usually instant for Titan, may take minutes for Claude)

**New Content: Bedrock Agents with MCP**
Amazon Bedrock AgentCore (launched October 2025) provides native MCP support. The workshop would demonstrate:

1. **Creating a Bedrock Agent**:
   - Define agent instructions (same prompts work across platforms)
   - Configure the foundation model (Claude Sonnet recommended)
   - Set up agent action groups

2. **Connecting Neo4j MCP Server**:
   - Deploy Neo4j MCP Server to AgentCore Runtime
   - AgentCore Gateway provides zero-code MCP tool creation
   - Configure connection to Neo4j Aura using connection string and credentials

3. **Testing the Agent**:
   - Use the Bedrock console to test agent interactions
   - Verify schema exploration and Cypher query execution

**AWS-Specific Advantages**:
- AgentCore Gateway supports automatic tool discovery from MCP servers
- Built-in session management (up to 8-hour sessions for complex tasks)
- Native integration with AWS IAM for security
- CloudWatch integration for monitoring agent execution

---

### Part 2: Coding Track (Labs 4-8)

#### Lab 4: Start Codespace (GitHub Codespaces - Unchanged Platform)
**Current**: GitHub Codespaces with Azure CLI and azd installed

**AWS Adaptation**: Keep GitHub Codespaces, update configuration for AWS

This approach maintains familiarity for existing workshop users while adapting for AWS services.

**Devcontainer Changes Required**:
- Replace Azure CLI with AWS CLI v2
- Replace Azure Developer CLI (azd) with AWS CDK CLI
- Add Strands Agents SDK to Python dependencies
- Update VS Code extensions for AWS (AWS Toolkit)

**Updated .devcontainer/devcontainer.json features**:
```json
{
  "features": {
    "ghcr.io/devcontainers/features/aws-cli:1": {},
    "ghcr.io/devcontainers/features/python:1": {"version": "3.12"},
    "ghcr.io/devcontainers/features/node:1": {}
  },
  "postCreateCommand": "npm install -g aws-cdk && pip install strands-agents strands-agents-tools"
}
```

**Changes Required**:

**Infrastructure Deployment (replacing azd up)**:
- Create AWS CDK stack that provisions:
  - Bedrock agent configuration
  - IAM roles for Bedrock access
  - CloudWatch log groups
  - (Optional) App Runner service for production deployment

**Environment Variables (replacing Azure config)**:
```
# AWS Configuration
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
AWS_BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
AWS_BEDROCK_AGENT_ID=           # Created by CDK deployment

# Neo4j Configuration (unchanged)
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
```

**New setup_env.py Script**:
- Sync AWS CDK outputs to .env file
- Use boto3 to retrieve Bedrock endpoint configuration
- Validate model access before proceeding

---

#### Lab 5: Building a Knowledge Graph
**Current**: Uses Azure OpenAI embeddings (text-embedding-ada-002)

**AWS Adaptation**:

**Notebook 01: Data Loading**
- No changes required - pure Neo4j operations
- Document and Chunk node creation is cloud-agnostic

**Notebook 02: Embeddings**
- Replace Azure OpenAI embedder with Bedrock embedder

**Current Azure Pattern**:
```python
# Uses Azure AI Inference SDK
from config import get_embedder
embedder = get_embedder()  # Returns Azure OpenAI embedder
```

**New AWS Pattern**:
```python
# Uses boto3 Bedrock Runtime client
import boto3
bedrock_runtime = boto3.client('bedrock-runtime')

# Amazon Titan Text Embeddings V2
# - Input: up to 8,192 tokens
# - Output: 256, 512, or 1024 dimensions (configurable)
# - Optimized for RAG use cases
```

**Changes Required**:
- Create `get_embedder()` wrapper that returns Bedrock-compatible embedder
- Update embedding dimension from 1536 (ada-002) to 1024 (Titan V2 default)
- Update vector index creation to use 1024 dimensions
- Note: neo4j-graphrag package supports custom embedders

**Notebook 03: Entity Extraction**
- Replace Azure OpenAI LLM with Bedrock LLM

**Current Pattern**:
```python
# Uses Azure AI client for entity extraction
from azure.ai.inference import ChatCompletionsClient
```

**New Pattern**:
```python
# Uses Bedrock Converse API (unified interface for all models)
import boto3
bedrock_runtime = boto3.client('bedrock-runtime')
# Converse API works with Claude, Titan, Llama, etc.
```

**Notebook 04: Full Dataset**
- Same changes as Notebooks 02 and 03
- Consider Bedrock batch inference for large-scale processing

---

#### Lab 6: GraphRAG Retrievers
**Current**: Uses neo4j-graphrag with Azure OpenAI

**AWS Adaptation**:

**Notebook 01: Vector Retriever**
- Replace embedder initialization with Bedrock embedder
- VectorRetriever from neo4j-graphrag works with any embedder

**Changes Required**:
```python
# Create Bedrock-compatible embedder for neo4j-graphrag
from neo4j_graphrag.embeddings import Embedder

class BedrockEmbedder(Embedder):
    def embed_query(self, text: str) -> list[float]:
        # Call Bedrock Titan Embeddings API
        pass
```

**Notebook 02: Vector + Cypher Retriever**
- Same embedder replacement
- VectorCypherRetriever patterns remain identical

**Notebook 03: Text2Cypher Retriever**
- Replace Azure LLM with Bedrock LLM for Cypher generation
- Claude models excel at code generation (including Cypher)

**Changes Required**:
```python
# Create Bedrock-compatible LLM for neo4j-graphrag
from neo4j_graphrag.llm import LLMInterface

class BedrockLLM(LLMInterface):
    def invoke(self, input: str) -> str:
        # Call Bedrock Converse API
        pass
```

**AWS-Specific Enhancement Opportunity**:
- Bedrock Knowledge Bases supports GraphRAG natively with Neptune Analytics
- Could demonstrate alternative approach using Bedrock's managed RAG

---

#### Lab 7: GraphRAG Agents
**Current**: Uses Microsoft Agent Framework with Azure AI Client

**AWS Adaptation**:

This is the most significant adaptation required. The Microsoft Agent Framework will be replaced with **Strands Agents SDK**, AWS's open-source agent framework launched in May 2025.

**Why Strands Agents SDK?**
- **Model-driven approach**: Define agents with just a prompt and tools - the LLM handles planning
- **Native MCP support**: Use MCP servers directly as agent tools
- **LangChain compatible**: Can use existing LangChain tools alongside native Strands tools
- **Production-proven**: Used internally at AWS for Amazon Q Developer, AWS Glue, and VPC Reachability Analyzer
- **Simple API**: Create agents in just a few lines of code
- **Bedrock native**: Uses Claude Sonnet on Bedrock by default

**Notebook 01: Simple Agent (Schema Tool)**

**Current Azure Pattern**:
```python
from agent_framework.azure import AzureAIClient
async with AzureAIClient(...) as client:
    async with client.create_agent(
        name="schema-agent",
        tools=[get_graph_schema],
    ) as agent:
        async for update in agent.run_stream(query):
            print(update.text)
```

**New AWS Pattern Using Strands Agents SDK**:
```python
from strands import Agent
from strands.tools import tool

@tool
def get_graph_schema() -> str:
    """Get the schema of the graph database including node labels, relationships, and properties."""
    return get_schema(driver)

# Create agent with tools - Strands uses Bedrock Claude by default
agent = Agent(
    system_prompt="You are a helpful assistant that answers questions about a graph database schema.",
    tools=[get_graph_schema]
)

# Run the agent (streaming is built-in)
response = agent("Summarise the schema of the graph database.")
print(response)
```

**Key Differences from Azure Pattern**:
- Use `@tool` decorator instead of relying on docstrings alone
- Agent creation is synchronous and simpler
- No explicit client/credential management needed (uses AWS credentials)
- Streaming happens automatically

**Notebook 02: Vector + Graph Agent**

```python
from strands import Agent
from strands.tools import tool
from langchain_community.tools import Neo4jVectorTool  # LangChain integration

@tool
def get_graph_schema() -> str:
    """Get the schema of the graph database."""
    return get_schema(driver)

@tool
def search_content(query: str) -> str:
    """Search for content semantically related to the query."""
    return vector_retriever.search(query)

agent = Agent(
    system_prompt="""You are a helpful assistant with access to a knowledge graph.
    Use get_graph_schema to understand the data structure.
    Use search_content for semantic questions about topics.""",
    tools=[get_graph_schema, search_content]
)
```

**Notebook 03: Text2Cypher Agent**

```python
from strands import Agent
from strands.tools import tool

@tool
def get_graph_schema() -> str:
    """Get the schema of the graph database."""
    return get_schema(driver)

@tool
def search_content(query: str) -> str:
    """Search for content semantically related to the query."""
    return vector_retriever.search(query)

@tool
def query_database(question: str) -> str:
    """Answer factual questions about companies, counts, lists, and specific attributes using database queries."""
    return text2cypher_retriever.search(question)

agent = Agent(
    system_prompt="""You are a helpful assistant that answers questions about SEC filings.

    Choose the appropriate tool:
    1. get_graph_schema - For questions about data structure
    2. search_content - For semantic questions about topics
    3. query_database - For specific facts, counts, and lookups""",
    tools=[get_graph_schema, search_content, query_database]
)
```

**AWS-Specific Features to Highlight**:
- **20+ pre-built tools**: Strands includes tools for files, APIs, AWS services
- **Bedrock Guardrails integration**: Content filtering and safety
- **AgentCore deployment**: Same code runs locally and deploys to production
- **CloudWatch observability**: Built-in metrics and tracing
- **Multi-agent support**: Create agent hierarchies for complex workflows

---

#### Lab 8: Hybrid Search (Optional)
**Current**: Fulltext and hybrid search using Neo4j indexes

**AWS Adaptation**:
- No changes required - purely Neo4j functionality
- Hybrid search combines vector + keyword matching
- Works identically regardless of embedding provider

**Changes Required**:
- Update embedder initialization to use Bedrock
- All Neo4j fulltext index operations remain the same

---

## MCP Integration: Azure Foundry vs AWS Bedrock

### Current Azure Implementation
Microsoft Foundry supports MCP servers as agent tools. The workshop demonstrates:
1. Connecting the Neo4j MCP Server to a Foundry agent
2. Using schema exploration and Cypher execution tools
3. Agent automatically discovers available MCP tools

### AWS Implementation: Strands Agents with LangChain Tools (Recommended)

The recommended approach combines **Strands Agents SDK** for the agent framework with **LangChain** tools for Neo4j integration. This provides:

- **Strands Agents**: AWS's open-source, model-driven agent framework
- **LangChain Tools**: Mature ecosystem with existing Neo4j integrations
- **Bedrock Models**: Claude or Titan as the foundation model

**Why This Combination?**

| Component | Purpose | Benefit |
|-----------|---------|---------|
| Strands Agents | Agent orchestration | Simple API, native MCP support, production-proven at AWS |
| LangChain Neo4j | Database tools | Mature, well-tested Neo4j integration |
| Amazon Bedrock | Foundation models | Managed, scalable, multiple model options |

**Implementation Pattern**:

```python
from strands import Agent
from strands.tools import tool
from langchain_community.graphs import Neo4jGraph
from langchain_aws import ChatBedrock

# Initialize Neo4j connection (LangChain)
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

# Create tools using Strands @tool decorator
@tool
def get_graph_schema() -> str:
    """Get the schema of the Neo4j graph database."""
    return graph.schema

@tool
def run_cypher_query(query: str) -> str:
    """Execute a read-only Cypher query against the database."""
    return graph.query(query)

# Create Strands agent with tools
agent = Agent(
    system_prompt="You are a helpful assistant that can query a Neo4j knowledge graph.",
    tools=[get_graph_schema, run_cypher_query]
)

# Run agent
result = agent("What companies are in the database?")
```

**MCP Server Integration (Alternative)**

Strands Agents also supports MCP servers natively:

```python
from strands import Agent
from strands.mcp import MCPClient

# Connect to Neo4j MCP Server
mcp_client = MCPClient("npx @neo4j/mcp-neo4j")

# Create agent with MCP tools
agent = Agent(
    tools=mcp_client.get_tools()  # Auto-discovers MCP tools
)
```

**Advantages of Recommended Approach**:
- **Simplicity**: Strands provides cleaner API than raw Bedrock calls
- **Flexibility**: Mix LangChain tools with native Strands tools
- **Production-ready**: Same code runs locally and deploys to AgentCore
- **Familiar patterns**: LangChain users recognize the tool patterns
- **Native MCP**: Can use MCP servers directly when needed

### Alternative Approaches

**Option 2: Bedrock AgentCore with MCP**

For production deployments requiring managed infrastructure:

- **AgentCore Runtime**: Deploy MCP servers as managed services
  - Supports MCP protocol versions 2025-06-18 and 2025-03-26
  - Complete session isolation
  - Up to 8-hour sessions for complex tasks

- **AgentCore Gateway**: Zero-code tool creation from MCP servers
  - Automatic tool discovery
  - Built-in authorization (OAuth, API keys)
  - Serverless infrastructure

**Option 3: Pure LangChain with Bedrock**

For teams already invested in LangChain:

```python
from langchain_aws import ChatBedrock
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.tools import Neo4jQueryTool

llm = ChatBedrock(model_id="anthropic.claude-3-sonnet-20240229-v1:0")
tools = [Neo4jQueryTool(graph=graph)]
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
```

**Advantages**:
- Familiar to LangChain users
- Extensive tool ecosystem
- Well-documented patterns

---

## Infrastructure as Code: Bicep to CDK

### Current Azure Bicep Structure
```
/infra/
  main.bicep
  main.parameters.json
  /core/
    /ai/cognitiveservices.bicep
    /host/ai-environment.bicep
    /monitor/loganalytics.bicep
    /security/role.bicep
```

### Proposed AWS CDK Structure
```
/infra/
  /cdk/
    app.py (or app.ts for TypeScript)
    /stacks/
      bedrock_stack.py
      monitoring_stack.py
      (optional) app_runner_stack.py
    /constructs/
      bedrock_agent.py
      neo4j_tools.py
```

### Key CDK Constructs Needed

**BedrockAgentConstruct**:
- Create Bedrock Agent
- Configure foundation model
- Define action groups for Neo4j tools
- Set up IAM roles

**MonitoringConstruct**:
- CloudWatch log groups
- X-Ray tracing (optional)
- Dashboard for agent metrics

**AppRunnerConstruct** (optional):
- Serverless API deployment
- Similar to Azure Container Apps

### CDK Deployment Commands
```bash
# Replace 'azd up' with:
cdk bootstrap    # One-time setup
cdk deploy       # Deploy all stacks

# Replace 'azd env get-values' with:
aws cloudformation describe-stacks --query "Stacks[0].Outputs"
```

---

## Python Dependencies Update

### Current Azure Requirements (pyproject.toml)
```
azure-identity>=1.19.0
azure-ai-projects>=1.0.0b11
azure-ai-inference>=1.0.0b7
agent-framework-core>=1.0.0b251120
agent-framework-azure-ai>=1.0.0b251120
```

### Proposed AWS Requirements
```
# Core AWS SDK
boto3>=1.35.0
botocore>=1.35.0

# Strands Agents SDK (AWS open-source agent framework)
strands-agents>=0.1.0
strands-agents-tools>=0.1.0

# LangChain integration for Neo4j tools
langchain>=0.3.0
langchain-aws>=0.2.0
langchain-community>=0.3.0
```

### Shared Requirements (unchanged)
```
neo4j>=5.0.0
neo4j-graphrag>=1.10.0
python-dotenv
pydantic
```

---

## Configuration Changes

### Current .env.sample (Azure)
```
AZURE_AI_PROJECT_ENDPOINT=
AZURE_AI_MODEL_NAME=gpt-4o-mini
AZURE_AI_EMBEDDING_NAME=text-embedding-ada-002
AZURE_OPENAI_ENDPOINT=
AZURE_TENANT_ID=
```

### Proposed .env.sample (AWS)
```
# AWS Configuration
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
AWS_BEDROCK_AGENT_ID=
AWS_BEDROCK_AGENT_ALIAS_ID=

# Embedding Configuration
EMBEDDING_DIMENSIONS=1024     # Titan V2 default (ada-002 uses 1536)

# Neo4j Configuration (unchanged)
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
NEO4J_VECTOR_INDEX_NAME=chunkEmbeddings
```

---

## Regional Considerations

### Azure Workshop Regions
Microsoft Foundry Agent Service available in:
- eastus2, swedencentral, westus2

### AWS Workshop Regions
Amazon Bedrock available in most regions. Recommended:
- **us-east-1** (N. Virginia) - Widest model availability
- **us-west-2** (Oregon) - Full Bedrock support
- **eu-west-1** (Ireland) - For EU-based workshops

### Model Availability Notes
- Amazon Titan models: Available in all Bedrock regions
- Anthropic Claude: Available in most regions (check current status)
- Model access requires one-time enablement per account

---

## Presentation Slide Updates

The workshop includes 15 Marp presentations. Required updates:

### Slides Requiring Major Updates

1. **lab-2-foundry/03-azure-ai-foundry-slides.md** → **aws-bedrock-slides.md**
   - Replace Foundry concepts with Bedrock concepts
   - Update screenshots for Bedrock console
   - Explain Bedrock model access workflow

2. **lab-7-agents/02-microsoft-agent-framework-slides.md** → **strands-agents-slides.md**
   - Replace AzureAIClient with Strands Agent patterns
   - Update code examples for Strands SDK @tool decorator
   - Explain LangChain tool integration and MCP support

### Slides Requiring Minor Updates

1. **lab-2-foundry/02-what-is-mcp-slides.md**
   - Update example references from Foundry to Bedrock
   - Add note about AgentCore MCP support

### Slides Requiring No Changes

- lab-1-neo4j-aura/* (Neo4j-focused)
- lab-5-knowledge-graph/* (Conceptual, not cloud-specific)
- lab-6-retrievers/01-retrievers-overview-slides.md (Conceptual)

---

## Cost Comparison

### Azure Workshop Estimated Costs
- Azure OpenAI (gpt-4o-mini): ~$0.15 per 1M input tokens
- Azure OpenAI (ada-002): ~$0.10 per 1M tokens
- Neo4j Aura: Based on instance size

### AWS Workshop Estimated Costs
- Bedrock Claude Sonnet: ~$3.00 per 1M input tokens (higher but more capable)
- Bedrock Claude Haiku: ~$0.25 per 1M input tokens (cost-effective alternative)
- Amazon Titan Embeddings V2: ~$0.02 per 1M tokens (cheaper than ada-002)
- Neo4j Aura: Same pricing (Marketplace billing)

### Cost Optimization Recommendations
- Use Claude Haiku for workshop exercises (similar capability, lower cost)
- Use Titan Embeddings V2 (optimized for RAG, lower cost)
- Pre-provision resources in a shared account for workshops
- Implement Bedrock inference profiles for cost tracking

---

## Timeline and Effort Estimate

### Phase 1: Core Adaptation (High Priority)
- Lab 0-1: Sign-in and Neo4j setup documentation
- Lab 3: Bedrock Agents with MCP
- Lab 4: Development environment and CDK setup
- Lab 5: Embeddings with Titan
- Lab 6: Retrievers with Bedrock LLM

### Phase 2: Agent Framework (Medium Priority)
- Lab 7: Full Strands Agents implementation
- Create LangChain tool wrappers for Neo4j operations
- Integrate with Bedrock via Strands SDK

### Phase 3: Polish and Testing (Lower Priority)
- Lab 8: Verify hybrid search works
- Update all presentation slides
- Test end-to-end workshop flow
- Documentation and troubleshooting guides

---

## Appendix A: AWS Service Quick Reference

### Strands Agents SDK
- **Purpose**: Open-source framework for building AI agents with a model-driven approach
- **Key Features**:
  - Simple API: Define agents with prompt + tools
  - Native MCP support: Use MCP servers directly as tools
  - 20+ pre-built tools included
  - Bedrock native: Uses Claude Sonnet by default
  - Production-proven: Powers Amazon Q Developer, AWS Glue
- **Installation**: `pip install strands-agents strands-agents-tools`
- **GitHub**: https://github.com/strands-agents/sdk-python
- **Documentation**: https://strandsagents.com

### Amazon Bedrock
- **Purpose**: Managed foundation models (Claude, Titan, Llama, etc.)
- **Key APIs**:
  - InvokeModel / InvokeModelWithResponseStream
  - Converse / ConverseStream (unified API with tool use)
  - InvokeAgent (for managed Bedrock Agents)
- **Documentation**: https://docs.aws.amazon.com/bedrock/

### Amazon Bedrock AgentCore
- **Purpose**: Build, deploy, operate AI agents at scale
- **Components**:
  - AgentCore Runtime: Deploy MCP servers and Strands agents
  - AgentCore Gateway: Centralized tool management with MCP support
- **Documentation**: https://docs.aws.amazon.com/bedrock-agentcore/

### Amazon Titan Text Embeddings V2
- **Purpose**: Generate text embeddings for RAG
- **Features**:
  - Up to 8,192 input tokens
  - Configurable output dimensions (256, 512, 1024)
  - 100+ languages supported
  - Optimized for RAG with normalization options
- **Model ID**: amazon.titan-embed-text-v2:0

### AWS CDK
- **Purpose**: Infrastructure as Code using familiar programming languages
- **Languages**: TypeScript, Python, Java, C#, Go
- **Bedrock Support**: L2 constructs for Guardrails, alpha support for agents
- **Documentation**: https://docs.aws.amazon.com/cdk/

---

## Appendix B: Research Sources

This proposal was informed by the following sources:

### Strands Agents SDK
- [Introducing Strands Agents, an Open Source AI Agents SDK](https://aws.amazon.com/blogs/opensource/introducing-strands-agents-an-open-source-ai-agents-sdk/)
- [Strands Agents SDK: A technical deep dive](https://aws.amazon.com/blogs/machine-learning/strands-agents-sdk-a-technical-deep-dive-into-agent-architectures-and-observability/)
- [Strands Agents Documentation](https://strandsagents.com)
- [Strands Agents GitHub](https://github.com/strands-agents/sdk-python)

### AWS Official Documentation
- [Amazon Bedrock Knowledge Bases](https://aws.amazon.com/bedrock/knowledge-bases/)
- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)
- [Amazon Titan Text Embeddings V2](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)

### AWS Blog Posts
- [Harness the power of MCP servers with Amazon Bedrock Agents](https://aws.amazon.com/blogs/machine-learning/harness-the-power-of-mcp-servers-with-amazon-bedrock-agents/)
- [Accelerate development with the Amazon Bedrock AgentCore MCP server](https://aws.amazon.com/blogs/machine-learning/accelerate-development-with-the-amazon-bedrock-agentcore-mcpserver/)
- [Dynamic text-to-SQL for enterprise workloads with Amazon Bedrock Agents](https://aws.amazon.com/blogs/machine-learning/dynamic-text-to-sql-for-enterprise-workloads-with-amazon-bedrock-agents/)

### Neo4j and AWS Integration
- [Knowledge Graphs and GraphRAG with AWS and Neo4j](https://docs.aws.amazon.com/architecture-diagrams/latest/knowledge-graphs-and-graphrag-with-neo4j/knowledge-graphs-and-graphrag-with-neo4j.html)
- [Neo4j AWS Strategic Collaboration Announcement](https://neo4j.com/press-releases/neo4j-aws-bedrock-integration/)
- [Neo4j on AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-xd42uzj2v7dae)

### Platform Comparisons
- [Azure AI Foundry vs AWS Bedrock: The 2025 Guide](https://blog.gopenai.com/azure-ai-foundry-vs-aws-bedrock-vs-google-vertex-ai-the-2025-guide-25a69c1d19b1)

---

## Conclusion

Adapting this workshop for AWS is feasible and aligns well with AWS's recent investments in agentic AI capabilities. The key advantages of an AWS version include:

1. **Native MCP Support**: Bedrock AgentCore provides first-class MCP integration, matching the Azure workshop's use of the Neo4j MCP Server

2. **Model Flexibility**: Bedrock's multi-model approach allows workshop participants to experiment with different models (Claude, Titan, Llama) for different tasks

3. **Enterprise Integration**: AWS's deep enterprise footprint means many workshop participants will already have AWS accounts and familiarity

4. **Cost Optimization**: Titan Embeddings V2 and Claude Haiku provide cost-effective options for workshop scenarios

The primary effort lies in adapting Lab 3 (Foundry Agents → Bedrock Agents) and Lab 7 (Microsoft Agent Framework → Strands Agents SDK with LangChain tools). The Neo4j integration remains largely unchanged since Neo4j Aura is available on both cloud marketplaces, and LangChain provides mature Neo4j tooling that integrates seamlessly with Strands Agents.
