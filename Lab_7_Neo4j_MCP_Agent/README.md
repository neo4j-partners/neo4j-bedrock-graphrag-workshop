# Lab 7 - Neo4j MCP Agent

Connect AI agents to your Neo4j knowledge graph using the Model Context Protocol (MCP). Choose between LangGraph and Strands agent frameworks.

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

## Notebooks

This lab provides two notebook options. Both connect to the same MCP server and produce the same results. Choose the one that fits your interest:

| Notebook | Framework | Description |
|----------|-----------|-------------|
| [neo4j_langgraph_mcp_agent.ipynb](neo4j_langgraph_mcp_agent.ipynb) | LangGraph | Full-featured agent with LangChain MCP adapters. Better for complex, multi-step workflows with fine-grained control over the agent loop. |
| [neo4j_strands_mcp_agent.ipynb](neo4j_strands_mcp_agent.ipynb) | Strands | Lightweight agent using the AWS-native Strands SDK. Fewer lines of code, built-in MCP support, simpler API. |

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
