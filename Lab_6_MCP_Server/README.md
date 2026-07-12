# Lab 6 - Neo4j MCP Server

Connect a Strands Agent to a Neo4j knowledge graph through the **Model Context Protocol (MCP)**. This lab introduces MCP tool discovery, then builds an autonomous **Text2Cypher** agent that discovers the graph schema and writes its own Cypher from scratch.

## What You'll Learn

- **MCP fundamentals**: Agent → MCP Server → Data Source architecture, tool discovery, Streamable HTTP transport
- **Text2Cypher pattern**: The agent discovers the graph schema and writes original Cypher, then executes it over MCP
- **Schema-first prompting**: grounding generated queries in the real graph structure so the agent uses correct labels, relationship types, and properties

## Prerequisites

- Completed **Lab 1** (Neo4j Aura instance with SEC financial data loaded)
- `CONFIG.txt` updated with `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`
- AWS credentials configured for Amazon Bedrock access

> **Note:** The MCP server is pre-deployed by the lab administrator with full embeddings and indexes. You do not need to complete Labs 2–4 before starting this lab.

## The MCP Server

This lab connects to the **Neo4j MCP server deployed on Amazon Bedrock AgentCore**. The deployment (AgentCore Gateway, IAM, container, and setup scripts) lives in a separate repository:

- **[neo4j-partners/aws-starter](https://github.com/neo4j-partners/aws-starter)**. See the `neo4j-agentcore-mcp-server/` directory.

The lab administrator runs that deployment and provides the resulting `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN` in `CONFIG.txt`. The server exposes two read-only tools over MCP: `get-schema` and `read-cypher`.

## Notebook

| Notebook | Title | What You Build |
|----------|-------|----------------|
| `01_mcp_text2cypher_agent.ipynb` | Neo4j MCP Agent with Text2Cypher | MCP connection via Streamable HTTP, tool discovery with `list_tools_sync()`, and an autonomous Text2Cypher agent that discovers the schema and writes original Cypher |

## Alternative Frameworks

This lab uses the **Strands Agents SDK** (AWS-native, built-in MCP support, simpler API). **LangGraph** is a viable alternative that provides fine-grained control over the agent loop via LangChain MCP adapters. It is better suited for complex, multi-step workflows.

## Sample Queries

Once your agent is running, try these questions about the SEC financial data:

| Category | Example Question |
|----------|-----------------|
| **Exploration** | "How many companies are in the database?" |
| **Products** | "What products does Apple offer?" |
| **Ownership** | "Which asset managers own stakes in NVIDIA?" |
| **Risk** | "What risk factors does Microsoft face?" |
| **Financials** | "Show me the financial metrics for Tesla." |
| **Cross-entity** | "Which companies face risk factors related to cybersecurity?" |
