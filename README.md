# Neo4j and AWS Bedrock GraphRAG Workshop

A hands-on workshop teaching Graph Retrieval-Augmented Generation (GraphRAG) patterns using Neo4j Aura and Amazon Bedrock.

## Workshop Overview

This workshop teaches you how to build AI-powered applications that combine the power of knowledge graphs with large language models. You'll learn to:

- Build and explore knowledge graphs from SEC 10-K filings
- Create vector embeddings using Amazon Titan
- Implement various retrieval patterns (Vector, Vector+Cypher, Text2Cypher)
- Build AI agents using Amazon Bedrock and Strands Agents SDK

## Prerequisites

- AWS Account with Bedrock access
- GitHub account (for Codespaces)
- Basic Python knowledge (for coding labs)

## Workshop Structure

### Part 1: No-Code Track (Labs 0-4)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 0](Lab_0_Sign_In/) | Sign In | AWS Console sign-in and Bedrock access verification |
| [Lab 1](Lab_1_Aura_Setup/) | Neo4j Aura Setup | Subscribe via AWS Marketplace, restore backup, explore graph |
| [Lab 2](Lab_2_Aura_Agents/) | Aura Agents | Build a no-code AI agent using Neo4j Aura Agent platform |
| [Lab 3](Lab_3_Bedrock_Setup/) | Bedrock Setup | Enable model access and test in the Bedrock Playground |
| [Lab 4](Lab_4_GAAB_Agents/) | AI Agent Builder | Create an agent using GAAB with Neo4j MCP integration |

### Part 2: Coding Track (Labs 5-9)

| Lab | Title | Description |
|-----|-------|-------------|
| [Lab 5](Lab_5_Start_Codespace/) | Start Codespace | Configure development environment with AWS tools |
| [Lab 6](Lab_6_Knowledge_Graph/) | Knowledge Graph | Build a knowledge graph with embeddings and entities |
| [Lab 7](Lab_7_Retrievers/) | GraphRAG Retrievers | Implement Vector, VectorCypher, and Text2Cypher retrievers |
| [Lab 8](Lab_8_Agents/) | GraphRAG Agents | Build agents using Strands Agents SDK |
| [Lab 9](Lab_9_Hybrid_Search/) | Hybrid Search | Combine vector and fulltext search (optional) |

## Quick Start

### Option 1: GitHub Codespaces (Recommended)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/your-org/lab-neo4j-aws)

1. Click the button above to launch a Codespace
2. Wait for the environment to initialize (~3 minutes)
3. Start with [Lab 0](Lab_0_Sign_In/) for setup instructions

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/lab-neo4j-aws.git
cd lab-neo4j-aws

# Install dependencies
pip install -e .

# Configure environment
cp .env.sample .env
# Edit .env with your credentials
```

See [GUIDE_DEV_CONTAINERS.md](GUIDE_DEV_CONTAINERS.md) for detailed setup instructions.

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Knowledge Graph** | Neo4j Aura (via AWS Marketplace) |
| **Foundation Models** | Amazon Bedrock (Claude 3.5 Sonnet) |
| **Embeddings** | Amazon Titan Text Embeddings V2 |
| **Agent Framework** | Strands Agents SDK |
| **Agent Builder** | AWS Generative AI Application Builder (GAAB) |
| **GraphRAG Library** | neo4j-graphrag |
| **Infrastructure** | AWS CDK |

## Architecture

```
User Query → Strands Agent → Tool Selection
                                   ↓
         ┌─────────────────────────┴─────────────────────────┐
         ↓                         ↓                         ↓
   Vector Search           Text2Cypher              Cypher Template
         ↓                         ↓                         ↓
   Titan Embeddings         Claude LLM                Direct Query
         ↓                         ↓                         ↓
         └─────────────────────────┴─────────────────────────┘
                                   ↓
                            Neo4j Aura
                                   ↓
                          Knowledge Graph
```

## AWS Services Used

- **Amazon Bedrock** - Foundation model access (Claude, Titan)
- **Generative AI Application Builder** - No-code agent creation with MCP support
- **AWS Marketplace** - Neo4j Aura subscription
- **Amazon CloudWatch** - Monitoring and logging
- **AWS CDK** - Infrastructure as Code

## Cost Considerations

- **Neo4j Aura**: Pay-as-you-go based on instance size
- **Amazon Bedrock**: Pay per token (Claude ~$3/M input, Titan Embeddings ~$0.02/M)
- **Recommendation**: Use Claude Haiku for lower costs during workshop exercises

## Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for details.

To report bugs or suggest improvements, open an issue at:
https://github.com/your-org/lab-neo4j-aws/issues

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Neo4j Developer Relations team
- AWS Solutions Architecture team
- GraphRAG community contributors
