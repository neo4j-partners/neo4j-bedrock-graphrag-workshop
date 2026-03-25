# Lab 5 — Neo4j MCP Server

Connect a Strands Agent to a Neo4j knowledge graph through the **Model Context Protocol (MCP)**. This lab introduces MCP tool discovery, then progresses from pre-written Cypher templates to fully autonomous Text2Cypher agents.

## What You'll Learn

- **MCP fundamentals**: Agent → MCP Server → Data Source architecture, tool discovery, Streamable HTTP transport
- **Cypher Templates pattern**: Pre-written queries in `@tool` functions for reliable, predictable results
- **Text2Cypher pattern**: The agent discovers the graph schema and writes original Cypher from scratch
- **Graph-enriched search**: Vector similarity combined with graph traversal for knowledge retrieval

## Prerequisites

- Completed **Lab 1** (Neo4j Aura instance with SEC financial data loaded)
- `CONFIG.txt` updated with `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`
- AWS credentials configured for Amazon Bedrock access

> **Note:** The MCP server is pre-configured by the lab administrator with full embeddings and indexes. You do not need to complete Lab 4 before starting this lab.

## Notebooks

Open each notebook in order. The progression builds from MCP basics to autonomous agents.

| Notebook | Title | What You Learn |
|----------|-------|----------------|
| `01_intro_strands_mcp.ipynb` | Intro to Strands + MCP | MCP connection, tool discovery, schema inspection |
| `02_graph_enriched_search.ipynb` | Graph-Enriched Search | Cypher Templates — pre-written vector search + graph traversal via `@tool` functions |
| `03_text2cypher_agent.ipynb` | Text2Cypher Agent | Text2Cypher — agent discovers schema and writes original Cypher from scratch |

## Alternative Frameworks

This lab uses the **Strands Agents SDK** (AWS-native, built-in MCP support, simpler API). **LangGraph** is a viable alternative that provides fine-grained control over the agent loop via LangChain MCP adapters — better suited for complex, multi-step workflows.

## Sample Queries

Once your agent is running in notebook 03, try these questions about the SEC financial data:

| Category | Example Question |
|----------|-----------------|
| **Exploration** | "How many companies are in the database?" |
| **Products** | "What products does Apple offer?" |
| **Ownership** | "Which asset managers own stakes in NVIDIA?" |
| **Risk** | "What risk factors does Microsoft face?" |
| **Cross-entity** | "Which companies face risk factors related to cybersecurity?" |
