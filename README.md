# Neo4j and AWS Bedrock GraphRAG Workshop

A hands-on workshop teaching Graph Retrieval-Augmented Generation (GraphRAG) patterns using Neo4j Aura and Amazon Bedrock. You will build and query a knowledge graph of SEC 10-K financial filings, then connect AI agents that retrieve structured and unstructured data to answer questions about companies, risk factors, and institutional ownership.

## Workshop Structure

### Part 1: No-Code Track (Labs 0-2)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 0](Lab_0_Sign_In/) | Sign In | AWS Console sign-in and Bedrock access verification |
| [Lab 1](Lab_1_Aura_Setup/) | Neo4j Aura Setup | Subscribe via AWS Marketplace, restore backup, explore graph |
| [Lab 2](Lab_2_Aura_Agents/) | Aura Agents | Build a no-code AI agent using Neo4j Aura Agent platform |

### Part 2: GraphRAG with Python (Labs 4-6)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 4](Lab_4_Intro_to_Bedrock_and_Agents/) | Intro to Bedrock and Agents | SageMaker setup, LangGraph foundations, tool binding, ReAct pattern |
| [Lab 6](Lab_6_GraphRAG/) | GraphRAG | Six notebooks: data loading, embeddings, vector retrieval, vector-cypher retrieval, fulltext search, hybrid search |

### Part 3: Advanced Agents (Labs 7-8)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 7](Lab_7_Neo4j_MCP_Agent/) | Neo4j MCP Agent | Connect AI agents to Neo4j via the Model Context Protocol (LangGraph and Strands implementations) |
| [Lab 8](Lab_8_Aura_Agents_API/) | Aura Agents API | Call the Lab 2 agent programmatically with OAuth2 authentication and async batch queries |

## Prerequisites

- AWS Account with Bedrock access (or workshop credentials via OneBlink)
- Basic Python knowledge (for Labs 4-8)

## Quick Start

### Option 1: AWS SageMaker Studio (Recommended for workshops)

Follow [Lab 4](Lab_4_Intro_to_Bedrock_and_Agents/README.md) to set up SageMaker Studio and clone the repository.

### Option 2: Local Development

```bash
git clone https://github.com/neo4j-partners/lab-neo4j-aws.git
cd lab-neo4j-aws

# Copy and fill in your credentials
cp CONFIG.txt CONFIG.txt.local
# Edit CONFIG.txt with your Neo4j and AWS credentials
```

Start with [Lab 0](Lab_0_Sign_In/) for AWS setup instructions.

## Configuration

All credentials are stored in `CONFIG.txt` at the project root (gitignored). The file uses dotenv format:

```
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
REGION=us-east-1
```

See `CONFIG.txt` for all available settings grouped by lab.

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Knowledge Graph** | Neo4j Aura (via AWS Marketplace) |
| **Foundation Models** | Amazon Bedrock (Claude Sonnet) |
| **Embeddings** | Amazon Titan Text Embeddings V2 |
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
  Titan Embeddings       Claude LLM                Direct Query
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
