# Final Review

Consolidation of `finalize-outline-v2.md`, `aws-outline.md`, `proposed-outline.md`, and `agentcore-deploy.md`, verified against the working tree on 2026-07-11. This supersedes all four for status tracking. The prior docs disagree on numbering and carry stale open items; the verified state below is authoritative.

## Verdict

The workshop is substantially implemented and high quality. The four-part structure, the Nova to Titan swap, the reusable GraphRAG agent module, the AgentCore deployment, and the Lab 5 memory notebooks are all in place and internally consistent. Remaining work is small and falls into two buckets: one correctness bug in a Lab 5 demo cell, and a set of site and content-hygiene items. There is also one structural deviation from the outline worth a decision.

## Implemented and Verified

- **Directory renames.** All labs on disk: `Lab_0_Sign_In`, `Lab_1_Aura_Setup`, `Lab_2_Data_Pipeline`, `Lab_3_GraphRAG_Search`, `Lab_4_GraphRAG_Agent`, `Lab_5_Agent_Memory`, `Lab_6_MCP_Server`, `zz_Appendix_What_Is_An_Agent`.
- **Nova to Titan code swap.** No `nova` references remain in any first-party `.py` or `.ipynb` file. All embedding config is 1024 dimensions; no `1536` references outside a clarifying comment in `Lab_5_Agent_Memory/lib/memory_utils.py`.
- **Seed embeddings.** `financial_data_load/seed-data/chunks.jsonl` holds 1024-dim vectors, matching Titan V2 and the `chunkEmbeddings` index. `regenerate_titan_embeddings.py` is present.
- **Reusable agent module.** `Lab_4_GraphRAG_Agent/lib/graphrag_agent.py` exists (8.5K). `agentcore_deploy/agent.py` imports `SYSTEM_PROMPT`, `build_retrievers`, `make_tools` from it rather than duplicating the tool bodies.
- **AgentCore deployment.** `Lab_4_GraphRAG_Agent/02_deploy_to_agentcore.ipynb`, `agentcore_deploy/agent.py`, and `agentcore_deploy/pyproject.toml` are all present, fulfilling the "deploy the agent you built" promise.
- **Lab 5 memory notebooks.** Both `01_short_term_memory.ipynb` and `02_long_term_memory.ipynb`, plus `lib/memory_utils.py`, `lib/data_utils.py`, and `lib/__init__.py`, are authored. Lab 5 is registered in `setup/run_notebooks.py`.
- **Config fallback.** Applied across the `data_utils.py` copies per `finalize-outline-v2.md`.
- **Antora site.** Four-part `nav.adoc` is complete: Part 1 (Lab 0, Lab 1), Part 2 (Lab 2 optional, Lab 3, Lab 4), Part 3 (Lab 5), Part 4 (Lab 6), plus the appendix.
- **"Under the hood" section.** Present at `site/modules/ROOT/pages/lab3.adoc:82`. This FIX.md carryover is done.
- **Sample queries.** Both `sample-queries.adoc` (under Lab 1) and `lab3-sample-queries.adoc` (under Lab 3) exist and are wired into nav.

## Work Remaining

**Correctness**
- Fix the empty recall demo in `Lab_5_Agent_Memory/02_long_term_memory.ipynb`. Cell 8 runs `search_entities("technology company")` and `long_term.get_context(...)` at the default `threshold=0.7`, and `adopt_existing_graph` is in cell 10, after the recall. The demo prints nothing. Lower the threshold, use query text closer to the stored entity, or move the adopt cell before the recall.
- Confirm the 1024-dim vectors in `chunks.jsonl` were produced by Titan V2, not merely truncated Nova output. The dimension matches, but model identity cannot be verified from the file alone. Run one query-time embedding and check similarity against a stored vector.

**Site pages**
- Add the strategic-overview-slides page. Slide content exists under `slides/` but is not surfaced as a workshop page.
- Add the Production Path / Call to Action closer page. No page for it exists in the Antora site.
- Rename the mismatched MCP architecture image and delete orphaned images not referenced by any current page.

**Structural decision**
- Reconcile Part 1 with the outline. The outline specifies Lab 0 as Aura free-trial sign-up plus the full seed load, and Lab 1 as graph exploration only. The repo instead has Lab 0 as AWS sign-in and Lab 1 as "Set Up Aura and Load the Graph" plus exploration. The seed load lives in Lab 1, and `Lab_0_Sign_In/README.md` still reads as AWS sign-in with stale "Labs 4-7" numbering. Decide whether to keep the current split or move to the outline's version, then align the Lab 0 README.

## Stale Items in Prior Docs

- `finalize-outline-v2.md` and `aws-outline.md` both list "make `setup/01_load_and_query.ipynb` self-sufficient" and "fix its `lib.data_utils` import path." That notebook no longer exists. Seed loading moved to Lab 1 instructions plus admin S3/CloudFront hosting via `setup/setup_s3_seed_data.sh`, with the data and regeneration tooling in `financial_data_load/`. These two items are obsolete as written and are replaced by the Part 1 structural decision above.
- `finalize-outline-v2.md` lists the "under the hood" section as pending. It is done.
