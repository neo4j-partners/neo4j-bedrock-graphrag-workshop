# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a hands-on workshop teaching GraphRAG (Graph Retrieval-Augmented Generation) using Neo4j and AWS Bedrock. The workshop uses SEC 10-K financial filing data (companies, products, risk factors, financial metrics, executives, asset managers) and progresses from no-code tools to building custom agents.

## Workshop Structure

- **Part 1 (Labs 0-2)**: No-code exploration using Neo4j Aura console and Aura Agents visual builder
- **Part 2 (Labs 3-5)**: Python-based GraphRAG with Strands Agents SDK and neo4j-graphrag library
- **Part 3 (Lab 6)**: MCP agents

## Key Configuration

All credentials are stored in `CONFIG.txt` at the project root (gitignored). The file uses dotenv format with keys: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `MODEL_ID`, `REGION`, `MCP_GATEWAY_URL`, `MCP_ACCESS_TOKEN`.

## Lab Code Patterns

### Lab 3 - Basic Strands Agent + AgentCore Deployment
Location: `Lab_3_Intro_to_Bedrock_and_Agents/`

Two notebooks:
- `01_basic_strands_agent.ipynb`: Uses `strands.Agent` with `strands.models.BedrockModel` and `@tool` decorator. Defines simple tools (get_current_time, add_numbers), creates an agent, tests it with queries including sample SEC filing data.
- `02_deploy_to_agentcore.ipynb`: Deploys the agent to AgentCore Runtime via `bedrock-agentcore-starter-toolkit` using `direct_code_deploy`. Agent code is pre-built in `agentcore_deploy/` (agent.py + pyproject.toml).

### Lab 4 - Graph-Enriched Search
Location: `Lab_4_Graph_Enriched_Search/`

Three notebooks using Strands Agents SDK with MCP to search a Neo4j knowledge graph:
- `00_intro_strands_mcp.ipynb`: Introduction to Strands+MCP — agent discovers tools via `list_tools_sync()` and queries the graph directly (Text2Cypher pattern, no `@tool` wrappers)
- `01_vector_search_mcp.ipynb`: Semantic vector search via `strands.tools.mcp.MCPClient` using Bedrock Nova embeddings
- `02_graph_enriched_search_mcp.ipynb`: Vector search with graph traversal for enriched context (document metadata, neighboring chunks, connected entities)

All three notebooks use Strands `MCPClient` with `streamablehttp_client` transport. Notebook 00 passes MCP tools directly to the agent (standard Strands pattern). Notebook 01 uses `lib/lab_4_data_utils.py` for Bedrock embeddings (lightweight — no neo4j dependency) and `MCPClient.call_tool_sync()` inside `@tool` wrappers for direct Cypher execution. Notebook 02 defines its own `get_embedding` inline and uses `MCPClient` in a context-manager-per-query pattern where the agent calls MCP tools directly.

### Lab 5 - GraphRAG
Location: `Lab_5_GraphRAG/`

Six notebooks covering data loading, embeddings, vector retrieval, graph-enhanced retrieval, full-text search, and hybrid search. Uses a forked neo4j-graphrag with Bedrock support (`neo4j-graphrag[bedrock]` from `neo4j-partners/neo4j-graphrag-python@bedrock-embeddings`).

### Lab 6 - Advanced Agents
Location: `Lab_6_Advanced_Agents/`

Text2Cypher pattern: the agent discovers the graph schema via MCP and writes its own Cypher from scratch. Distinct from Lab 4's Cypher Templates pattern where queries are pre-written. Two framework implementations: LangGraph + langchain-mcp-adapters, and Strands.

## Shared Utilities

`lib/data_utils.py`: `Neo4jConfig`, `BedrockConfig` (pydantic-settings), `Neo4jConnection`, `DataLoader`, `get_embedder()`, `get_llm()`, `get_embedding()`, `get_schema()`, `split_text()`. Loads config from project-root `CONFIG.txt`.

`lib/mcp_utils.py`: `MCPConnection` — wraps raw MCP `ClientSession` over Streamable HTTP for persistent connections and `execute_query(cypher)`. Loads config from `CONFIG.txt` by default.

`Lab_4_Graph_Enriched_Search/lib/lab_4_data_utils.py`: Lightweight `BedrockConfig` and `get_embedding()` only — no neo4j or neo4j-graphrag dependency. Used by Lab 4 notebooks. Lab 4 no longer has its own `mcp_utils.py` — all MCP access uses Strands `MCPClient` directly.

`financial_data_load/lib/`: Local copies of `data_utils.py` and `mcp_utils.py` that load from `financial_data_load/.env` instead of the project-root `CONFIG.txt`. These are copied from the root `lib/` to simplify env loading for the test harness. If either copy is changed, the other must be updated to match.

## Knowledge Graph Schema

- **Nodes**: Company, Product, RiskFactor, AssetManager, Document, Chunk
- **Relationships**: OFFERS, FACES_RISK, COMPETES_WITH, PARTNERS_WITH, OWNS, FILED, FROM_DOCUMENT, NEXT_CHUNK, FROM_CHUNK
- **Vector Index**: `chunkEmbeddings` on Chunk.embedding (1024 dims for Nova)
- **Fulltext Indexes**: `search_chunks` (on Chunk.text), `search_entities` (on Company/Product/RiskFactor names)

## Financial Data

Structured CSV seed data lives in `setup/seed-data/`: entity tables (companies, products, risk_factors, asset_managers), junction tables (company_products, company_risk_factors, asset_manager_companies), and relationship tables (company_competitors, company_partners).

## Running Notebooks

The notebooks are designed for AWS SageMaker Studio but work locally with:
1. Configure `CONFIG.txt` with Neo4j and AWS credentials
2. Install dependencies per notebook (uses `%pip install`)
3. Ensure AWS credentials are configured for Bedrock access

## Dependencies

Lab 5 uses `pyproject.toml` at `Lab_5_GraphRAG/src/pyproject.toml`: Python 3.11+, neo4j-graphrag[bedrock] (from neo4j-partners fork), python-dotenv, pydantic-settings, nest-asyncio.
