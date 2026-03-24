---
title: solution_srcs Quality Review
date: 2026-03-24
reviewed_against: /Users/ryanknight/projects/neo4j-graphrag-python
---

# solution_srcs/ Quality Review

Review of `financial_data_load/solution_srcs/` against the neo4j-graphrag-python library to identify custom reimplementations, incorrect usage, and quality issues.

## Files Using neo4j-graphrag Well (no issues)

| File | Pattern | Notes |
|------|---------|-------|
| `02_01_vector_retriever.py` | `VectorRetriever` + `GraphRAG` | Clean, idiomatic usage |
| `02_02_vector_cypher_retriever.py` | `VectorCypherRetriever` | Good `retrieval_query` patterns, modern Cypher |
| `02_03_text2cypher_retriever.py` | `Text2CypherRetriever` + `get_schema()` | Custom prompt justified for modern Cypher compliance |
| `05_02_hybrid_search.py` | `HybridRetriever` + `HybridCypherRetriever` | Excellent — uses `result_formatter`, alpha comparison, all library features |
| `01_03_entity_extraction.py` | `SimpleKGPipeline` | Clean pipeline usage |
| `config.py` | `BedrockNovaEmbeddings` + `BedrockLLM` | Correct library types |

## Issues & Decisions

### 1. `01_02_embeddings.py:67-78` — Custom vector search reimplements VectorRetriever

**DECISION: FIX** — Replace `vector_search()` and `demo_search()` with `VectorRetriever`.

### 2. `05_01_fulltext_search.py` — Complete rewrite needed

**DECISION: REWRITE** — Remove all raw fulltext/Lucene content. Replace with a HybridRetriever showcase.

`05_02_hybrid_search.py` already covers: basic HybridRetriever, alpha comparison, HybridCypherRetriever with graph traversal + result_formatter, and search method comparison. So `05_01` needs to be complementary, not duplicative.

**Options for 05_01 rewrite:**

**Option A: HybridRetriever + GraphRAG (full RAG pipeline)**
- Use `HybridRetriever` as the retriever inside `GraphRAG` for LLM-generated answers
- Compare hybrid RAG answers vs vector-only RAG answers (using same query)
- Shows the practical payoff: hybrid retrieval produces better answers
- Parallels the progression from `02_01` (VectorRetriever + GraphRAG) to hybrid
- Complements `05_02` which focuses on retrieval patterns without GraphRAG

**Option B: HybridRetriever + metadata filtering**
- Demonstrate `filters` parameter for pre-filtering by node properties before search
- Show how to combine hybrid search with graph-aware filtering
- Practical pattern for multi-tenant or scoped search use cases

**Option C: HybridRetriever + ToolsRetriever (LLM-driven tool selection)**
- Use `ToolsRetriever` to let the LLM choose between VectorRetriever, HybridRetriever, and Text2CypherRetriever based on query type
- Shows the library's most advanced retrieval pattern
- Each retriever is converted to a Tool via `convert_to_tool()`

**Recommendation: Option A** — it's the most natural progression (02_01 does vector+GraphRAG, 05_01 does hybrid+GraphRAG, 05_02 dives deep into hybrid mechanics). It demonstrates the practical value of hybrid search in a way participants can immediately see.

### 3. `04_03:219` — String interpolation in fulltext Cypher

**DECISION: FIX** — Use parameterized `$search_term` instead of f-string interpolation.

### 4. `02_02_vector_cypher_retriever.py:13-14` — Wrong type hints

**DECISION: FIX** — Replace `OpenAIEmbeddings`/`OpenAILLM` imports and type hints with `BedrockNovaEmbeddings`/`BedrockLLM`.

### 5. `config.py:91-132` — Dead code: `get_embedding()` and supporting types

**DECISION: DELETE**

Research findings:
- `_NovaEmbedding`, `_NovaEmbeddingResponse`, `_bedrock_client` are only used inside `solution_srcs/config.py` itself
- The Lab 4 files (`04_01`, `04_02`, `04_03`) import `get_embedding` from `lib.data_utils`, NOT from `config.py`
- `lib/data_utils.py:86` already has a clean `get_embedding()` that delegates to `get_embedder().embed_query()`
- `config.py`'s `get_embedding()` is dead code — no callers

Delete: `get_embedding()`, `_NovaEmbedding`, `_NovaEmbeddingResponse`, `_bedrock_client`, and the `json`/`boto3` imports they require.

### 6. `01_02_embeddings.py:34-42` — Session-per-chunk embedding loop

**DECISION: FIX** — Batch with `UNWIND`.

## Fix Plan — Status

| # | File | Action | Status |
|---|------|--------|--------|
| 1 | `config.py` | Delete dead code: `get_embedding()`, `_NovaEmbedding`, `_NovaEmbeddingResponse`, `_bedrock_client`, unused `json`/`boto3`/`BaseModel` imports. Clean stale docstring referencing `get_embedding()`. | DONE |
| 2 | `02_02_vector_cypher_retriever.py` | Replace `OpenAIEmbeddings`/`OpenAILLM` imports and type hints (lines 13-14, 60, 81) with `BedrockNovaEmbeddings`/`BedrockLLM` | DONE |
| 3 | `04_03_fulltext_hybrid_search_mcp.py` | Parameterize fulltext Cypher — `$search_term` via `params` dict, removed `safe_term` string interpolation | DONE |
| 4 | `01_02_embeddings.py` | Batch embedding storage with `UNWIND` (single session/transaction). Replaced custom `vector_search()`/`demo_search()` with `VectorRetriever` | DONE |
| 5 | `05_01_fulltext_search.py` | Full rewrite — Option A: HybridRetriever + GraphRAG. Compares vector-only vs hybrid RAG answers, includes alpha sweep demo | DONE |
| 6 | `05_01_fulltext_search.py` | **Rename file** to `05_01_hybrid_rag.py` — filename still says "fulltext_search" but content is now entirely HybridRetriever + GraphRAG | DONE |

## Post-Fix Review Notes

All 5 changes reviewed. Findings:

- **config.py** — Clean. Dead code removed, `pydantic.Field` import correctly retained (used by config classes), stale docstring fixed.
- **02_02_vector_cypher_retriever.py** — All 4 references updated (2 imports, 2 type hints). No remaining OpenAI references.
- **04_03_fulltext_hybrid_search_mcp.py** — `fulltext_search_tool` now passes `$search_term` via params dict. `limit` remains f-string interpolated as `int` — consistent with `top_k` in the vector tools in the same file and safe since it's cast to `int`.
- **01_02_embeddings.py** — Embedding generation loop still iterates (necessary since `embed_query` is single-item), but storage is now batched in one `UNWIND` transaction. `demo_search()` uses `VectorRetriever` with `return_properties=["text", "index"]` and handles both string and dict content defensively.
- **05_01_fulltext_search.py** — Clean rewrite. Uses `GraphRAG` with both `VectorRetriever` (baseline) and `HybridRetriever` (comparison). Alpha sweep shows 5 values. Complementary to `05_02` which focuses on retrieval mechanics without GraphRAG. Index existence checks included. **Filename needs renaming** (item 6 above).
