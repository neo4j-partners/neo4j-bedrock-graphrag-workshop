# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a hands-on workshop teaching GraphRAG (Graph Retrieval-Augmented Generation) using Neo4j and AWS Bedrock. The workshop uses SEC 10-K financial filing data (companies, products, risk factors, financial metrics, executives, asset managers) and progresses from no-code tools to building custom agents.

## Workshop Structure

- **Part 1 (Labs 0-2)**: No-code exploration using Neo4j Aura console and Aura Agents visual builder
- **Part 2 (Labs 3-6)**: Python-based GraphRAG with Strands Agents SDK and neo4j-graphrag library
- **Part 3 (Lab 7)**: MCP agents and Aura Agents API

## Key Configuration

All credentials are stored in `CONFIG.txt` at the project root (gitignored). The file uses dotenv format with keys: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `MODEL_ID`, `REGION`, `MCP_GATEWAY_URL`, `MCP_ACCESS_TOKEN`.

## Lab Code Patterns

### Lab 3 - Basic Strands Agent + AgentCore Deployment
Location: `Lab_3_Intro_to_Bedrock_and_Agents/01_basic_strands_agent.ipynb`

Uses `strands.Agent` with `strands.models.BedrockModel` and `@tool` decorator. Defines simple tools (get_current_time, add_numbers), creates an agent, tests it with queries including sample SEC filing data. Ends with packaging and deploying the agent to AgentCore Runtime via `bedrock-agentcore-starter-toolkit` using `direct_code_deploy`.

### Lab 4 - Graph-Enriched Search
Location: `Lab_4_Graph_Enriched_Search/`

Three notebooks using Strands Agents SDK with MCP to search a Neo4j knowledge graph:
- `01_vector_search_mcp.ipynb`: Semantic vector search via `strands.tools.mcp.MCPClient` using Bedrock Nova embeddings
- `02_graph_enriched_search_mcp.ipynb`: Vector search with graph traversal for enriched context (document metadata, neighboring chunks, connected entities)
- `03_fulltext_hybrid_search_mcp.ipynb`: Fulltext keyword search and agent-driven hybrid search with custom `@tool` wrappers

Notebooks 01-02 use Strands `MCPClient` with `streamablehttp_client` transport in a context-manager-per-query pattern. Notebook 03 additionally uses `lib/mcp_utils.py` (`MCPConnection` wrapping a raw MCP `ClientSession`) for persistent connections needed by custom async `@tool` functions.

### Lab 6 - GraphRAG
Location: `Lab_6_GraphRAG/`

Six notebooks covering data loading, embeddings, vector retrieval, graph-enhanced retrieval, full-text search, and hybrid search. Uses a forked neo4j-graphrag with Bedrock support (`neo4j-graphrag[bedrock]` from `neo4j-partners/neo4j-graphrag-python@bedrock-embeddings`).

### Lab 7 - MCP Agent
Location: `Lab_7_Neo4j_MCP_Agent/`

Two implementations (may be removed — largely redundant with Lab 4): one using LangGraph + langchain-mcp-adapters, one using Strands.

### Lab 8 - Aura Agents API
Location: `Lab_8_Aura_Agents_API/aura_agent_client.ipynb`

Contains `AuraAgentClient` class for OAuth2 authentication (client credentials flow) and agent invocation against `api.neo4j.io`.

## Shared Utilities

`lib/data_utils.py`: `Neo4jConfig`, `BedrockConfig` (pydantic-settings), `Neo4jConnection`, `DataLoader`, `get_embedder()`, `get_llm()`, `get_embedding()`, `get_schema()`, `split_text()`. Loads config from project-root `CONFIG.txt`.

`lib/mcp_utils.py`: `MCPConnection` — wraps raw MCP `ClientSession` over Streamable HTTP for persistent connections and `execute_query(cypher)`. Loads config from `CONFIG.txt` by default.

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

Lab 6 uses `pyproject.toml` at `Lab_6_GraphRAG/src/pyproject.toml`: Python 3.11+, neo4j-graphrag[bedrock] (from neo4j-partners fork), python-dotenv, pydantic-settings, nest-asyncio.
