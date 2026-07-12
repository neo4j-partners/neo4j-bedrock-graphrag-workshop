# Neo4j and AWS Bedrock GraphRAG Workshop

**[View the full workshop guide](https://neo4j-partners.github.io/neo4j-bedrock-graphrag-workshop)**

A hands-on workshop teaching Graph Retrieval-Augmented Generation (GraphRAG) patterns using Neo4j Aura and Amazon Bedrock. You will build and query a knowledge graph of SEC 10-K financial filings, then connect AI agents that retrieve structured and unstructured data to answer questions about companies, risk factors, and institutional ownership.

## Workshop Structure

### Part 1: Getting Started with Neo4j Aura and the Dataset (Labs 0-1)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 0](Lab_0_Sign_In/README.md) | Sign In | AWS Console sign-in and Bedrock access verification |
| [Lab 1](Lab_1_Aura_Setup/README.md) | Neo4j Aura Setup | Sign up for Neo4j Aura, load knowledge graph via Cypher, explore graph |

### Part 2: AWS ETL, Semantic Search, and GraphRAG (Labs 2-4)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 2](Lab_2_Data_Pipeline/README.md) | Data Pipeline (Optional) | Load chunks, generate Titan embeddings, create a vector index, and link chunks to graph entities |
| [Lab 3](Lab_3_GraphRAG_Search/README.md) | Semantic Search and GraphRAG | Vector retrieval and vector-cypher retrieval over the knowledge graph with the neo4j-graphrag library |
| [Lab 4](Lab_4_GraphRAG_Agent/) | Strands GraphRAG Agent | Wrap the retrievers as Strands tools and let the agent choose the retrieval strategy per question |

### Part 3: Agent Memory (Optional / Advanced)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 5](Lab_5_Agent_Memory/README.md) | Agent Memory with Neo4j | Add persistent memory across conversation turns with neo4j-agent-memory |

### Part 4: Neo4j MCP Server (Optional / Advanced)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 6](Lab_6_MCP_Server/README.md) | Neo4j MCP Server | Strands Agents with MCP: tool discovery, Cypher Templates, and Text2Cypher patterns |

### Appendix

| Section | Title | Description |
|---------|-------|-------------|
| [Appendix](zz_Appendix_What_Is_An_Agent/README.md) | What Is an Agent? | Strands Agents SDK basics, tool binding, the ReAct pattern, and AgentCore deployment |

## Prerequisites

- AWS Account with Bedrock access (or workshop credentials via OneBlink)
- Basic Python knowledge (for Labs 2-6)

## Quick Start

### Option 1: AWS SageMaker Studio (Recommended for workshops)

Follow the [Environment Setup: SageMaker Studio](https://neo4j-partners.github.io/neo4j-bedrock-graphrag-workshop/workshop/neo4j-bedrock-graphrag-workshop/1.0/part2-setup-instructions.html) guide to create a SageMaker Studio domain, launch JupyterLab, and clone the repository.

### Option 2: Local Development

```bash
git clone https://github.com/neo4j-partners/neo4j-bedrock-graphrag-workshop.git
cd neo4j-bedrock-graphrag-workshop

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
| **Embeddings** | Amazon Titan Text Embeddings V2 |
| **Agent Frameworks** | Strands Agents SDK |
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
https://github.com/neo4j-partners/neo4j-bedrock-graphrag-workshop/issues

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
