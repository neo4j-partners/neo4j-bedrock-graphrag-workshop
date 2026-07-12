# Finalize Outline v2

Synthesis of `aws-outline.md`, `proposed-outline.md`, and `FIX.md` against the current working tree, verified 2026-07-11. The dated status block in `aws-outline.md` (2026-07-10) is now partly stale: the Nova to Titan code swap has since been completed. This document supersedes it.

---

## What Has Been Implemented and Changed

- **Directory renames:** Complete. `zz_Appendix_What_Is_An_Agent`, `Lab_2_Data_Pipeline`, `Lab_3_GraphRAG_Search`, `Lab_4_GraphRAG_Agent`, `Lab_5_Agent_Memory`, and `Lab_6_MCP_Server` all exist on disk alongside `Lab_0_Sign_In` and `Lab_1_Aura_Setup`.
- **Nova to Titan code swap:** Done. No `nova` references remain in any notebook or first-party `.py` file. `Lab_6_MCP_Server/lib/lab_5_data_utils.py` now calls `amazon.titan-embed-text-v2:0`, and the lib `data_utils.py` copies reference Titan.
- **Embedding regeneration script:** Added. `financial_data_load/regenerate_titan_embeddings.py` regenerates the seed `chunks.jsonl` vectors with Titan so stored and query-time embeddings share one vector space. This resolves the open question in `aws-outline.md`: regenerate, do not keep the Nova vectors.
- **Dimensions standardized:** 1024 across all config; no `1536` references remain.
- **Antora site restructured:** `part1`–`part4` and `lab0`–`lab6` pages plus `appendix-agent` pages exist under `site/modules/ROOT/pages/`, matching the four-part target.
- **Lab content sound:** Lab 3 (vector + vector-cypher retrievers), Lab 4 (Strands GraphRAG agent), and Lab 6 (three MCP notebooks) are present and functionally correct.
- **Strategic slides drafted:** `slides/` holds overview content and architecture diagrams.
- **`FIX.md` is superseded:** Its numbering (Lab 4 = neo4j-graphrag, Lab 5 = MCP, Lab 6 = pipeline) predates the revamp renumbering. Only its site-hygiene items (image cleanup, "under the hood" section, sample-queries link) are still relevant and are folded into the checklist below.

---

## Completed (2026-07-11)

The numbering, label, and repo-hygiene fixes below are done and verified.

- [x] Retitle and repoint `Lab_3_GraphRAG_Search/README.md` (Lab 4 → Lab 3; notebook list trimmed to the two retriever notebooks; "Next" links repointed to `Lab_4_GraphRAG_Agent`/`Lab_6_MCP_Server`).
- [x] Retitle `Lab_6_MCP_Server/README.md` (Lab 5 → Lab 6) and fix the "This completes Lab 5" summary cell (→ Lab 6).
- [x] Rename `Lab_6_MCP_Server/lib/lab_5_data_utils.py` → `lib/data_utils.py` and update its importers (`lib/__init__.py` and notebook 02).
- [x] Update root `README.md`: four-part lab numbers and new directory paths (tech stack and architecture were already on Titan).
- [x] Remove the empty `Lab_4_GraphRAG_Search/` directory.

Also completed in the same pass (not previously tracked):

- [x] Add `Lab_4_GraphRAG_Agent/README.md` (the lab had none; the root README linked to a bare directory).
- [x] Complete the lab-to-lab "Next Steps" flow (Lab 0 → 1, Lab 1 → 2/3, Lab 2 → 3) and correct the Lab 4 notebook's internal "Lab 3 / 04-05" narrative numbering.
- [x] Fix stale directory path comments in the `lib/data_utils.py` copies and the `financial_data_load/solution_srcs/` path builders.

---

## Labs Needing Fixes

### Setup / Lab 0 — Seed Load Not Self-Sufficient
- **Problem:** `setup/01_load_and_query.ipynb` loads only the unstructured layer (Chunk nodes, embeddings, vector index, `FROM_DOCUMENT`/`NEXT_CHUNK`/`FROM_CHUNK`) and `MATCH`es pre-existing structured nodes.
- **Required change:** Fold the structured CSV load from `financial_data_load/seed-data/` into this notebook so Lab 0 produces the complete graph on its own, as the `.adoc` pages already claim.
- **Import path:** Fix `from lib.data_utils import get_embedder`; there is no `lib/` under `setup/`.

