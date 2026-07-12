# Site / Slides / Labs Alignment

This document records where the workshop's three surfaces disagree or have gaps, then lays out a plan to fix them. The three surfaces are:

- **Labs** — the runnable notebooks and lab READMEs under `Lab_*/` (the source of truth for what attendees actually do).
- **Site** — the Antora instruction pages under `site/modules/ROOT/pages/` (what attendees read and follow).
- **Slides** — the eight Marp decks under `slides/overview-*/` (conceptual background).

Scope note: the slide decks are conceptual by design, so API-level omissions there are expected and not treated as defects. The meaningful problems are contradictions and gaps in the **site instructions**, plus a few **concepts** the decks under-represent.

---

## Part 1: What Is Out of Alignment

### Tier 1 — Contradictions (site and labs actively disagree; one side is stale)

These are the highest priority: attendees following the site will hit instructions that do not match what the lab does.

| # | Area | Lab says | Site says | Verified |
|---|------|----------|-----------|----------|
| C1 | **Lab 0 Bedrock model access** | Access is enabled by default in commercial regions; "no longer a separate model access request step" (`Lab_0_Sign_In/README.md:69`). Includes a Playground smoke test. | "Model access is not enabled by default. You enable access to both models as part of this lab" (`lab0.adoc:20`); walks through Manage model access → Save changes (`lab0-instructions.adoc:59-64`). No Playground step. | Yes (both files read) |
| C2 | **Lab 5 long-term memory mechanism** | `ExtractionConfig(extractor_type=ExtractorType.NONE)` — extraction OFF, no extractor LLM; notebooks write memory explicitly via `add_entity`/`add_fact`/`add_preference` (`Lab_5_Agent_Memory/lib/memory_utils.py:78`). | Long-term memory "holds entities and facts **extracted from the conversation over time** ... it distills durable knowledge" (`lab5.adoc:33`, `part3.adoc:7`). | Yes (both files read) |
| C3 | **Lab 1 Aura tier** | AuraDB Free, "permanent free instance with no expiry" via `console-preview.neo4j.io` (`Lab_1_Aura_Setup/Aura_Free_Trial.md:4-15`). | Professional tier, 14-day free trial, with Graph Analytics = Plugin and Vector-optimized = Enabled, 4 GB RAM (`lab1-instructions.adoc:48-76`). | Reported |
| C4 | **Lab 1 exploration algorithm** | Degree Centrality + "size nodes based on scores" (`Lab_1_Aura_Setup/EXPLORE.md:56-94`). | Louvain community detection + "Unique colors" (`lab1-explore.adoc:61-86`). | Reported |
| C5 | **Lab 4 tool framing** | Wraps **two** tools: `semantic_search` (VectorRetriever) and `graph_enriched_search` (VectorCypherRetriever); the point is the agent choosing between them (`Lab_4_GraphRAG_Agent/lib/graphrag_agent.py:124-176`). | Frames Lab 4 as wrapping "**the** `VectorCypherRetriever`" (singular) (`lab4.adoc:3,9,20`; `lab4-instructions.adoc:9`). | Reported |
| C6 | **Lab 3 retrieval query** | Chunk-scoped `collect { ... }` subqueries for products AND risks, taught to "avoid cartesian products" (notebook 02; `graphrag_agent.py:44`). | Shows a different query using `OPTIONAL MATCH (company)-[:FACES_RISK]->(risk)` (`lab3.adoc:72-80`). | Reported |
| C7 | **Claude model version** | `lib/data_utils.py:63` defaults `MODEL_ID` to `us.anthropic.claude-sonnet-4-5-...` (Sonnet 4.5). | `Lab_0_Sign_In/README.md:62` tells users to select "Claude Sonnet 4.6" in the Playground. Site names no specific version. | Yes |

### Tier 2 — Substantive lab content absent from the site instructions

Real techniques the notebooks teach that the site never mentions.

