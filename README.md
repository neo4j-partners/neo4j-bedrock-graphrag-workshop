# Neo4j and AWS Bedrock GraphRAG Workshop

**[View the full workshop guide](https://neo4j-partners.github.io/lab-neo4j-aws)**

A hands-on workshop teaching Graph Retrieval-Augmented Generation (GraphRAG) patterns using Neo4j Aura and Amazon Bedrock. You will build and query a knowledge graph of SEC 10-K financial filings, then connect AI agents that retrieve structured and unstructured data to answer questions about companies, risk factors, and institutional ownership.

## Workshop Structure

### Part 1: Setup & Visual Exploration with Neo4j (Labs 0-2)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 0](Lab_0_Sign_In/README.md) | Sign In | AWS Console sign-in and Bedrock access verification |
| [Lab 1](Lab_1_Aura_Setup/README.md) | Neo4j Aura Setup | Sign up for Neo4j Aura, load knowledge graph via Cypher, explore graph |
| [Lab 2](Lab_2_Aura_Agents/README.md) | Aura Agents | Build a no-code AI agent using Neo4j Aura Agent platform |

### Part 2: Building GraphRAG Agents (Labs 3-4)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 3](Lab_3_Intro_to_Bedrock_and_Agents/README.md) | Intro to Bedrock and Agents | SageMaker setup, Strands Agents SDK, tool binding, ReAct pattern, AgentCore deployment |
| [Lab 4](Lab_4_GraphRAG_Search/README.md) | GraphRAG Search | Load chunk embeddings, vector retrieval, and vector-cypher retrieval over a knowledge graph |

### Part 3: MCP Agents & Data Pipeline (Labs 5-6)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 5](Lab_5_MCP_Server/README.md) | Neo4j MCP Server | Strands Agents with MCP: tool discovery, Cypher Templates, and Text2Cypher patterns |
| [Lab 6](Lab_6_GraphRAG_Pipeline/README.md) | GraphRAG Pipeline | Build a GraphRAG data pipeline from scratch: data loading, embeddings, and vector-cypher retrieval |

## Prerequisites

- AWS Account with Bedrock access (or workshop credentials via OneBlink)
- Basic Python knowledge (for Labs 3-6)

## Quick Start

### Option 1: AWS SageMaker Studio (Recommended for workshops)

Follow [Lab 3](Lab_3_Intro_to_Bedrock_and_Agents/README.md) to set up SageMaker Studio and clone the repository.

### Option 2: Local Development

```bash
git clone https://github.com/neo4j-partners/lab-neo4j-aws.git
cd lab-neo4j-aws

# Copy and fill in your credentials
cp CONFIG.txt CONFIG.txt.local
# Edit CONFIG.txt with your Neo4j and AWS credentials
```

Start with [Lab 0](Lab_0_Sign_In/README.md) for AWS setup instructions.

## Configuration

All credentials are stored in `CONFIG.txt` at the project root (gitignored). The file uses dotenv format:

```
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
REGION=us-east-1
```

See `CONFIG.txt` for all available settings grouped by lab.

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Knowledge Graph** | Neo4j Aura |
| **Foundation Models** | Amazon Bedrock (Claude Sonnet) |
| **Embeddings** | Amazon Nova Multimodal Embeddings |
| **Agent Frameworks** | LangGraph, Strands Agents SDK |
| **GraphRAG Library** | neo4j-graphrag |
| **Agent Protocol** | Model Context Protocol (MCP) |

## Architecture

```
User Query → AI Agent → Tool Selection
                              ↓
        ┌─────────────────────┴─────────────────────────┐
        ↓                     ↓                         ↓
  Vector Search         Text2Cypher              Cypher Template
        ↓                     ↓                         ↓
  Nova Embeddings        Claude LLM                Direct Query
        ↓                     ↓                         ↓
        └─────────────────────┴─────────────────────────┘
                              ↓
                       Neo4j Aura
                              ↓
                    SEC 10-K Knowledge Graph
```

## Contributing

We welcome contributions! To report bugs or suggest improvements, open an issue at:
https://github.com/neo4j-partners/lab-neo4j-aws/issues

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
