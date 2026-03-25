# Workshop Restructure Plan

## Lab 5 — Questions / Comments

8. **Site documentation needs a full rewrite.** The current `lab5.adoc`, `lab5-instructions.adoc`, and `lab5-sample-queries.adoc` describe the old Lab 5 (neo4j-graphrag library, five notebooks, VectorRetriever/HybridRetriever, data pipeline from scratch). The new Lab 5 is an entirely different lab (Strands Agents + MCP Server, Text2Cypher pattern, three notebooks). These pages need to be rewritten from scratch, not patched. Same for `nav.adoc` which currently says "Lab 5: GraphRAG" — should become "Lab 5: Neo4j MCP Server" or similar.

Answer: For this can we copy and past the old content to create the new lab 5 content. It is archived in site/modules/ROOT/archive_pages

9. **Narrative arc / notebook ordering.** The current plan is:
   - Notebook 01: Intro to Strands + MCP (Text2Cypher — agent writes its own Cypher)
   - Notebook 02: Graph-Enriched Search (Cypher Templates — pre-written `@tool` queries with vector search)
   - Notebook 03: Strands Text2Cypher (Text2Cypher again — agent writes its own Cypher)

   This goes Text2Cypher → Templates → Text2Cypher, which is a confusing progression. Should the order be flipped so the narrative builds from structured (templates) to autonomous (text2cypher)? e.g.:
   - 01: Intro to Strands + MCP (discovery, basic tool listing)
   - 02: Graph-Enriched Search (Cypher Templates — structured, predictable)
   - 03: Text2Cypher (fully autonomous — agent writes its own Cypher)

   Or is the current ordering intentional because notebook 01 is simpler despite being text2cypher?

Answer: Great idea! Let's do that

10. **`lib/lab_4_data_utils.py` naming.** Notebook 02 imports `from lib.lab_4_data_utils import get_embedding`. When this moves to `Lab_5_MCP_Server/lib/`, having a file named `lab_4_data_utils.py` in Lab 5 is confusing. Rename to `data_utils.py` or `embedding_utils.py`?

Answer: Name it based on the lab to be sure it is not confused so lab_5 ...