- **L0-a** Lab 0: Bedrock Playground smoke test + the GraphRAG test prompt (`Lab_0_Sign_In/README.md:58-69`).
- **L0-b** Lab 0: the whole troubleshooting section — Access Denied → `AmazonBedrockFullAccess`, first-invoke Marketplace/payment/one-time Anthropic use-case form, region availability (`README.md:71-84`).
- **L3-a** Lab 3: `result_formatter=format_record` + `RetrieverResultItem` (separates chunk text from metadata; default "serializes the entire record into a single string") (notebook 02; `graphrag_agent.py:59`).
- **L3-b** Lab 3: `return_context=True` / `retriever_config={'top_k': N}` and inspecting `response.retriever_result.items` (notebooks 01/02).
- **L3-c** Lab 3: `notifications_min_severity='OFF'` driver gotcha for deprecated `db.index.vector.queryNodes` warnings (both notebooks).
- **L4-a** Lab 4: inspecting the ReAct history via `agent.messages` (`toolUse`/`toolResult` blocks) (notebook 01).
- **L4-b** Lab 4: the `BedrockAgentCoreApp` + `@app.entrypoint` handler contract (`agentcore_deploy/agent.py`).
- **L4-c** Lab 4: warm-microVM init pattern — build retrievers once at module level, fresh `Agent` per request to avoid state leakage (`agent.py:42-89`).
- **L4-d** Lab 4: specific `.bedrock_agentcore.yaml` fields (`direct_code_deploy`, `PYTHON_3_13`, `linux/arm64`, network/protocol/observability) (notebook 02).
- **L5-a** Lab 5: `search_facts` and `search_preferences` retrieval methods; site only shows `search_entities` (`02_long_term_memory.ipynb`).
- **L5-b** Lab 5: `threshold` semantics — 0.7 default, lowered to 0.5 and why (notebook 02).
- **L6-a** Lab 6: Text2Cypher system-prompt guardrails — modern Cypher rules (`elementId()`, `COUNT{}`, `EXISTS{}`, `$param`) and read-only allowlist / mandatory `LIMIT` / `COALESCE` (`01_mcp_text2cypher_agent.ipynb` cell 7).

### Tier 3 — Concepts under-represented in the slide decks

- **S-a** agent-agentcore deck: the agent *selecting between two retrieval strategies* (deck currently implies one graph tool).
- **S-b** agent-agentcore deck: how AgentCore deployment actually works (app/entrypoint handler + warm-microVM), described only at "what it does" level.
- **S-c** mcp deck: the Text2Cypher prompt-engineering technique (guardrails / modern-Cypher rules); schema-first is covered but this is not.

### Tier 4 — Expected / not a problem (no action unless requested)

API minutiae correctly confined to the notebooks: `upsert_vectors`/`create_vector_index` call shapes, `elementId()` id-ordering, `adopt_existing_graph` argument signature and report fields, `add_entity` dedup `.action`, `agentcore` CLI flags, ARM64 cross-compile detail, deployment permission preflight, dependency pins, MCP auth-header/context-manager wiring.

---

## Part 2: Plan to Fix and Align

### Open decisions (need your input before execution)

The plan branches on these. They are asked as questions alongside this document.

- **D1 (→ C1, L0-a, L0-b):** For the workshop's AWS accounts, is Bedrock model access enabled by default, or must attendees enable it manually? Determines whether the site's "enable model access" procedure is replaced by a verification-only step.
- **D2 (→ C3):** Which Aura path is canonical — AuraDB Free (permanent) or Professional (14-day trial with Graph Analytics plugin + vector-optimized)? Affects whether GDS/vector features are available for the explore lab.
- **D3 (→ C4):** Standardize the Lab 1 exploration on Louvain, Degree Centrality, or keep both?
- **D4 (→ C7):** Correct Claude model — Sonnet 4.5 (matches code) or 4.6 (matches Lab 0 README)?
- **D5 (backfill scope):** How much of Tier 2 (site gaps) and Tier 3 (slide concepts) to add — contradictions only, contradictions + substantive site gaps, or contradictions + gaps + slide concepts?