### Lab 4 — AgentCore Deployment (Done) and Tool Code Duplication
- **Done:** `02_deploy_to_agentcore.ipynb` and `agentcore_deploy/` (agent.py + pyproject.toml) now exist, so attendees deploy and invoke over REST the exact agent from the opening demo.
- **Remaining problem:** The two retriever `@tool` functions and the agent assembly now live in two places, notebook `01_strands_graphrag_agent.ipynb` (cells 7 and 9) and `agentcore_deploy/agent.py`, and Lab 5 needs to reuse the same agent. There is no importable module.
- **Required change:** Extract the shared, reusable pieces into a module (see "Shared" below). Notebook 01 stays inline and untouched (it is the teaching surface); `agentcore_deploy/agent.py` and Lab 5 import the module.

### Shared — Reusable GraphRAG Agent Module and Config Fallback

**Why.** Lab 5 must reuse the Lab 4 GraphRAG agent, and `agentcore_deploy/agent.py` currently duplicates the tool code. Notebooks cannot be imported, so "taught inline" and "single source of truth" are mutually exclusive for the same code. The split below resolves that by consumer: the lab that *teaches* the code keeps it inline; the consumers that only *use* it import a module.

**New module: `Lab_4_GraphRAG_Agent/lib/graphrag_agent.py`.** Holds the reusable building blocks lifted verbatim from the current `agentcore_deploy/agent.py`, with no connection or config read at import time:
- `SYSTEM_PROMPT`, `RETRIEVAL_QUERY` constants and `format_record(record) -> RetrieverResultItem`.
- `build_retrievers(uri, username, password, region) -> tuple[neo4j.Driver, VectorRetriever, VectorCypherRetriever]` — verifies connectivity; caller owns the driver.
- `make_tools(vector_retriever, vector_cypher_retriever) -> list` — defines `semantic_search` / `graph_enriched_search` as `@tool` closures over the retrievers (no module-level globals).
- `build_agent(model_id, region, tools, *, system_prompt=SYSTEM_PROMPT, temperature=0.0) -> Agent`.
- `GraphRAGAgent` dataclass (`agent`, `tools`, `driver`) that owns the driver, with `close()` plus `__enter__` / `__exit__`.
- `build_graphrag_agent() -> GraphRAGAgent` — one-call convenience that reads config via `data_utils` (`Neo4jConfig()` / `BedrockConfig()`), then wires `build_retrievers -> make_tools -> build_agent`. No file parsing of its own.

**Consumers.**
- **Notebook 01 stays inline and untouched.** It is the canonical teaching moment (wrapping a retriever as a Strands `@tool`, assembling a `BedrockModel` agent). Optionally add a closing cell that imports the module and shows `inspect.getsource(semantic_search)` to make explicit that the packaged tools are the same code just built.
- **`agentcore_deploy/agent.py`** imports `build_retrievers`, `make_tools`, and `SYSTEM_PROMPT` from `graphrag_agent`, keeping its module-level warm-microVM init and its deploy-templated `NEO4J_URI`/etc. constants, but dropping the duplicated tool bodies. It does **not** call `build_graphrag_agent()`: the AgentCore runtime has no `CONFIG.txt` or `data_utils`, so it passes its own constants into `build_retrievers(...)`.
- **Lab 5** imports `build_graphrag_agent` and wraps the returned agent with the memory layer.

**Deploy bundling (best practice: build-time copy from a single source).** `direct_code_deploy` bundles only `agentcore_deploy/` (`source_path`), and the runtime has no `CONFIG.txt` or `lib/`. So: `lib/graphrag_agent.py` is canonical; `02_deploy_to_agentcore.ipynb` copies it into `agentcore_deploy/graphrag_agent.py` at deploy time (beside the existing constant-templating step), and that copy is gitignored. To keep the module importable in that runtime, its module top imports only `neo4j` / `neo4j_graphrag` / `strands` (all already in the deploy `pyproject.toml`); `build_graphrag_agent()` imports `data_utils` lazily inside the function so importing the module never requires it.

**Duplication note.** Notebook 01 and `graphrag_agent.py` intentionally hold the same ~90 lines of tool/agent code, the same accepted trade-off as the `data_utils.py` copies. Add a "keep in sync" comment to both so the invariant is explicit.

**Config fallback (all 5 `data_utils.py` copies).** Replace the dotenv-loading block with an explicit `if/elif/else` fallback so exactly one source is authoritative per run (no layered overrides), then let pydantic-settings (`Neo4jConfig` / `BedrockConfig`, `env_prefix=""`) validate required keys. Precedence is per context to avoid pointing the destructive `financial_data_load` harness at the workshop instance:
- The four lab copies (`Lab_2_Data_Pipeline`, `Lab_3_GraphRAG_Search`, `Lab_4_GraphRAG_Agent`, `Lab_6_MCP_Server`): load `CONFIG.txt` if it exists (workshop, authoritative), else `financial_data_load/.env` (local testing), else raise `FileNotFoundError` naming both.
- The `financial_data_load` copy: load its own `financial_data_load/.env` if it exists (test harness, authoritative), else `CONFIG.txt`, else raise.

