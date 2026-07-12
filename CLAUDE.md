# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a hands-on workshop teaching GraphRAG (Graph Retrieval-Augmented Generation) using Neo4j and AWS Bedrock. The workshop uses SEC 10-K financial filing data (companies, products, risk factors, financial metrics, executives, asset managers) and progresses from no-code tools to building custom agents.

## Workshop Structure

- **Part 1 (Labs 0-1)**: Getting started with Neo4j Aura and the SEC 10-K dataset
- **Part 2 (Labs 2-4)**: GraphRAG data pipeline, semantic search with neo4j-graphrag, and a Strands GraphRAG agent
- **Part 3 (Lab 5)**: Agent memory with Neo4j
- **Part 4 (Lab 6)**: Neo4j MCP server

## Key Configuration

All credentials are stored in `CONFIG.txt` at the project root (gitignored). The file uses dotenv format with keys: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `MODEL_ID`, `REGION`, `MCP_GATEWAY_URL`, `MCP_ACCESS_TOKEN`.

## Lab Code Patterns

### Lab 2 - GraphRAG Data Pipeline (Optional)
Location: `Lab_2_Data_Pipeline/`

One notebook covering data loading and embedding generation together. Wipes the graph and rebuilds from `financial_data.json` (isolated sandbox). Uses neo4j-graphrag with Bedrock support (`neo4j-graphrag[bedrock]>=1.18.0` from PyPI). Retrieval is deferred to Lab 3.
- `01_chunking_and_embeddings.ipynb`

### Lab 3 - Semantic Search and GraphRAG (neo4j-graphrag Library)
Location: `Lab_3_GraphRAG_Search/`

Two notebooks using the neo4j-graphrag Python library with direct Python driver connections:
- `01_vector_retriever.ipynb`: `VectorRetriever` + `GraphRAG` pipeline for semantic question answering
- `02_vector_cypher_retriever.ipynb`: `VectorCypherRetriever` with custom Cypher retrieval query traversing companies, products, risk factors

Uses `lib/data_utils.py` for embedder/LLM helpers. All Neo4j access is via `neo4j.GraphDatabase.driver()` (no MCP). Both notebooks assume the seed load (Lab 1) already populated the graph with chunks, embeddings, and the vector index.

### Lab 4 - Strands GraphRAG Agent
Location: `Lab_4_GraphRAG_Agent/`

Two notebooks:
- `01_strands_graphrag_agent.ipynb`: Wraps both retrievers from Lab 3 as Strands `@tool` functions (`semantic_search` over the VectorRetriever and `graph_enriched_search` over the VectorCypherRetriever) and builds an agent with `strands.models.BedrockModel` that chooses the retrieval strategy per question.
- `02_deploy_to_agentcore.ipynb`: Deploys the agent to Amazon Bedrock AgentCore. The deployment package lives in `agentcore_deploy/` (`agent.py` with the `BedrockAgentCoreApp` + `@app.entrypoint` handler and warm-microVM init, plus `.bedrock_agentcore.yaml`).

Uses `lib/data_utils.py` for embedder/LLM helpers.

### Lab 5 - Agent Memory with Neo4j
Location: `Lab_5_Agent_Memory/`

Adds `neo4j-agent-memory` on top of the Lab 4 Strands agent so it remembers across conversation turns. Uses the same Aura instance and Bedrock Titan embeddings.
- `01_short_term_memory.ipynb`: short-term, within-conversation memory.
- `02_long_term_memory.ipynb`: long-term memory. Extraction is OFF (`ExtractionConfig(extractor_type=ExtractorType.NONE)`, no extractor LLM); knowledge is written explicitly via `add_entity`/`add_fact`/`add_preference` and recalled via `search_entities`/`search_facts`/`search_preferences`.

### Lab 6 - Neo4j MCP Server
Location: `Lab_6_MCP_Server/`

One notebook using Strands Agents SDK with MCP to search a Neo4j knowledge graph:
- `01_mcp_text2cypher_agent.ipynb`: MCP tool discovery and schema inspection, then an autonomous Text2Cypher agent that writes its own Cypher

All MCP access via Strands `MCPClient` with `streamablehttp_client` transport. The MCP server is pre-deployed with full embeddings by the lab administrator. Its deployment code lives in the separate `neo4j-partners/aws-starter` repository (`neo4j-agentcore-mcp-server/`).

## Shared Utilities

There is no root `lib/` package. Each lab and the loader ships its own local `lib/` so notebooks can import helpers directly.

`data_utils.py` provides `Neo4jConfig`, `BedrockConfig` (pydantic-settings), `Neo4jConnection`, `DataLoader`, `get_embedder()`, `get_llm()`, `get_embedding()`, `get_schema()`, `split_text()`. It exists as five copies:
- `Lab_2_Data_Pipeline/lib/`, `Lab_3_GraphRAG_Search/lib/`, `Lab_4_GraphRAG_Agent/lib/`, `Lab_5_Agent_Memory/lib/`: load config from the project-root `CONFIG.txt`. These four are identical except for a one-line provenance comment.
- `financial_data_load/lib/`: loads from `financial_data_load/.env` instead of `CONFIG.txt` (so the destructive load/rebuild harness never touches the workshop instance); otherwise the same helpers.

Any change to shared logic (for example the `MODEL_ID` default) must be applied to all five copies to keep them in sync.

`mcp_utils.py` (`MCPConnection`, which wraps a raw MCP `ClientSession` over Streamable HTTP for persistent connections and `execute_query(cypher)`) exists only in `financial_data_load/lib/`, loading config from `financial_data_load/.env`.

## Knowledge Graph Schema

- **Nodes**: Company, Product, RiskFactor, AssetManager, Document, Chunk
- **Relationships**: OFFERS, FACES_RISK, COMPETES_WITH, PARTNERS_WITH, OWNS, FILED, FROM_DOCUMENT, NEXT_CHUNK, FROM_CHUNK
- **Vector Index**: `chunkEmbeddings` on Chunk.embedding (1024 dims for Titan Text Embeddings V2)
- **Fulltext Indexes**: `search_entities` (on Company/Product/RiskFactor names) is created by the Lab 1 seed load; `search_chunks` (on Chunk.text) is not in the base graph and is created by an explicit `CREATE FULLTEXT INDEX` step in the Lab 3 sample queries (`lab3-sample-queries.adoc`)

## Financial Data

Structured CSV seed data lives in `financial_data_load/seed-data/`: entity tables (companies, products, risk_factors, asset_managers), junction tables (company_products, company_risk_factors, asset_manager_companies), and relationship tables (company_competitors, company_partners).

## Running Notebooks

The notebooks are designed for AWS SageMaker Studio but work locally with:
1. Configure `CONFIG.txt` with Neo4j and AWS credentials
2. Install dependencies per notebook (uses `%pip install`)
3. Ensure AWS credentials are configured for Bedrock access

## Dependencies

Labs 2, 3, and 4 install neo4j-graphrag via `%pip install` in notebook cells: `neo4j-graphrag[bedrock]>=1.18.0` from PyPI. Bedrock support is upstreamed and released as of 1.18.0, so the neo4j-partners git fork is no longer used.
