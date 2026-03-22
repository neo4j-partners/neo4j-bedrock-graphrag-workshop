# Proposal: Align lab-neo4j-aws with the Manufacturing Workshop Structure

## Problem Statement

The `lab-neo4j-aws` workshop (financial/SEC domain) and the `neo4j-aws-manufacturing` workshop teach the same core concepts, GraphRAG with Neo4j and AWS Bedrock, but have diverged in structure, lab coverage, and tooling maturity.

The manufacturing workshop has three properties the financial workshop lacks:

1. **A complete lab progression.** Manufacturing covers no-code agents, a LangGraph foundations lab, consolidated GraphRAG, MCP integration, and Aura Agents API across seven labs with clean numbering (0-2, 4-7). The financial workshop jumps from Lab 3 to Lab 6, has no Bedrock/Agents intro lab, no MCP lab, and no API integration lab. Participants who complete the financial workshop leave without exposure to MCP or programmatic agent access.

2. **Consolidated GraphRAG content.** Manufacturing teaches data loading, embeddings, vector retrieval, vector-cypher retrieval, fulltext search, and hybrid search in a single lab (Lab 5) with six progressive notebooks and a shared `data_utils.py` utilities module. The financial workshop scatters this across four separate labs (6, 7, 8, 9) with duplicated setup code and no shared utilities.

3. **Operational infrastructure.** Manufacturing ships with a `setup/` directory containing CLI validation tools (populate, verify, test-queries), a `TransformedData/` directory with documented CSV data and an Excalidraw data model diagram, a `CONFIG.txt` template, and a `CLAUDE.md` for Claude Code users. The financial workshop has none of these.

The `new-workshops/` directory in the financial workshop contains an early prototype with Python solution scripts that predates the current notebook structure. It duplicates content from Labs 6-9 and adds confusion about which files are canonical.

## Proposed Solution

Restructure `lab-neo4j-aws` to match the manufacturing workshop's lab numbering, progression, and tooling while keeping the SEC 10-K financial domain. This is a structural alignment, not a domain change. The financial data, entity types (Company, Product, RiskFactor, FinancialMetric, Executive, AssetManager), and SEC-specific queries remain intact.

### What changes

**Lab restructuring.** Adopt the manufacturing workshop's seven-lab arc:

| New Lab | Source | Content |
|---------|--------|---------|
| Lab 0 | Existing Lab 0 | Sign in to AWS |
| Lab 1 | Existing Lab 1 | Neo4j Aura setup and backup restore |
| Lab 2 | Existing Lab 2 | No-code Aura Agents (Cypher templates, similarity search, Text2Cypher) |
| Lab 4 | **New** | Intro to Bedrock and Agents (LangGraph foundations, tool binding, ReAct pattern) |
| Lab 5 | Existing Labs 6, 7, 9 consolidated | GraphRAG: six notebooks (data loading, embeddings, vector retriever, vector-cypher retriever, fulltext search, hybrid search) |
| Lab 6 | **New** | Neo4j MCP Agent (LangGraph and Strands implementations, schema-first querying) |
| Lab 7 | **New** | Aura Agents API (OAuth2 flow, REST client, async batch queries) |

Lab 3 (Bedrock Setup) merges into Lab 4's prerequisites section rather than standing alone. Existing Lab 8 (Strands agents) is not a separate lab; the agent patterns move into Lab 6 as the Strands MCP implementation.

**Shared utilities module.** Create `data_utils.py` at the root or Lab 5 level, consolidating Neo4j connection management, Bedrock client initialization, CSV loading, and text splitting from `config.py` into a Pydantic-based module matching the manufacturing pattern (`Neo4jConfig`, `BedrockConfig`, `Neo4jConnection`). Remove `config.py`.

**Data and documentation directory.** Create `TransformedData/` with the SEC financial CSVs (companies, products, risk factors, financial metrics, executives, asset managers, and relationship junction tables), a `DATA_ARCHITECTURE.md` documenting the graph schema, and an Excalidraw data model diagram.

**Setup and validation tooling.** Create `setup/` with:
- A `populate/` CLI tool to load the financial knowledge graph and verify node/relationship counts
- A `solutions_bedrock/` validator CLI to test each GraphRAG retriever pattern against the financial data
- A root-level `CONFIG.txt` template listing all required and optional environment variables

**Configuration files.** Add `CLAUDE.md` with project-specific instructions for Claude Code users. Add slides directories to each lab.

**Cleanup.** Remove `new-workshops/` entirely. Its solution scripts are superseded by the consolidated Lab 5 notebooks and the `setup/solutions_bedrock/` validator. Remove `infra/cdk/` monitoring stack (CloudWatch dashboard/logs that are not used in workshops) but keep the Bedrock IAM stack.

### How this solves the problem

Participants follow the same progression regardless of which domain workshop they attend. Instructors can teach either workshop interchangeably. New labs (MCP, Aura API) close the coverage gaps. Consolidated GraphRAG content eliminates duplicated setup and lets participants see the full retrieval strategy spectrum in one sitting. Validation tooling lets instructors verify the environment before a session starts.