### Lab 5 — Agent Memory Notebooks (Authored 2026-07-11; execution deferred)
- **Problem:** `Lab_5_Agent_Memory/` contained only a `README.md`.
- **Required change:** Author two hands-on notebooks on `neo4j-agent-memory` that add a memory layer to the (now importable) Lab 4 Strands GraphRAG agent: short-term conversational memory and long-term durable knowledge. Reasoning traces move to an optional site callout, not a notebook. Add the matching site page content.
- **Status:** Done. Both notebooks (`01_short_term_memory.ipynb`, `02_long_term_memory.ipynb`), `lib/memory_utils.py`, `lib/data_utils.py`, and `lib/__init__.py` are authored; `README.md`, `lab5.adoc`, and `lab5-instructions.adoc` are updated; the reasoning-traces "Going Further" callout is on the site page; nav already lists Lab 5. All code was statically verified (nbformat validity, `PyCF_ALLOW_TOP_LEVEL_AWAIT` syntax check, and every SDK attribute/label checked against `neo4j-agent-memory` v0.5.0 source). **Running the notebooks end-to-end against live Aura + Bedrock is deferred**, to be done in a workshop dry-run. Region is passed explicitly via `BedrockEmbedder(region_name=REGION)`, so no `AWS_REGION`/`REGION` rename was needed.

#### Implementation Plan

Reference implementation: `/Users/ryanknight/projects/neo4j-labs/agent-memory` (Python SDK `neo4j-agent-memory`, v0.5.0).

**Summary and scope.** Two notebooks that add `neo4j-agent-memory` on top of the Lab 4 Strands GraphRAG agent, running against the same Aura instance and Titan embeddings. Both are required and each covers one memory pillar.

- **Notebook 1, short-term memory:** The conversational recall layer. Resolves "their competitors" to Apple across turns.
- **Notebook 2, long-term memory:** The durable knowledge layer. Entities, preferences, and facts that survive across sessions.

Reasoning traces (the introspection and audit layer) are covered as an optional "Going Further" callout on the site page, illustrated with the one-hop audit Cypher, rather than as a third notebook.

Scope is deliberately capped: self-hosted bolt path against Aura, Titan embeddings for consistency, embedding-only memory config, and wrapper-driven integration. No tool-driven memory, dedup, enrichment, geospatial, reasoning-trace, or eval-harness depth.

**Key library facts this rests on.**
- **Async-only:** Every memory call is a coroutine. In notebooks, prefix with `await`.
- **Bolt path for Aura:** Construct `MemorySettings(neo4j=Neo4jConfig(uri=..., username=..., password=SecretStr(...)), embedding="bedrock/amazon.titan-embed-text-v2:0", extraction=ExtractionConfig(extractor_type=ExtractorType.NONE))`. No `llm=` is set: the core path is embedding-only and does manual writes, so the LLM extractor is not needed. The bolt path (direct Python driver) unlocks write-Cypher and `adopt_existing_graph`; the hosted NAMS path does not.
- **Embedding-only, extraction off:** `add_message` defaults to `extract_entities=True` / `extraction_mode="auto"`, which would invoke an LLM extractor. Setting `extraction=ExtractorType.NONE` removes that surface. The manual `add_entity` / `add_preference` / `add_fact` writes in Notebook 2 do not need an LLM either.
- **Two pillars used:** `memory.short_term` and `memory.long_term`, plus the top-level `memory.get_context(query, session_id=...)` that merges conversational and knowledge context.
- **Wrapper-driven integration:** Lab 5 wraps the imported Lab 4 agent by writing each turn with `memory.short_term.add_message(...)` and prepending `memory.get_context(...)` before each invocation. The library's `context_graph_tools` / `llm_provider_from_strands` Strands helpers are deliberately not used: explicit writes and context injection teach the mechanism more directly.

