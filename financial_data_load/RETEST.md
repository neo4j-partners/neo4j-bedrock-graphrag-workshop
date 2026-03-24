# Retest Plan

## What changed

All three Lab 4 solution files and main.py were updated to:

1. Replace custom `MCPConnection` with standard Strands `MCPClient`
2. Use `@tool` wrappers to keep embeddings off the LLM context window (input path)
3. Add Cypher-level `{.*, embedding: null}` filtering (output path)
4. Convert all `main()` functions to sync (matching `is_async=False` in main.py)
5. Use parameterized Cypher queries (`$query_vector` with `params` dict)

## What to test

### Solution 9 — `04_01_vector_search_mcp.py`
```
uv run python main.py solutions 9
```
- **Status:** PASSED
- Three vector searches should complete with similarity scores and chunk text
- No embedding arrays in agent output

### Solution 10 — `04_02_graph_enriched_search_mcp.py`
```
uv run python main.py solutions 10
```
- **Status:** PARTIAL — vector-only and graph-enriched searches passed; entity-enriched hit transient Bedrock `ServiceUnavailableException`
- **Retest:** Run again when Bedrock is not rate-limited
- Three search levels should each return results: vector-only, graph-enriched (with document + neighbor context), entity-enriched (with companies, products, risks)
- Two Q&A queries should synthesize answers from entity-enriched search
- No embedding arrays in agent output

### Solution 11 — `04_03_fulltext_hybrid_search_mcp.py`
```
uv run python main.py solutions 11
```
- **Status:** NOT TESTED — Bedrock rate-limited before it could run
- **Retest:** Run when Bedrock is available
- Fulltext searches: "revenue", "revnue~" (fuzzy), "risk*" (wildcard), "revenue AND growth" (boolean)
- Fulltext + graph traversal: "iPhone" with document/company/product context
- Hybrid search: three queries using both vector_search and fulltext_search_tool
- No embedding arrays in agent output

### main.py change
- Line 490: `is_async` changed from `True` to `False` for 04_03
- Verify solution 11 launches without async wrapper errors

## What to look for

1. **No embedding arrays in output** — tool results should contain text, scores, document names, entities — never `[0.023, -0.056, ...]` float arrays
2. **MCP connection works** — "MCP tools discovered" should print tool names
3. **Cypher tool found** — should find `neo4j-mcp-server-target___read-cypher`
4. **`@tool` wrappers invoked** — agent logs should show tool calls like `vector_search`, `graph_enriched_search`, `entity_enriched_search`, `fulltext_search_tool`
5. **No `MCPConnection` import errors** — solutions no longer use the custom class
6. **Transient Bedrock errors** — `ServiceUnavailableException` is rate limiting, not a code bug; retry after a pause

---

## lib/data_utils.py refactor — replace anti-patterns with neo4j-graphrag library calls

### What changed

Both `Lab_5_GraphRAG/lib/data_utils.py` and `financial_data_load/lib/data_utils.py` were updated together (they must stay in sync):

1. **`get_embedding()`** — removed 40 lines of manual Bedrock API calls (`boto3.client`, JSON request body, `_NovaEmbedding` pydantic models, response parsing). Now delegates to `get_embedder().embed_query(text)` with a cached embedder instance. Same return type (`list[float]`), same model, same parameters.
2. **`get_schema()`** — removed 40 lines of raw Cypher (`db.schema.nodeTypeProperties`, `db.schema.relTypeProperties`, manual formatting). Now delegates to `neo4j_graphrag.schema.get_schema(driver, sanitize=True)`. Note: the library version uses `apoc.meta.data()` internally instead of `db.schema.*` procedures.
3. **Removed imports** — `json`, `boto3`, `BaseModel` (from pydantic), `_NovaEmbedding`, `_NovaEmbeddingResponse`, `_bedrock_client` global.
4. **Added import** — `from neo4j_graphrag.schema import get_schema as _lib_get_schema`.

### Three Lab 5 notebooks were also updated

- **`01_data_loading.ipynb`** — replaced inline `split_into_chunks()` with `split_text()` from `data_utils` (uses library's `FixedSizeSplitter`). Updated `%pip install` to include neo4j-graphrag.
- **`02_embeddings.ipynb`** — replaced raw Cypher `UNWIND/SET` embedding batch update with `upsert_vectors()` from `neo4j_graphrag.indexes`.
- **`05_fulltext_search.ipynb`** — replaced raw `CREATE FULLTEXT INDEX` Cypher with `create_fulltext_index()` from `neo4j_graphrag.indexes`. Updated `%pip install` to include neo4j-graphrag.

### What to test

#### `get_embedding()` — used by Lab 4 solution files via `financial_data_load/lib/data_utils.py`
```
uv run python main.py solutions 9
uv run python main.py solutions 10
uv run python main.py solutions 11
```
- These solutions call `get_embedding()` to generate query vectors for MCP tool wrappers
- Verify embedding dimensions are still 1024
- Verify vector search results are returned with scores (same behavior as before)

#### `get_schema()` — used by Lab 6 solution files
```
uv run python main.py solutions 13
```
- Verify schema is returned as a formatted string (output format may differ slightly since the library uses `apoc.meta.data` instead of `db.schema.nodeTypeProperties`)
- If APOC is not available on the target Neo4j instance, `get_schema()` will fail — this would be a regression

#### Lab 5 notebooks (run sequentially in order)
```
01_data_loading.ipynb   — verify split_text() produces chunks (count may differ from old naive splitter due to word-boundary awareness)
02_embeddings.ipynb     — verify upsert_vectors() writes embeddings to all Chunk nodes
05_fulltext_search.ipynb — verify create_fulltext_index() creates the index successfully
```

### What to look for

1. **`get_embedding()` returns identical results** — same 1024-dim float arrays, same model. The only change is the code path (library embedder vs raw boto3), not the API call.
2. **`get_schema()` output format change** — the library version produces a different text format than the old hand-rolled version. Callers that parse the string may need adjustment. Callers that pass it to an LLM (Text2Cypher) should work fine.
3. **APOC dependency** — the library's `get_schema` requires `apoc.meta.data()`. Neo4j Aura includes APOC core, so this should work. Self-hosted Neo4j without APOC will fail.
4. **Chunk count change in notebook 01** — `FixedSizeSplitter(approximate=True)` tries to break on word boundaries, so the number and content of chunks may differ from the old character-exact splitter. This is intentional (better quality chunks) but means notebook output won't match previous runs exactly.
