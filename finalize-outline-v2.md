# Finalize Outline v2

Synthesis of `aws-outline.md`, `proposed-outline.md`, and `FIX.md` against the current working tree, verified 2026-07-11. The dated status block in `aws-outline.md` (2026-07-10) is now partly stale: the Nova to Titan code swap has since been completed. This document supersedes it.

---

## What Has Been Implemented and Changed

- **Directory renames:** Complete. `zz_Appendix_What_Is_An_Agent`, `Lab_2_Data_Pipeline`, `Lab_3_GraphRAG_Search`, `Lab_4_GraphRAG_Agent`, `Lab_5_Agent_Memory`, and `Lab_6_MCP_Server` all exist on disk alongside `Lab_0_Sign_In` and `Lab_1_Aura_Setup`.
- **Nova to Titan code swap:** Done. No `nova` references remain in any notebook or first-party `.py` file. `Lab_6_MCP_Server/lib/lab_5_data_utils.py` now calls `amazon.titan-embed-text-v2:0`, and the lib `data_utils.py` copies reference Titan.
- **Embedding regeneration script:** Added. `setup/regenerate_titan_embeddings.py` regenerates the seed `chunks.jsonl` vectors with Titan so stored and query-time embeddings share one vector space. This resolves the open question in `aws-outline.md`: regenerate, do not keep the Nova vectors.
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
- **Required change:** Fold the structured CSV load from `setup/seed-data/` into this notebook so Lab 0 produces the complete graph on its own, as the `.adoc` pages already claim.
- **Import path:** Fix `from lib.data_utils import get_embedder`; there is no `lib/` under `setup/`.

### Lab 4 — Missing AgentCore Deployment
- **Problem:** `Lab_4_GraphRAG_Agent/` has only `01_strands_graphrag_agent.ipynb`, no `agentcore_deploy/` and no `bedrock-agentcore-starter-toolkit` references.
- **Required change:** Add the AgentCore deployment notebook and `agentcore_deploy/` artifact so attendees deploy and invoke over REST the exact agent shown in the opening demo. Reference material lives in `zz_Appendix_What_Is_An_Agent/agentcore_deploy/`.

### Lab 5 — Agent Memory Notebooks Unauthored
- **Problem:** `Lab_5_Agent_Memory/` contains only a `README.md`.
- **Required change:** Author the hands-on notebooks on `neo4j-agent-memory`: configure `MemoryClient` against the existing Aura instance, wrap the Lab 4 agent to write turns to short-term memory, and call `get_context()` before each invocation. Add the matching site page content.

### Site — Missing Pages and FIX.md Carryovers
- **Missing pages:** No dedicated strategic-overview-slides page and no Production Path / Call to Action closer page exist, though the outline and slide content call for both.
- **From FIX.md (still valid):** Add a brief "What the Library Does Under the Hood" section to the neo4j-graphrag lab page; ensure a sample-queries page/link is wired; rename the mismatched MCP architecture image; delete orphaned images not referenced by any current page.

---

## Checklist of Fixes

**Highest priority (correctness / core promise)**
- [ ] Verify `setup/regenerate_titan_embeddings.py` has actually been run and `setup/seed-data/chunks.jsonl` now holds Titan vectors.
- [ ] Make Lab 0 seed load self-sufficient: fold structured CSV load into `setup/01_load_and_query.ipynb`.
- [ ] Fix the `lib.data_utils` import path in `setup/01_load_and_query.ipynb`.
- [ ] Add AgentCore deployment (notebook + `agentcore_deploy/`) to `Lab_4_GraphRAG_Agent`.
- [ ] Author the `Lab_5_Agent_Memory` notebooks on `neo4j-agent-memory`.

**Hygiene**
- [ ] Add the strategic-overview-slides page and the Call to Action closer page to the site.
- [ ] Add "What the Library Does Under the Hood" section to the neo4j-graphrag lab page.
- [ ] Rename the mismatched MCP architecture image and delete orphaned images.
- [ ] Confirm sample-queries page and its cross-references resolve.