### Expected outcomes

- Seven labs with consistent numbering across both workshops
- Three new labs (Bedrock intro, MCP agent, Aura Agents API) added to the financial domain
- Four existing labs (6, 7, 8, 9) consolidated into one (Lab 5) with six notebooks
- One lab removed as standalone (Lab 3, merged into Lab 4 prerequisites)
- One directory removed (`new-workshops/`)
- Shared `data_utils.py` replacing `config.py`
- `TransformedData/`, `setup/`, `CONFIG.txt`, and `CLAUDE.md` added

## Requirements

### Lab structure

- Labs numbered 0, 1, 2, 4, 5, 6, 7 matching the manufacturing workshop. No Lab 3.
- Each lab directory contains a `README.md` with objectives, prerequisites, and step-by-step instructions.
- Each lab directory contains a `slides/` subdirectory for presentation materials.
- Labs 0-2 require no coding. Labs 4-7 use Jupyter notebooks.

### Lab 4: Intro to Bedrock and Agents

- Covers SageMaker Studio setup (or Codespace alternative).
- Introduces LangGraph's StateGraph, MessagesState, and conditional edges.
- Demonstrates tool definition with `@tool` decorator and `llm.bind_tools()`.
- Uses ChatBedrockConverse with inference profiles.
- Includes the Bedrock model access verification currently in Lab 3.

### Lab 5: GraphRAG

- Six notebooks in sequence: `01_data_loading`, `02_embeddings`, `03_vector_retriever`, `04_vector_cypher_retriever`, `05_fulltext_search`, `06_hybrid_search`.
- All notebooks import from a shared `data_utils.py` module.
- Data loading uses CSVs from `TransformedData/` for structured data and text files for SEC filing content.
- Embeddings use Amazon Titan Text Embeddings V2 (1024 dimensions).
- Each retriever notebook includes a retriever selection guide comparing when to use each pattern.
- `data_utils.py` uses Pydantic settings for `Neo4jConfig` and `BedrockConfig`.

### Lab 6: Neo4j MCP Agent

- README explains MCP concepts (transport, tool discovery, schema-first querying).
- Two notebook implementations: one with LangGraph, one with Strands Agents SDK.
- Uses Neo4j MCP Server tools (`get-schema`, `read-cypher`).
- Documents the AWS deployment architecture (AgentCore Gateway, Secrets Manager).

### Lab 7: Aura Agents API

- Covers OAuth2 client credentials flow against `api.neo4j.io`.
- Builds a typed Python client with Pydantic response models.
- Demonstrates token caching, auto-refresh, and async batch queries.
- Shows how to invoke the Lab 2 agent programmatically.

### Data and tooling

- `TransformedData/` contains CSV files for all node types and relationships in the SEC financial graph, plus `DATA_ARCHITECTURE.md` and an Excalidraw diagram.
- `setup/populate/` loads the knowledge graph from CSVs and verifies counts.
- `setup/solutions_bedrock/` validates each GraphRAG retriever against the loaded data.
- `CONFIG.txt` at root lists all environment variables with comments grouping them by lab.

### Cleanup

- `new-workshops/` directory removed completely.
- `config.py` removed after `data_utils.py` replaces it.
- `setup_env.py` functionality absorbed into `setup/populate/` CLI.
- Labs 3, 6, 7, 8, 9 directories removed after content migrates to new structure.

## Implementation Plan

### Phase 1: Analysis

- [x] Inventory all notebooks, code, and data across existing Labs 3, 6, 7, 8, 9
- [x] Map each notebook's content to the target lab structure
- [x] Identify SEC-domain adaptations needed for new labs (4, 6, 7) based on manufacturing originals
- [x] Document the financial graph schema for `DATA_ARCHITECTURE.md`

**Mapping (completed):**

| Existing | Target | Content |
|----------|--------|---------|
| Lab 6/01_data_loading | Lab 5/01_data_loading | Document→Chunk graph creation |
| Lab 6/02_embeddings | Lab 5/02_embeddings | Titan V2 embeddings + vector index |
| Lab 7/01_vector_retriever | Lab 5/03_vector_retriever | VectorRetriever + GraphRAG |
| Lab 7/02_vector_cypher_retriever | Lab 5/04_vector_cypher_retriever | Graph-enhanced retrieval |
| Lab 9/01_fulltext_search | Lab 5/05_fulltext_search | Fulltext indexes + operators |
| Lab 9/02_hybrid_search | Lab 5/06_hybrid_search | HybridRetriever + alpha tuning |
| Lab 6/03_entity_extraction | Dropped (uses SimpleKGPipeline, not in scope) |
| Lab 6/04_full_dataset | Dropped (pre-built graph loaded in Lab 1) |
| Lab 6/05_advanced_queries | Dropped (advanced queries, optional) |
| Lab 7/03_text2cypher | Lab 6 MCP agent (schema-first Text2Cypher via MCP) |
| Lab 8/01-03_agents | Lab 6 (Strands agent patterns move to MCP notebook) |
| Lab 3 Bedrock setup | Lab 4 prerequisites section |

