# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a hands-on workshop teaching GraphRAG (Graph Retrieval-Augmented Generation) using Neo4j and AWS Bedrock. The workshop uses SEC 10-K financial filing data (companies, products, risk factors, financial metrics, executives, asset managers) and progresses from no-code tools to building custom agents.

## Workshop Structure

- **Part 1 (Labs 0-2)**: No-code exploration using Neo4j Aura console and Aura Agents visual builder
- **Part 2 (Labs 3-6)**: Python-based GraphRAG with LangGraph and neo4j-graphrag library
- **Part 3 (Labs 7-8)**: Advanced MCP (Model Context Protocol) agents and Aura Agents API

## Key Configuration

All credentials are stored in `CONFIG.txt` at the project root (gitignored). The file uses dotenv format:

```
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
REGION=us-east-1
```

## Lab Code Patterns

### Lab 3 - Basic LangGraph Agent + AgentCore Deployment
Location: `Lab_3_Intro_to_Bedrock_and_Agents/basic_langgraph_agent.ipynb`

Uses `ChatBedrockConverse` from langchain-aws with the ReAct pattern:
```python
from langchain_aws import ChatBedrockConverse
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
```

For cross-region inference profiles (MODEL_ID starting with `us.` or `global.`), derive base_model_id:
```python
if MODEL_ID.startswith("us.anthropic."):
    BASE_MODEL_ID = MODEL_ID.replace("us.anthropic.", "anthropic.")
```

Includes AgentCore deployment at the end using `bedrock-agentcore-starter-toolkit` and `direct_code_deploy`.

### Lab 4 - MCP-Based Retrieval
Location: `Lab_4_MCP_Retrieval/`

Three notebooks covering vector search, graph-enriched retrieval, and hybrid search through the Neo4j MCP server:
- `01_vector_search_mcp.ipynb`: Semantic vector search via MCP using Bedrock Titan embeddings
- `02_graph_enriched_search_mcp.ipynb`: Vector search with graph traversal for enriched context (document, chunks, entities)
- `03_fulltext_hybrid_search_mcp.ipynb`: Fulltext keyword search and agent-driven hybrid search with `@tool` wrappers

MCP connection pattern (notebooks 01-02 use inline setup; notebook 03 uses `lib/mcp_utils.py`):
```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
# Or via lib utilities:
from lib.mcp_utils import MCPConnection
from lib.data_utils import get_embedding
```

### Lab 6 - GraphRAG
Location: `Lab_6_GraphRAG/`

Six notebooks covering data loading, embeddings, vector retrieval, graph-enhanced retrieval, full-text search, and hybrid search.

Uses a forked neo4j-graphrag with Bedrock support:
```bash
pip install "neo4j-graphrag[bedrock] @ git+https://github.com/neo4j-partners/neo4j-graphrag-python.git@bedrock-embeddings"
```

Key utility classes in `data_utils.py`:
- `Neo4jConnection`: Manages driver connection using `Neo4jConfig` (pydantic-settings)
- `CSVLoader`: Loads structured data from `TransformedData/` CSV files
- `DataLoader`: Loads text data files
- `get_embedder()`: Returns `BedrockEmbeddings` configured from environment
- `get_llm()`: Returns `BedrockLLM` configured from environment
- `split_text()`: Wraps `FixedSizeSplitter` with async handling for Jupyter

Graph structure for SEC financial data:
```
(:Company) -[:OFFERS_PRODUCT]-> (:Product)
(:Company) -[:OFFERS_SERVICE]-> (:Service)
(:Company) -[:FACES_RISK]-> (:RiskFactor)
(:Company) -[:HAS_METRIC]-> (:FinancialMetric)
(:Company) -[:HAS_EXECUTIVE]-> (:Executive)
(:AssetManager) -[:OWNS]-> (:Company)
(:Company) -[:FILED]-> (:Document) <-[:FROM_DOCUMENT]- (:Chunk) -[:NEXT_CHUNK]-> (:Chunk)
```

### Lab 7 - MCP Agent
Location: `Lab_7_Neo4j_MCP_Agent/`

Two implementations:
- `neo4j_langgraph_mcp_agent.ipynb`: LangGraph + langchain-mcp-adapters
- `neo4j_strands_mcp_agent.ipynb`: Alternative using Strands framework

MCP connection pattern:
```python
from mcp.client.streamable_http import streamablehttp_client
from langchain_mcp_adapters.tools import load_mcp_tools
```

### Lab 8 - Aura Agents API
Location: `Lab_8_Aura_Agents_API/aura_agent_client.ipynb`

Contains `AuraAgentClient` class for OAuth2 authentication and agent invocation:
- Token URL: `https://api.neo4j.io/oauth/token`
- Uses client credentials flow with Basic Auth
- Tokens cached and auto-refreshed on 401

## Knowledge Graph Schema

The SEC financial dataset includes:
- **Nodes**: Company, Product, Service, RiskFactor, FinancialMetric, Executive, AssetManager, Document, Chunk
- **Relationships**: OFFERS_PRODUCT, OFFERS_SERVICE, FACES_RISK, HAS_METRIC, HAS_EXECUTIVE, OWNS, FILED, FROM_DOCUMENT, NEXT_CHUNK, FROM_CHUNK
- **Vector Index**: `chunkEmbeddings` on Chunk.embedding (1024 dims for Titan)
- **Fulltext Indexes**: `search_chunks` (on Chunk.text), `search_entities` (on Company/Product/RiskFactor names)

## Financial Data

Structured CSV data lives in `TransformedData/`:
- `companies.csv`, `products.csv`, `services.csv` — Entity data
- `risk_factors.csv`, `financial_metrics.csv`, `executives.csv`, `asset_managers.csv`
- Junction tables for relationships between entities
- `sec_filings.csv` — SEC filing metadata

## Running Notebooks

The notebooks are designed for AWS SageMaker Studio but work locally with:
1. Configure `CONFIG.txt` with Neo4j and AWS credentials
2. Install dependencies per notebook (uses `%pip install`)
3. Ensure AWS credentials are configured for Bedrock access

## Dependencies

Lab 6 uses `pyproject.toml` at `Lab_6_GraphRAG/src/pyproject.toml`:
- Python 3.11+
- neo4j-graphrag[bedrock] (from neo4j-partners fork)
- python-dotenv, pydantic-settings, nest-asyncio