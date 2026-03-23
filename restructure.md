# Workshop Restructure Proposal

## Decisions

| Question | Answer |
|----------|--------|
| Current Lab 3 slot? | Open — no conflict |
| AgentCore deployment integration style? | Fully integrated into the notebook flow |
| New Lab 4 notebook 2 through MCP or direct? | MCP |
| Current Lab 6 GraphRAG notebooks? | Leave as-is for now |
| `bedrock_agentcore_mcp_agent.ipynb` fate? | Dropped — its content is redundant with new Lab 4 |
| Data loading in new Lab 4? | Assume data is loaded and available via the MCP server |

---

## Current State

**Lab 4** ("Intro to Bedrock and Agents") has three notebooks:
- `basic_langgraph_agent.ipynb` — builds a simple ReAct agent with Bedrock and LangGraph using local tools
- `bedrock_agentcore_mcp_agent.ipynb` — connects the agent to Neo4j via MCP
- `deploy_agentcore_agent.ipynb` — deploys the MCP agent to AgentCore Runtime

**Lab 6** ("GraphRAG") has a series of notebooks including:
- `03_vector_retriever.ipynb` — semantic vector search against Neo4j directly
- `04_vector_cypher_retriever.ipynb` — graph-enriched vector search using Cypher traversal

---

## Changes Made

### New Lab 3: Intro to Bedrock and Agents

`Lab_3_Intro_to_Bedrock_and_Agents/`

Copied from the current Lab 4 with only `basic_langgraph_agent.ipynb` and its supporting files (load_sample_data.py, sample_financial_data.txt, images/, slides/, README.md).

The notebook was updated with AgentCore deployment fully integrated at the end (sections 9-13). The flow is: build a basic agent with simple tools → test it locally → package it for AgentCore → deploy → invoke the deployed agent via CLI and boto3 → cleanup.

The deployed agent wraps the same `get_current_time` and `add_numbers` tools in a `BedrockAgentCoreApp` handler.

### New Lab 4: MCP-Based Retrieval

`Lab_4_MCP_Retrieval/`

**Notebook 1 — `01_vector_search_mcp.ipynb`**

Semantic vector search through MCP. The notebook generates query embeddings using Bedrock Titan, passes them to a ReAct agent, and the agent executes vector search Cypher (`db.index.vector.queryNodes`) through the MCP server's `execute-query` tool. Includes multiple search queries at different `top_k` values.

**Notebook 2 — `02_graph_enriched_search_mcp.ipynb`**

Graph-enriched vector search through MCP. Creates two agents for side-by-side comparison:
- Vector-only agent — returns just chunk text and score
- Graph-enriched agent — follows `FROM_DOCUMENT` and `NEXT_CHUNK` relationships to include document metadata and neighboring chunk context

Also includes a Q&A agent that synthesizes answers from graph-enriched retrieval results.

### Dropped

`bedrock_agentcore_mcp_agent.ipynb` — its MCP connection pattern and general Cypher querying are covered by the new Lab 4 notebooks. No unique content that isn't absorbed elsewhere.

---

## Status

- [x] Create `Lab_3_Intro_to_Bedrock_and_Agents/` with supporting files
- [x] Merge AgentCore deployment into Lab 3 notebook (sections 9-13)
- [x] Create `Lab_4_MCP_Retrieval/` directory
- [x] Create `01_vector_search_mcp.ipynb` — vector search via MCP
- [x] Create `02_graph_enriched_search_mcp.ipynb` — graph-enriched search via MCP
- [x] Update this document with status

### Also completed

- Deleted `Lab_4_Intro_to_Bedrock_and_Agents/` — content fully redistributed to Lab 3 and Lab 4
- Updated Lab 3 `README.md` — title, description, and next steps
- Updated all cross-references in `README.md`, `CLAUDE.md`, `CONFIG.txt`, `setup/README.md`, `Lab_1_Aura_Setup/Neo4j_Aura_Signup.md`, `Lab_2_Aura_Agents/README.md`, `Lab_8_Aura_Agents_API/README.md`

### Not changed

- `Lab_6_GraphRAG/` — left as-is per decision
