# Lab 7 - Neo4j MCP Agent

Connect AI agents to your Neo4j knowledge graph using the Model Context Protocol (MCP). Instead of writing Cypher queries by hand, you will ask natural language questions and let an AI agent query the SEC financial data for you.

## What You'll Learn

- What MCP is and how it connects AI agents to external data sources
- How the Neo4j MCP Server exposes graph operations as discoverable tools
- The schema-first approach: why the agent retrieves the graph schema before writing queries
- Two agent framework implementations: LangGraph (complex workflows) and Strands (lightweight, AWS-native)

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 1** (Neo4j Aura instance with SEC financial data loaded)
- Your `CONFIG.txt` file updated with MCP Gateway credentials (`MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`)
- AWS credentials configured for Amazon Bedrock access

## MCP Overview

The **Model Context Protocol (MCP)** is an open standard that defines how AI agents discover and interact with external tools and data sources. It provides a uniform interface so that any MCP-compatible agent can connect to any MCP-compatible server without custom integration code.

### How MCP Works

MCP defines a three-component architecture:

```
AI Agent  <-->  MCP Server  <-->  Data Source
(Client)       (Protocol)        (Neo4j, APIs, etc.)
```

1. **AI Agent (Client)**: The LLM-powered application that needs to access external data. It discovers available tools by asking the MCP server what operations are supported.
2. **MCP Server**: A lightweight service that exposes data source operations as tools. It translates between the MCP protocol and the data source's native API.
3. **Data Source**: The underlying system (Neo4j, a REST API, a file system, etc.) that holds the data.

### Transport Options

MCP supports multiple transport mechanisms:

| Transport | Description | Use Case |
|-----------|-------------|----------|
| **stdio** | Standard input/output streams | Local development, CLI tools |
| **Streamable HTTP** | HTTP-based streaming protocol | Cloud deployments, remote servers |

This lab uses Streamable HTTP to connect to an MCP Gateway running on AWS.

### Neo4j MCP Server Tools

The Neo4j MCP Server exposes two primary tools:

| Tool | Description |
|------|-------------|
| **get-neo4j-schema** | Returns the graph schema: node labels, relationship types, and properties |
| **read-neo4j-cypher** | Executes a read-only Cypher query and returns results |

The agent discovers these tools automatically through the MCP protocol. It does not need to know about them in advance.

## AWS Deployment Architecture

In this workshop, the MCP infrastructure is pre-deployed on AWS:

```
Agent (Notebook)  -->  AgentCore Gateway (HTTPS)  -->  Neo4j MCP Server (Container)  -->  Secrets Manager  -->  Neo4j Aura
```

- **Agent (Notebook)**: Your Jupyter notebook running a LangGraph or Strands agent. It connects to the gateway using a URL and access token from `CONFIG.txt`.
- **AgentCore Gateway**: An AWS-managed HTTPS endpoint that authenticates requests and routes them to the MCP server.
- **Neo4j MCP Server**: A containerized service that implements the MCP protocol and translates tool calls into Neo4j operations.
- **Secrets Manager**: Stores the Neo4j Aura connection credentials securely. The MCP server retrieves them at runtime.
- **Neo4j Aura**: Your graph database containing SEC financial data.

You do not need to set up any of this infrastructure. The gateway URL and access token are provided in `CONFIG.txt`.

## Notebooks

This lab provides two notebook options. Both connect to the same MCP server and produce the same results. Choose the one that fits your interest:

| Notebook | Framework | Description |
|----------|-----------|-------------|
| [neo4j_langgraph_mcp_agent.ipynb](neo4j_langgraph_mcp_agent.ipynb) | LangGraph | Full-featured agent with LangChain MCP adapters. Better for complex, multi-step workflows with fine-grained control over the agent loop. |
| [neo4j_strands_mcp_agent.ipynb](neo4j_strands_mcp_agent.ipynb) | Strands | Lightweight agent using the AWS-native Strands SDK. Fewer lines of code, built-in MCP support, simpler API. |

## Schema-First Approach

Both notebooks instruct the agent to follow a schema-first pattern:

1. **Retrieve the schema** before writing any Cypher query. The agent calls `get-neo4j-schema` to learn what node labels, relationship types, and properties exist in the database.
2. **Write a Cypher query** based on the actual schema. This prevents the agent from guessing at property names or relationship types that do not exist.
3. **Execute the query** using `read-neo4j-cypher` and return the results.

This approach produces more accurate queries because the agent works with the real structure of the data rather than assumptions.

## Sample Queries

Once your agent is running, try these questions about the SEC financial data:

| Category | Example Question |
|----------|-----------------|
| **Exploration** | "How many companies are in the database?" |
| **Products** | "What products does Apple offer?" |
| **Ownership** | "Which asset managers own stakes in NVIDIA?" |
| **Risk** | "What risk factors does Microsoft face?" |
| **Financials** | "Show me the financial metrics for Tesla." |
| **Executives** | "Who are the executives at Amazon?" |
| **Cross-entity** | "Which companies face risk factors related to cybersecurity?" |

## Next Steps

After completing this lab, continue to [Lab 8 - Aura Agents API](../Lab_8_Aura_Agents_API/) to interact with Neo4j Aura Agents through a REST API.