**Stage 1: Foundation and setup.**
- **Directory scaffold:** Add `01_short_term_memory.ipynb`, `02_long_term_memory.ipynb`, and `lib/data_utils.py` (copy of the Lab 4 helper for `get_llm`/embedder) under `Lab_5_Agent_Memory/`.
- **Dependency cell:** `%pip install "neo4j-agent-memory[bedrock]==0.5.0"` alongside the existing Lab 4 installs. Pin the version so the notebook APIs stay stable.
- **Config load:** Reuse `CONFIG.txt` keys `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `MODEL_ID`, `REGION` via the same `data_utils` fallback loader (CONFIG.txt, else `financial_data_load/.env`); construct one shared `MemorySettings` reused across both notebooks. **As built:** `MemoryClient` construction lives in a new `lib/memory_utils.py` (`build_memory_client` / `build_memory_settings`) rather than in `data_utils.py`, so that copy stays a faithful, syncable clone of the shared helper and the `neo4j-agent-memory` dependency (and the SDK's own `Neo4jConfig`, aliased `MemoryNeo4jConfig`) is isolated. Each notebook still opens with a one-line helper call.
- **Import the Lab 4 agent:** Call `build_graphrag_agent()` from `graphrag_agent.py` (see "Shared" above) so Lab 5 extends the known Lab 4 agent rather than rebuilding it. The one-line call is appropriate here because the agent is already-taught material; everything new in Lab 5 (the memory wrapping) stays fully visible.
- **Smoke test:** Open a `MemoryClient`, write one message, call `get_context`, confirm the connection and that memory nodes land in Aura.

**Stage 2: Notebook 1, short-term memory.**
- **Short-term write:** After each turn, `await memory.short_term.add_message(session_id, MessageRole.USER|ASSISTANT, content)` for both user and assistant messages.
- **Context injection:** Before each turn, `await memory.get_context(query, session_id=session_id)` and prepend it to the agent prompt.
- **The headline demo:** Run the three-question flow (Apple risk factors, then "their competitors", then "summarize what we discussed") to show cross-turn resolution.
- **Inspect in Neo4j:** A short Cypher cell showing `Conversation` and `Message` nodes beside the SEC graph.

**Stage 3: Notebook 2, long-term memory.**
- **Durable knowledge:** `add_preference`, `add_fact`, and `add_entity` (which returns an `(entity, dedup_result)` tuple) to persist facts beyond the conversation. `add_fact` takes its object via the `obj=` argument.
- **Retrieve in a fresh session:** `search_entities` and `long_term.get_context` to show knowledge surviving a new `session_id`.
- **Optional stretch cell:** `adopt_existing_graph(...)` to layer long-term memory over the existing SEC 10-K Company nodes. Mark clearly as optional so the core path stays short.
- **Inspect in Neo4j:** A Cypher cell showing `Entity`, `Preference`, and `Fact` nodes.

**Stage 4: Site page and finalize.**
- **Update README:** Replace the "in development" status; list the two notebooks and note that reasoning traces are covered as an optional site callout.
- **Site page:** Author the Part 3 Agent Memory `.adoc` page mirroring the two-notebook arc, wire it into `nav.adoc`.
- **Reasoning-traces callout:** Add an optional "Going Further" section to the site page framing traces as the observability and audit layer, illustrated with the one-hop audit query `MATCH (e:Entity {name:'Apple'})<-[:TOUCHED]-(s:ReasoningStep)<-[:HAS_STEP]-(rt:ReasoningTrace)`. Prose only, no notebook.
- **Checklist:** Tick the Lab 5 item below.

### Site — Missing Pages and FIX.md Carryovers
- **Missing pages:** No dedicated strategic-overview-slides page and no Production Path / Call to Action closer page exist, though the outline and slide content call for both.
- **From FIX.md (still valid):** Add a brief "What the Library Does Under the Hood" section to the neo4j-graphrag lab page; ensure a sample-queries page/link is wired; rename the mismatched MCP architecture image; delete orphaned images not referenced by any current page.

---

## Checklist of Fixes

**Highest priority (correctness / core promise)**
- [ ] Verify `financial_data_load/regenerate_titan_embeddings.py` has actually been run and `financial_data_load/seed-data/chunks.jsonl` now holds Titan vectors.
- [ ] Make Lab 0 seed load self-sufficient: fold structured CSV load into `setup/01_load_and_query.ipynb`.
- [ ] Fix the `lib.data_utils` import path in `setup/01_load_and_query.ipynb`.
- [x] Add AgentCore deployment (notebook + `agentcore_deploy/`) to `Lab_4_GraphRAG_Agent`.
- [ ] Extract `Lab_4_GraphRAG_Agent/lib/graphrag_agent.py`; point `agentcore_deploy/agent.py` and Lab 5 at it; leave notebook 01 inline.
- [ ] Apply the CONFIG.txt-else-`financial_data_load/.env` fallback loader to all 5 `data_utils.py` copies.
- [x] Author the `Lab_5_Agent_Memory` notebooks on `neo4j-agent-memory`. (Statically verified against SDK v0.5.0; end-to-end execution against live Aura + Bedrock deferred to a dry-run.)

**Hygiene**
- [ ] Add the strategic-overview-slides page and the Call to Action closer page to the site.
- [ ] Add "What the Library Does Under the Hood" section to the neo4j-graphrag lab page.
- [ ] Rename the mismatched MCP architecture image and delete orphaned images.
- [ ] Confirm sample-queries page and its cross-references resolve.