For every contradiction except the ones above, the plan treats the **runnable notebook/library code as the source of truth** and updates the site to match (C2 Lab 5 extraction, C5 Lab 4 two-tool, C6 Lab 3 query are all "fix the site").

### Execution with parallel agents

The work decomposes cleanly because each lab's site pages and each slide deck are separate files, so there is almost no write contention. Recommended orchestration (a coordinator plus a fan-out of content agents, mirroring the pattern in `fix-slides.md`):

**Phase 0 — Coordinator (serial):** lock in D1–D5 answers, then write per-agent briefs. The coordinator exclusively owns any shared/duplicated files so agents never collide on them:
- `lib/data_utils.py` and its copies (`Lab_3_GraphRAG_Search/lib/`, `Lab_4_GraphRAG_Agent/lib/`, `financial_data_load/lib/`) for the C7 model-version fix — these must stay byte-identical per `CLAUDE.md`, so one owner.
- `slides/scripts/build-slides.mjs` and `slides/README.md` if any deck metadata changes.

**Phase 1 — Content agents (parallel, disjoint file sets):**

| Agent | Owns | Fixes |
|-------|------|-------|
| A — Lab 0 site | `lab0.adoc`, `lab0-instructions.adoc` | C1; add L0-a Playground smoke test, L0-b troubleshooting |
| B — Lab 1 site | `lab1-instructions.adoc`, `lab1-explore.adoc`, `Aura_Free_Trial.md` / `EXPLORE.md` if reconciled | C3, C4 |
| C — Lab 3 site | `lab3.adoc`, `lab3-instructions.adoc` | C6; add L3-a formatter/`RetrieverResultItem`, L3-b context inspection, L3-c driver gotcha |
| D — Lab 4 site | `lab4.adoc`, `lab4-instructions.adoc` | C5; add L4-a `agent.messages`, L4-b app handler, L4-c warm-microVM, L4-d yaml fields |
| E — Lab 5 site | `lab5.adoc`, `lab5-instructions.adoc`, `part3.adoc` | C2; add L5-a `search_facts`/`search_preferences`, L5-b threshold |
| F — Lab 6 site | `lab6.adoc`, `lab6-instructions.adoc` | add L6-a Text2Cypher guardrails |
| G — agent-agentcore deck | `slides/overview-agent-agentcore/01-agent-agentcore-slides.md` | S-a two-tool selection, S-b deployment concept |
| H — mcp deck | `slides/overview-mcp/01-mcp-slides.md` | S-c Text2Cypher prompt concept |

Agents B–H are gated on D-answers only where noted (B needs D2/D3; A needs D1; the model-version fix is coordinator-owned per D4). Agents C, D, E, F, G, H can start as soon as D5 sets scope.

**Phase 2 — Coordinator (serial, last):** apply the C7 model-version fix across the `data_utils.py` copies; rebuild slides under Node 22 (`PATH="/opt/homebrew/opt/node@22/bin:..." node scripts/build-slides.mjs`) and rebuild the Antora site (`cd site && npm run build`); run the verification sweep below.

**Concurrency guidance:** launch A–H in a single batch (they touch disjoint files). Keep the two shared-file categories (data_utils copies, build-slides.mjs/README) off-limits to the fan-out and handled only by the coordinator, exactly as `fix-slides.md` did with its registration files.

### Verification

- Grep the site build for the removed contradictions (e.g. no "extracted from the conversation" in `lab5.html`; Lab 0 access wording matches D1; Lab 4 mentions both tools).
- Confirm the Lab 3 site query matches the notebook's `collect{}` retrieval query.
- Rebuild slides (Node 22) and confirm the two decks render with the new concept slides and zero em-dashes.
- Confirm all `data_utils.py` copies remain identical after the model-version fix.
- Rebuild the site and confirm no unresolved xrefs.

### Deferred (Tier 4)

Not in scope unless you opt in via D5; listed in Part 1 Tier 4.
