# Workshop Restructure Plan

## Questions / Comments

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
