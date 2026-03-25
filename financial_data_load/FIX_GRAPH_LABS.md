---
title: Notebook Quality Review
date: 2026-03-24
related: FIX_GRAPH.md (solution_srcs fixes)
---

# Notebook Quality Review

Review of all lab notebooks for the same issues found in `solution_srcs/`, plus any additional notebook-specific problems.

## Notebooks With No Issues

| Notebook | Pattern | Notes |
|----------|---------|-------|
| Lab 3: `01_basic_strands_agent.ipynb` | Strands SDK | Clean, no neo4j-graphrag usage expected |
| Lab 5: `01_data_loading.ipynb` | Raw Cypher | Parameterized Cypher, proper batch UNWIND |
| Lab 5: `03_vector_retriever.ipynb` | `VectorRetriever` + `GraphRAG` | Clean, idiomatic |
| Lab 5: `04_vector_cypher_retriever.ipynb` | `VectorCypherRetriever` + `GraphRAG` | Excellent side-by-side comparison |
| Lab 5: `06_hybrid_search.ipynb` | `HybridRetriever` + `HybridCypherRetriever` | Excellent — retriever selection guide, alpha tuning, result_formatter |
| Lab 6: `neo4j_langgraph_mcp_agent.ipynb` | LangGraph + MCP | Text2Cypher pattern, comprehensive system prompt |
| Lab 6: `neo4j_strands_mcp_agent.ipynb` | Strands + MCP | Same Text2Cypher pattern, more concise |

## Issues Found

### 1. Lab 5: `02_embeddings.ipynb`, cell `test-search` — Custom vector search instead of VectorRetriever

Cell `test-search` runs raw `db.index.vector.queryNodes` Cypher with manual `embedder.embed_query()`:

```python
query_embedding = embedder.embed_query(query)
session.run("""
    CALL db.index.vector.queryNodes('chunkEmbeddings', 3, $embedding)
    YIELD node, score
    ...
""", embedding=query_embedding)
```

This is the same issue fixed in `solution_srcs/01_02_embeddings.py`. The embedding generation and index creation cells are fine (uses `upsert_vectors()` from the library — actually better than the solution file). Only the test search cell needs updating.

**Fix:** Replace raw Cypher search with `VectorRetriever.search()`. Add note that the next notebook covers retrievers in depth.

### 2. Lab 5: `05_fulltext_search.ipynb` — Entire notebook teaches Lucene/raw fulltext

This is the notebook equivalent of `05_01_fulltext_search.py` which was rewritten to use `HybridRetriever` + `GraphRAG`. The notebook currently:
- Teaches Lucene operators (fuzzy `~`, wildcard `*`, boolean AND/NOT) via raw Cypher
- Uses `db.index.fulltext.queryNodes()` directly throughout
- Has no `HybridRetriever` usage
- Links to `06_hybrid_search.ipynb` as the "next" notebook

**Fix:** Rewrite to mirror the new `05_01_hybrid_rag.py` solution — HybridRetriever + GraphRAG comparing vector-only vs hybrid RAG answers. Rename to `05_hybrid_rag.ipynb`.

### 3. Lab 4: `03_fulltext_hybrid_search_mcp.ipynb` — REMOVED

Notebook and solution file deleted. Fulltext/hybrid search is covered properly in Lab 5 using `HybridRetriever`.

### 4. `main.py:493` and `README.md:250` — Stale references to renamed solution file

`main.py` line 493 still references `solution_srcs.05_01_fulltext_search` (renamed to `05_01_hybrid_rag`). `README.md` line 250 references `05_01_fulltext_search.py`.

**Fix:** Update module path and description in both files.

## Fix Plan — Status

| # | File | Action | Status |
|---|------|--------|--------|
| 1 | `Lab_5_GraphRAG/02_embeddings.ipynb` cell `test-search` | Replace raw vector Cypher with `VectorRetriever.search()`. Updated `search-header` markdown to reference retriever. | DONE |
| 2 | `Lab_5_GraphRAG/05_fulltext_search.ipynb` | Full rewrite to HybridRetriever + GraphRAG. Renamed to `05_hybrid_rag.ipynb`. | DONE |
| 3 | `Lab_4_Graph_Enriched_Search/03_fulltext_hybrid_search_mcp.ipynb` | REMOVED — notebook deleted, fulltext/hybrid covered in Lab 5 | REMOVED |
| 4 | `financial_data_load/main.py:493` | Updated module path and description to `05_01_hybrid_rag` / "Hybrid RAG" | DONE |
| 5 | `financial_data_load/README.md:250` | Updated filename and description | DONE |
| 6 | `Lab_5_GraphRAG/04_vector_cypher_retriever.ipynb` cell `summary` | Updated "Next" link and text from fulltext_search to hybrid_rag | DONE |
| 7 | `Lab_5_GraphRAG/README.md` | Updated notebook table and learning objectives | DONE |
| 8 | `site/modules/ROOT/pages/lab5-instructions.adoc` | Updated notebook table entry | DONE |
