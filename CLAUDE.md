# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a hands-on workshop teaching GraphRAG (Graph Retrieval-Augmented Generation) using Neo4j and AWS Bedrock. The workshop uses SEC 10-K financial filing data (companies, products, risk factors, financial metrics, executives, asset managers) and progresses from no-code tools to building custom agents.

## Workshop Structure

- **Part 1 (Labs 0-1)**: Getting started with Neo4j Aura and the SEC 10-K dataset
- **Part 2 (Labs 2-4)**: GraphRAG data pipeline, semantic search with neo4j-graphrag, and a Strands GraphRAG agent
- **Part 3 (Lab 5)**: Agent memory with Neo4j
- **Part 4 (Lab 6)**: Neo4j MCP server
- **Appendix**: What is an agent (basic Strands agent + AgentCore deployment)

## Key Configuration

All credentials are stored in `CONFIG.txt` at the project root (gitignored). The file uses dotenv format with keys: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `MODEL_ID`, `REGION`, `MCP_GATEWAY_URL`, `MCP_ACCESS_TOKEN`.

## Lab Code Patterns

### Lab 2 - GraphRAG Data Pipeline (Optional)
Location: `Lab_2_Data_Pipeline/`

Three notebooks covering data loading, embedding generation, and vector-cypher retrieval. Wipes the graph and rebuilds from `financial_data.json` (isolated sandbox). Uses neo4j-graphrag with Bedrock support (`neo4j-graphrag[bedrock]` from `neo4j-partners/neo4j-graphrag-python@bedrock-embeddings`).
- `01_data_loading.ipynb`, `02_embeddings.ipynb`, `03_vector_cypher_retriever.ipynb`

### Lab 3 - Semantic Search and GraphRAG (neo4j-graphrag Library)
Location: `Lab_3_GraphRAG_Search/`

Two notebooks using the neo4j-graphrag Python library with direct Python driver connections:
- `01_vector_retriever.ipynb`: `VectorRetriever` + `GraphRAG` pipeline for semantic question answering
- `02_vector_cypher_retriever.ipynb`: `VectorCypherRetriever` with custom Cypher retrieval query traversing companies, products, risk factors

Uses `lib/data_utils.py` for embedder/LLM helpers. All Neo4j access is via `neo4j.GraphDatabase.driver()` (no MCP). Both notebooks assume the seed load (Lab 0) already populated the graph with chunks, embeddings, and the vector index.

### Lab 4 - Strands GraphRAG Agent
Location: `Lab_4_GraphRAG_Agent/`

One notebook:
- `01_strands_graphrag_agent.ipynb`: Wraps both retrievers from Lab 3 as Strands `@tool` functions and builds an agent with `strands.models.BedrockModel` that chooses the retrieval strategy per question.

Uses `lib/data_utils.py` for embedder/LLM helpers.

### Lab 5 - Agent Memory with Neo4j
Location: `Lab_5_Agent_Memory/`

Net-new lab (in development) that adds `neo4j-agent-memory` on top of the Lab 4 Strands agent so it remembers across conversation turns. Uses the same Aura instance and Bedrock Titan embeddings.

### Lab 6 - Neo4j MCP Server
Location: `Lab_6_MCP_Server/`

Three notebooks using Strands Agents SDK with MCP to search a Neo4j knowledge graph:
- `01_intro_strands_mcp.ipynb`: MCP tool discovery, schema inspection, simple queries — pure MCP introduction
- `02_graph_enriched_search.ipynb`: Cypher Templates pattern — `@tool` wrappers with vector search + graph traversal via MCP
- `03_text2cypher_agent.ipynb`: Text2Cypher pattern — autonomous agent writes its own Cypher

Uses `lib/data_utils.py` for Bedrock embeddings (lightweight — no neo4j or neo4j-graphrag dependency). All MCP access via Strands `MCPClient` with `streamablehttp_client` transport. The MCP server is pre-deployed with full embeddings by the lab administrator.

### Appendix - What Is an Agent?
Location: `zz_Appendix_What_Is_An_Agent/`

Two notebooks (reference material, moved out of the main path):
- `01_basic_strands_agent.ipynb`: Uses `strands.Agent` with `strands.models.BedrockModel` and `@tool` decorator. Defines simple tools (get_current_time, add_numbers), creates an agent, tests it with queries including sample SEC filing data.
- `02_deploy_to_agentcore.ipynb`: Deploys the agent to AgentCore Runtime via `bedrock-agentcore-starter-toolkit` using `direct_code_deploy`. Agent code is pre-built in `agentcore_deploy/` (agent.py + pyproject.toml).

## Shared Utilities

`lib/data_utils.py`: `Neo4jConfig`, `BedrockConfig` (pydantic-settings), `Neo4jConnection`, `DataLoader`, `get_embedder()`, `get_llm()`, `get_embedding()`, `get_schema()`, `split_text()`. Loads config from project-root `CONFIG.txt`.

`lib/mcp_utils.py`: `MCPConnection` — wraps raw MCP `ClientSession` over Streamable HTTP for persistent connections and `execute_query(cypher)`. Loads config from `CONFIG.txt` by default.

`Lab_3_GraphRAG_Search/lib/data_utils.py` and `Lab_4_GraphRAG_Agent/lib/data_utils.py`: Copies of root `lib/data_utils.py` used by the Lab 3 and Lab 4 notebooks for `get_embedder()` and `get_llm()`.

`Lab_6_MCP_Server/lib/data_utils.py`: Lightweight `BedrockConfig` and `get_embedding()` only — no neo4j or neo4j-graphrag dependency. Used by Lab 6 MCP notebooks. Lab 6 uses Strands `MCPClient` directly for all MCP access.

`financial_data_load/lib/`: Local copies of `data_utils.py` and `mcp_utils.py` that load from `financial_data_load/.env` instead of the project-root `CONFIG.txt`. These are copied from the root `lib/` to simplify env loading for the test harness. If either copy is changed, the other must be updated to match.

## Knowledge Graph Schema

- **Nodes**: Company, Product, RiskFactor, AssetManager, Document, Chunk
- **Relationships**: OFFERS, FACES_RISK, COMPETES_WITH, PARTNERS_WITH, OWNS, FILED, FROM_DOCUMENT, NEXT_CHUNK, FROM_CHUNK
- **Vector Index**: `chunkEmbeddings` on Chunk.embedding (1024 dims for Titan Text Embeddings V2)
- **Fulltext Indexes**: `search_chunks` (on Chunk.text), `search_entities` (on Company/Product/RiskFactor names)

## Financial Data

Structured CSV seed data lives in `financial_data_load/seed-data/`: entity tables (companies, products, risk_factors, asset_managers), junction tables (company_products, company_risk_factors, asset_manager_companies), and relationship tables (company_competitors, company_partners).

## Running Notebooks

The notebooks are designed for AWS SageMaker Studio but work locally with:
1. Configure `CONFIG.txt` with Neo4j and AWS credentials
2. Install dependencies per notebook (uses `%pip install`)
3. Ensure AWS credentials are configured for Bedrock access

## Dependencies

Labs 2, 3, and 4 install neo4j-graphrag via `%pip install` in notebook cells: `neo4j-graphrag[bedrock]` from the neo4j-partners fork (`neo4j-partners/neo4j-graphrag-python@bedrock-embeddings`).
