# Site Pages Fix Plan

Comparison of `site/modules/ROOT/pages/` (current) vs `site/modules/ROOT/archive_pages/` (archive).

The archive had: MCP-first (Lab 4) → neo4j-graphrag library (Lab 5) → Text2Cypher agents (Lab 6).
The current has: neo4j-graphrag library (Lab 4) → MCP (Lab 5) → data pipeline (Lab 6).

The rewrite successfully reorganized the flow but introduced several inconsistencies and content gaps.

---

## Fix 1: nav.adoc — Move Lab 5 to Part 2, Lab 6 to Part 3 Bonus

**Files**: `site/nav.adoc`, `README.md`

Update nav.adoc from:
```
* Part 2: Building GraphRAG Agents
** Lab 3: Bedrock & Agents
** Lab 4: GraphRAG Search
* Part 3: Advanced GraphRAG Patterns
** Lab 5: Neo4j MCP Server
** Lab 6: GraphRAG Pipeline
```

To:
```
* Part 2: Building GraphRAG Agents
** Lab 3: Bedrock & Agents
** Lab 4: GraphRAG Search
*** lab4-sample-queries (new, see Fix 2)
** Lab 5: Neo4j MCP Server
* Part 3: Bonus — Build Your Own Pipeline
** Lab 6: GraphRAG Pipeline
```

Update root `README.md` Part 2/Part 3 tables to match.

---

## Fix 2: Create lab4-sample-queries.adoc

**Files**: new `site/modules/ROOT/pages/lab4-sample-queries.adoc`, `site/modules/ROOT/pages/sample-queries.adoc`

Create `lab4-sample-queries.adoc` based on the archive's `lab5-sample-queries.adoc` content, adapted for Lab 4:
- Document-Chunk structure queries
- Vector similarity search (reusing stored embeddings)
- Graph-enriched retrieval (chunk→company, chunk→risk factors, adjacent chunks)
- **Fulltext search section** with CREATE INDEX statements as setup, then fulltext query examples (fuzzy, boolean, entity search)
- Index verification

Update `sample-queries.adoc` line 199 to link to the new page:
```
See the xref:lab4-sample-queries.adoc[Lab 4: Advanced Sample Queries] page for those queries.
```

Add to nav.adoc under Lab 4 (see Fix 1).

---

## Fix 3: No action — Hybrid retrievers intentionally cut

---

## Fix 4: No action — LangGraph intentionally cut, keep existing mention in Lab 5

---

## Fix 5: Add "What the Library Does Under the Hood" to Lab 4

**Files**: `site/modules/ROOT/pages/lab4.adoc`

Add a brief, high-level section (short paragraph, no implementation details) explaining that the neo4j-graphrag retrievers handle embedding generation, vector index queries, and result formatting internally — the same steps participants will do manually through MCP in Lab 5. Keep it simple for non-experienced participants.

---

## Fix 6: Reframe Lab 6 as Optional Bonus

**Files**: `site/modules/ROOT/pages/lab6.adoc`, `site/modules/ROOT/pages/lab6-instructions.adoc`, `site/modules/ROOT/pages/lab5.adoc`

- Update Lab 6 overview intro to frame it as optional/bonus
- Update Lab 5 "Next Steps" to present Lab 6 as optional rather than the natural next step
- Update Lab 6 instructions closing to congratulate on the main workshop completion (Labs 0-5) and note Lab 6 was bonus
- Nav.adoc already handled in Fix 1

---

## Fix 7: Update sample-queries.adoc reference

**Files**: `site/modules/ROOT/pages/sample-queries.adoc`

Replace line 199 with a link to the new `lab4-sample-queries.adoc` page (depends on Fix 2).

---

## Fix 8: Rename mismatched image + clean up orphans

**Rename**:
- `lab6-mcp-agent-architecture.png` → `lab5-mcp-agent-architecture.png`
- Update reference in `lab5.adoc` line 22

**Delete orphaned images** (not referenced by any current page):
| Image | Origin |
|-------|--------|
| `graphrag-retrieval-flow.png` | archive Lab 5 |
| `lab4-graph-enriched-retrieval.png` | archive Lab 4 |
| `lab4-mcp-retrieval-architecture.png` | archive Lab 4 |
| `lab5-data-pipeline.png` | archive Lab 5 |
| `lab5-retriever-comparison.png` | archive Lab 5 |
| `lab1-free-trial-instance.png` | not referenced anywhere |

---

## Execution Order

1. Fix 8 — images (rename + delete orphans)
2. Fix 2 — create `lab4-sample-queries.adoc`
3. Fix 5 — add "under the hood" section to Lab 4
4. Fix 7 — update `sample-queries.adoc` reference
5. Fix 6 — reframe Lab 6 as bonus
6. Fix 1 — update `nav.adoc` and `README.md`