### Phase 2: Implementation

- [x] Create `TransformedData/` with SEC financial CSVs, schema docs, and Excalidraw diagram
  - 14 CSV files (8 node types + 4 junction tables + sec_filings)
  - DATA_ARCHITECTURE.md with full schema documentation
  - Placeholder Excalidraw diagram
- [x] Create `data_utils.py` with Pydantic-based Neo4j and Bedrock configuration
  - Neo4jConfig, BedrockConfig, Neo4jConnection, DataLoader, CSVLoader
  - get_embedder(), get_llm(), get_schema(), split_text()
- [x] Build Lab 4 (Bedrock and Agents intro) adapted from manufacturing, using financial domain examples
  - README.md with SageMaker setup instructions
  - basic_langgraph_agent.ipynb (23 cells)
  - load_sample_data.py + sample_financial_data.txt
- [x] Consolidate Labs 6, 7, 9 into new Lab 5 with six notebooks importing `data_utils.py`
  - 01_data_loading through 06_hybrid_search (6 notebooks)
  - financial_data.txt, src/pyproject.toml, README.md
- [x] Build Lab 6 (MCP Agent) adapted from manufacturing, with LangGraph and Strands notebooks querying financial data
  - neo4j_langgraph_mcp_agent.ipynb (21 cells)
  - neo4j_strands_mcp_agent.ipynb (18 cells)
  - README.md with MCP architecture and deployment docs
- [x] Build Lab 7 (Aura Agents API) adapted from manufacturing, invoking the financial domain agent from Lab 2
  - aura_agent_client.ipynb (34 cells) with AuraAgentClient class
  - README.md with OAuth2 flow and credentials guide
- [x] Create `setup/populate/` CLI for financial knowledge graph loading
  - 6 Python modules: config, schema, loader, main, formatting, samples
  - Typer CLI: load, verify, clean, samples commands
- [x] Create `setup/solutions_bedrock/` CLI for retriever validation
  - 5 Python modules: config, data, retrievers, main
  - Typer CLI: test (6-phase validation), chat (interactive GraphRAG)
- [x] Add `CONFIG.txt`, `CLAUDE.md`, and `slides/` directories
  - CONFIG.txt with all env vars grouped by lab
  - CLAUDE.md with repo overview and code patterns
  - slides/ in Labs 0, 1, 2, 4, 5, 6, 7
- [x] Remove `new-workshops/`, `config.py`, `setup_env.py`, and old lab directories
  - Removed: new-workshops/, Lab_3_Bedrock_Setup/, Lab_6_Knowledge_Graph/,
    Lab_7_Retrievers/, Lab_8_Agents/, Lab_9_Hybrid_Search/, config.py, setup_env.py

### Missing Images

The following images are referenced in documentation but do not exist yet. These need to be captured as screenshots from the live UI.

**Lab 0 — Sign In** (`Lab_0_Sign_In/images/`):
- `aws_signin.png` — AWS Console sign-in page with Account ID field

**Lab 1 — Aura Signup** (`Lab_1_Aura_Setup/images/`):
- `find_marketplace.png` — AWS Console search bar showing "marketplace" search
- `search_neo4j.png` — AWS Marketplace search results for "neo4j aura"
- `neo4j_aura_listing.png` — Neo4j AuraDB Professional product listing
- `continue_subscribe.png` — Product details page with "Continue to Subscribe" button
- `accept_terms.png` — Terms and conditions acceptance dialog
- `setup_account.png` — "Set Up Your Account" link after subscription
- `signup_aura.png` — Neo4j Aura sign-up form
- `select_marketplace_org.png` — Organization dropdown showing Marketplace Organization
- `instance_running.png` — Aura console showing instance with green "Running" status

**Lab 1 — Explore** (`Lab_1_Aura_Setup/images/`):
- `build_pattern.png` — Explore search bar with AssetManager → OWNS → Company → FACES_RISK → RiskFactor pattern
- `company_graph.png` — Graph visualization showing asset managers, companies, and risk factors
- `centrality_results.png` — Graph with nodes sized by degree centrality scores

**Lab 2 — Aura Agents** (`Lab_2_Aura_Agents/images/`):
- `agent_config.png` — Agent creation form with name, description, and system instructions
- `shared_risks_tool.png` — Cypher template tool configuration for find_shared_risks
- `apple_query.png` — Agent response to Apple company overview question
- `apple_reasoning.png` — Agent tool selection reasoning panel
- `ai_ml_query.png` — Agent response to AI/ML semantic search question
- `risk_factors.png` — Agent response showing Text2Cypher risk factor query

### Phase 3: Verification

- [ ] Run `setup/populate/` against a fresh Aura instance and verify node/relationship counts
- [ ] Execute all six Lab 5 notebooks end-to-end
- [ ] Execute both Lab 6 notebooks (LangGraph and Strands MCP agents)
- [ ] Execute Lab 7 notebook against a running Aura Agent
- [ ] Run `setup/solutions_bedrock/` validation suite
- [ ] Verify no references to removed files or old lab numbers remain
- [ ] Walk through Labs 0-2 README instructions manually