11. **Config parsing inconsistency across notebooks.** Notebooks 01 and 02 use `load_dotenv("../CONFIG.txt")`, but Notebook 03 (from Lab 6) uses manual file parsing (`open("../CONFIG.txt")` + `line.split("=", 1)`). This is fragile (doesn't handle comments or blank lines) and inconsistent. Standardize all three to `load_dotenv`?

Answer: yes Standardize all three to `load_dotenv`?

12. **LangGraph notebook dropped — should the README/docs acknowledge it?** The old Lab 6 offered two framework options (LangGraph + Strands). Only the Strands notebook survives in the new Lab 5. The `neo4j_langgraph_mcp_agent.ipynb` is being deleted per the checklist. Should the new Lab 5 docs mention LangGraph as an alternative, or just present Strands as the single path?

Answer: Great idea! Yes, let's just mention it 

13. **Cross-lab framing mismatch.** The old Lab 6 `README.md` and notebook 03 frame themselves as "unlike Lab 4's Cypher Templates." After the restructure, all three notebooks live in the same lab (Lab 5), and the new Lab 4 is GraphRAG Search (direct Python driver, no MCP). The "How This Differs from Lab 4" framing needs rewriting to be self-contained within Lab 5 — e.g., "Notebook 03 contrasts with Notebook 02's template approach" rather than referencing a different lab.

Answer: Yes let's fix the framing 

14. **Notebook filenames.** The checklist says "Notebook 01", "Notebook 02", "Notebook 03" but doesn't specify target filenames. Proposed:
    - `01_intro_strands_mcp.ipynb`
    - `02_graph_enriched_search.ipynb`
    - `03_text2cypher_agent.ipynb`

    Or should they follow a different naming convention?

Yes that works great.


15. **Prerequisites — do students need chunks + embeddings loaded?** Notebook 02 runs vector search via MCP, which requires the `chunkEmbeddings` vector index and Chunk nodes with embeddings. That data gets loaded in new Lab 4 (notebook 01_load_and_query). Should Lab 5 prerequisites explicitly state "Complete Lab 4 Notebook 01" as a prerequisite? Or does Lab 5 work with just the structured graph from Lab 1 (in which case notebook 02 won't return vector results)?


Answer:  The lab administrator will provide an mcp server with full embeddings

16. **Notebook 01 scope vs. reordering.** The source notebook (`00_intro_strands_mcp.ipynb`) already does full Text2Cypher — the agent writes its own Cypher and runs schema discovery, traversals, aggregations. If the agreed ordering is intro → templates → text2cypher, notebook 01 becomes a Text2Cypher demo before students see Cypher Templates in notebook 02. Two options:
    - **Option A**: Trim notebook 01 to pure MCP introduction — tool discovery (`list_tools_sync`), schema inspection, maybe one simple read query — and save all "agent writes Cypher" for notebook 03.
    - **Option B**: Keep notebook 01 as-is (simple text2cypher). The narrative becomes: "see how easy it is for an agent to write Cypher → now see the template approach for reliability → now build a full autonomous agent." Text2Cypher appears twice but at different complexity levels.


Option A sounds great. Lets' keep it simple 

17. **Site docs source clarification.** The archived `lab6.adoc` and `lab6-instructions.adoc` contain the MCP/Text2Cypher content relevant to the new Lab 5. The archived `lab5.adoc`/`lab5-instructions.adoc` contain neo4j-graphrag retriever content (irrelevant). The base for the new Lab 5 site pages should be the archived Lab 6 docs, not the archived Lab 5 docs. Confirm?

Confirmed. That sounds great 
---

## Earlier Questions / Comments (Labs 1–4)

1. **Data conflict — single company vs. multi-company graph.** The current Lab 5 data pipeline (01_data_loading + 02_embeddings) builds a single-company graph from `financial_data.json` (Apple only, 12 products, 5 risks). But Labs 1-2 use the full multi-company graph loaded by `setup/populate` (6 companies, asset managers, competitors, partners). If the goal is one Aura instance across Labs 1-4, which dataset wins? Options:
   - **Option A**: New Lab 4 loads seed-embeddings on top of the existing multi-company graph (no wipe). Retriever notebooks query the richer graph.
   - **Option B**: New Lab 4 wipes and rebuilds from `financial_data.json` like current Lab 5 does — but then Labs 1-2 Aura Agents work is gone.
   - Recommend **Option A** — load chunks + embeddings from `setup/seed-embeddings` without clearing, so the structured layer from Labs 1-2 stays intact.

**Answer**: Option A.

**Issue — property name mismatch.** Lab 1 loads the structured graph with **camelCase** properties (`Document.documentId`, `Product.productId`, `Company.companyId`, `Document.accessionNumber`). The `test_roundtrip.py` loading code uses **snake_case** (`Document.document_id`, `.accession_number`). If Lab 4 notebook 01 uses the test_roundtrip pattern as-is, it will create **duplicate Document nodes** instead of linking chunks to the existing ones from Lab 1. Fix: Lab 4's load Cypher must MATCH existing nodes by their camelCase properties (e.g., `MATCH (d:Document {documentId: rel.document_id})`). Same for entity_chunks — MATCH Products by `productId`, RiskFactors by `riskId`.

**Answer**: I changed the loading code to use camelCase properties. Does that solve that problem? 

**Issue — retrieval query references.** The current Lab 5 VectorCypherRetriever query uses `doc.name`, but Lab 1's Document nodes don't have a `name` property — they have `accessionNumber` and `filingType`. The retrieval queries in new Lab 4 notebooks 02 and 03 need updating to use the multi-company graph's actual properties.

**Answer**: Yes, let's align to Lab 1 properties. Those should be consistent based on the initial setup/seed-data  everything has been updated to be consistent camelCase properties

2. **seed-embeddings completeness.** The `setup/seed-embeddings/` files have chunks, chunk-document links, chunk sequences, and entity-chunk links — but no pre-computed embedding vectors. Does the new Lab 4 notebook 01 need to generate embeddings (Bedrock call), or should we add pre-computed vectors to the seed data so Lab 4-01 is purely a load step?

**Answer**: Embedding vectors are in `setup/seed-embeddings/chunks.jsonl` (1024-dim). `setup/export_embeddings/test_roundtrip.py` has the load pattern.

3. **Lab 6 scope.** RESTRUCTURE.md lists Lab 6 as "Building a GraphRag Data pipeline" reusing current Lab 5 notebooks (01_data_loading, 02_embeddings, 04_vector_cypher_retriever, 05_hybrid_rag) plus `financial_data.json`. This is essentially the current Lab 5 reorganized. Should it wipe the graph and rebuild from scratch (isolated sandbox), or build on the existing data?

**Answer**: Wipe the graph.

4. **Dropped notebooks.** Confirming these are deleted, not moved:
   - `Lab_4_Graph_Enriched_Search/01_vector_search_mcp.ipynb`
   - `Lab_6_Advanced_Agents/neo4j_langgraph_mcp_agent.ipynb`

**Answer**: Correct.

5. **`setup/populate` tool missing.** The `setup/README.md` references a `setup/populate` CLI tool for loading the structured graph, but the directory doesn't exist. Lab 1 actually loads data via manual Cypher `LOAD CSV` statements from a CloudFront URL. Is `populate` still planned, or should the README be updated?

**Answer**: Deleted. Students use Lab_1_Aura_Setup/README.md Part 3.

6. ~~**CloudFront CSV headers vs. local seed-data headers.**~~ **Resolved** — Lab 1's Cypher already uses camelCase column references (`row.companyId`, `row.documentId`), matching the local seed-data CSV headers.

7. **test_roundtrip.py doesn't load entity_chunks.** The test creates Chunks, Documents, FROM_DOCUMENT, and NEXT_CHUNK — but skips entity_chunks.csv (FROM_CHUNK relationships linking Products/RiskFactors to Chunks). These are needed by the VectorCypherRetriever. **In progress** — user is adding this.

---

## Current State

```
Lab 0 - Sign In
Lab 1 - Aura Setup          (create instance, load via LOAD CSV from CloudFront)
Lab 2 - Aura Agents          (no-code, uses populated graph)
Lab 3 - Intro to Bedrock     (Strands agent, AgentCore deploy — no Neo4j)
Lab 4 - Graph Enriched Search (Strands + MCP, 3 notebooks)
Lab 5 - GraphRAG              (data load, embeddings, retrievers, hybrid — single company)
Lab 6 - Advanced Agents       (LangGraph + Strands MCP agents)
```

## Target State

```
Lab 0 - Sign In
Lab 1 - Aura Setup           (unchanged)
Lab 2 - Aura Agents          (unchanged)
Lab 3 - Intro to Bedrock     (unchanged)
Lab 4 - GraphRAG Search      (NEW — direct Neo4j python, same Aura instance)
Lab 5 - Neo4j MCP Server     (reshuffled from old Labs 4 + 6)
Lab 6 - GraphRAG Pipeline    (reshuffled from old Lab 5)
```

---

## Checklist

### Lab 4 — GraphRAG Search (new)

- [x] Create `Lab_4_GraphRAG_Search/` directory
- [x] **Notebook 01 — Load & Query**: `01_load_and_query.ipynb` — loads chunks + embeddings from `setup/seed-embeddings` (no wipe), creates vector index, loads entity_chunks (FROM_CHUNK for Product/RiskFactor/FinancialMetric/Company), verifies graph, runs test queries including raw vector search.
- [x] **Notebook 02 — Vector Retriever**: `02_vector_retriever.ipynb` — adapted from Lab 5, uses `../CONFIG.txt`, VectorRetriever + GraphRAG pipeline.
- [x] **Notebook 03 — Vector Cypher Retriever**: `03_vector_cypher_retriever.ipynb` — retrieval query updated to use `doc.accessionNumber` and `doc.filingType` (matching Lab 1 properties), traverses Company via FILED, includes FROM_CHUNK products.
- [x] Copy/adapt `Lab_5_GraphRAG/lib/` utilities needed by the new notebooks
- [ ] Verify all three notebooks run end-to-end against the same Aura instance used in Labs 1-2

### Lab 5 — Neo4j MCP Server Intro (reshuffled)

- [ ] Create `Lab_5_MCP_Server/` directory
- [ ] **Notebook 01**: Copy from `Lab_4_Graph_Enriched_Search/00_intro_strands_mcp.ipynb`
- [ ] **Notebook 02**: Copy from `Lab_4_Graph_Enriched_Search/02_graph_enriched_search_mcp.ipynb`
- [ ] **Notebook 03**: Copy from `Lab_6_Advanced_Agents/neo4j_strands_mcp_agent.ipynb`
- [ ] Update internal paths/references in all three notebooks

### Lab 6 — Building a GraphRAG Data Pipeline (reshuffled)

- [ ] Create `Lab_6_GraphRAG_Pipeline/` directory
- [ ] **Notebook 01 — Data Loading**: Copy from `Lab_5_GraphRAG/01_data_loading.ipynb`
- [ ] **Notebook 02 — Embeddings**: Copy from `Lab_5_GraphRAG/02_embeddings.ipynb`
- [ ] **Notebook 03 — Vector Cypher Retriever**: Copy from `Lab_5_GraphRAG/04_vector_cypher_retriever.ipynb`
- [ ] **Notebook 04 — Hybrid RAG**: Copy from `Lab_5_GraphRAG/05_hybrid_rag.ipynb`
- [ ] Copy `financial_data.json` into the new lab directory
- [ ] Copy/adapt `lib/` utilities
- [ ] Update internal paths/references

### Cleanup

- [ ] Delete old `Lab_4_Graph_Enriched_Search/` directory
- [ ] Delete old `Lab_5_GraphRAG/` directory
- [ ] Delete old `Lab_6_Advanced_Agents/` directory
- [ ] Delete dropped notebooks: `01_vector_search_mcp.ipynb`, `neo4j_langgraph_mcp_agent.ipynb`
- [ ] Update `CLAUDE.md` workshop structure and lab descriptions
- [ ] Update `setup/README.md` CONFIG.txt table (which labs need which keys)
- [ ] Update any cross-references between labs (next/previous links in notebook markdown)

### Site Documentation (Lab 4 complete)

- [x] Update `site/modules/ROOT/pages/lab4.adoc` — rewritten for GraphRAG Search (VectorRetriever, VectorCypherRetriever, two-layer graph, direct Python driver)
- [x] Update `site/modules/ROOT/pages/lab4-instructions.adoc` — new notebook table, updated prerequisites and next steps
- [x] Update `site/nav.adoc` — Lab 4 title changed from "Graph-Enriched Search" to "GraphRAG Search"
- [x] Cypher review — all queries use explicit WITH grouping, parameterized values, UNWIND batch ops, IF NOT EXISTS for indexes
- [x] `Lab_4_GraphRAG_Search/README.md` created
- [x] Antora site builds with no new errors
