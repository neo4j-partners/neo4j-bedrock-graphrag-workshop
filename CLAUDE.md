# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a hands-on workshop teaching GraphRAG (Graph Retrieval-Augmented Generation) using Neo4j and AWS Bedrock. The workshop uses SEC 10-K financial filing data (companies, products, risk factors, financial metrics, executives, asset managers) and progresses from no-code tools to building custom agents.

## Workshop Structure

- **Part 1 (Labs 0-2)**: No-code exploration using Neo4j Aura console and Aura Agents visual builder
- **Part 2 (Labs 3-4)**: Python-based GraphRAG with Strands Agents SDK and neo4j-graphrag library
- **Part 3 (Labs 5-6)**: MCP agents and GraphRAG data pipeline

## Key Configuration

All credentials are stored in `CONFIG.txt` at the project root (gitignored). The file uses dotenv format with keys: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `MODEL_ID`, `REGION`, `MCP_GATEWAY_URL`, `MCP_ACCESS_TOKEN`.

## Lab Code Patterns

### Lab 3 - Basic Strands Agent + AgentCore Deployment
Location: `Lab_3_Intro_to_Bedrock_and_Agents/`

Two notebooks:
- `01_basic_strands_agent.ipynb`: Uses `strands.Agent` with `strands.models.BedrockModel` and `@tool` decorator. Defines simple tools (get_current_time, add_numbers), creates an agent, tests it with queries including sample SEC filing data.
- `02_deploy_to_agentcore.ipynb`: Deploys the agent to AgentCore Runtime via `bedrock-agentcore-starter-toolkit` using `direct_code_deploy`. Agent code is pre-built in `agentcore_deploy/` (agent.py + pyproject.toml).

### Lab 4 - GraphRAG Search
Location: `Lab_4_GraphRAG_Search/`

Three notebooks using the neo4j-graphrag Python library with direct Python driver connections:
- `01_load_and_query.ipynb`: Load chunks + embeddings from `setup/seed-embeddings`, create vector index, link entities to chunks via `FROM_CHUNK` relationships, run test queries
- `02_vector_retriever.ipynb`: `VectorRetriever` + `GraphRAG` pipeline for semantic question answering
- `03_vector_cypher_retriever.ipynb`: `VectorCypherRetriever` with custom Cypher retrieval query traversing companies, products, risk factors

Uses `lib/data_utils.py` for embedder/LLM helpers. All Neo4j access is via `neo4j.GraphDatabase.driver()` (no MCP). The same Aura instance from Labs 1-2 is used — notebook 01 adds the unstructured layer on top of the existing structured graph.

### Lab 5 - Neo4j MCP Server
Location: `Lab_5_MCP_Server/`

Three notebooks using Strands Agents SDK with MCP to search a Neo4j knowledge graph:
- `01_intro_strands_mcp.ipynb`: MCP tool discovery, schema inspection, simple queries — pure MCP introduction
- `02_graph_enriched_search.ipynb`: Cypher Templates pattern — `@tool` wrappers with vector search + graph traversal via MCP
- `03_text2cypher_agent.ipynb`: Text2Cypher pattern — autonomous agent writes its own Cypher

Uses `lib/lab_5_data_utils.py` for Bedrock embeddings (lightweight — no neo4j or neo4j-graphrag dependency). All MCP access via Strands `MCPClient` with `streamablehttp_client` transport. The MCP server is pre-deployed with full embeddings by the lab administrator.

### Lab 6 - GraphRAG Pipeline
Location: `Lab_6_GraphRAG_Pipeline/`

Three notebooks covering data loading, embedding generation, and vector-cypher retrieval. Wipes the graph and rebuilds from `financial_data.json` (isolated sandbox). Uses neo4j-graphrag with Bedrock support (`neo4j-graphrag[bedrock]` from `neo4j-partners/neo4j-graphrag-python@bedrock-embeddings`).

## Shared Utilities

`lib/data_utils.py`: `Neo4jConfig`, `BedrockConfig` (pydantic-settings), `Neo4jConnection`, `DataLoader`, `get_embedder()`, `get_llm()`, `get_embedding()`, `get_schema()`, `split_text()`. Loads config from project-root `CONFIG.txt`.

`lib/mcp_utils.py`: `MCPConnection` — wraps raw MCP `ClientSession` over Streamable HTTP for persistent connections and `execute_query(cypher)`. Loads config from `CONFIG.txt` by default.

`Lab_4_GraphRAG_Search/lib/data_utils.py`: Copy of root `lib/data_utils.py` used by Lab 4 notebooks for `get_embedder()` and `get_llm()`.

`Lab_5_MCP_Server/lib/lab_5_data_utils.py`: Lightweight `BedrockConfig` and `get_embedding()` only — no neo4j or neo4j-graphrag dependency. Used by Lab 5 MCP notebooks. Lab 5 uses Strands `MCPClient` directly for all MCP access.

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

Labs 4 and 6 install neo4j-graphrag via `%pip install` in notebook cells: `neo4j-graphrag[bedrock]` from the neo4j-partners fork (`neo4j-partners/neo4j-graphrag-python@bedrock-embeddings`).
