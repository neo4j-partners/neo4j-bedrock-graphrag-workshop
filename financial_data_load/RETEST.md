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
