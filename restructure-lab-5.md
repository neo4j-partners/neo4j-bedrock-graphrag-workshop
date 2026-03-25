# Lab 5 Restructure Plan — Neo4j MCP Server

## Summary

Move three existing MCP notebooks into a new `Lab_5_MCP_Server/` directory. Reorder them so the narrative builds from introduction → templates → autonomous agent. Trim notebook 01 to a pure MCP intro. Update site docs using archived Lab 6 content as the base.

## Decisions (from re-plan.md Q8–Q17)

| # | Decision |
|---|----------|
| 8 | Site docs: archive current lab5 pages, base new ones on archived lab6 pages |
| 9 | Reorder: intro → templates → text2cypher |
| 10 | Rename lib to `lab_5_data_utils.py` |
| 11 | Standardize all notebooks to `load_dotenv` |
| 12 | Mention LangGraph as an alternative in docs/README |
| 13 | Fix cross-lab framing to be self-contained within Lab 5 |
| 14 | Filenames: `01_intro_strands_mcp.ipynb`, `02_graph_enriched_search.ipynb`, `03_text2cypher_agent.ipynb` |
| 15 | No Lab 4 prerequisite — lab admin provides MCP server with full embeddings |
| 16 | Trim notebook 01 to pure MCP intro (tool discovery, schema inspection, one simple query) |
| 17 | Base site docs on archived `lab6.adoc`/`lab6-instructions.adoc`, not archived lab5 |

---

## Step 1 — Create directory and copy lib

1. Create `Lab_5_MCP_Server/` directory.
2. Create `Lab_5_MCP_Server/lib/` directory.
3. Copy `Lab_4_Graph_Enriched_Search/lib/lab_4_data_utils.py` → `Lab_5_MCP_Server/lib/lab_5_data_utils.py`.
   - Rename the file (not just copy) to `lab_5_data_utils`.
   - No code changes needed inside the file — the `CONFIG.txt` path resolution (`Path(__file__).parent.parent.parent / "CONFIG.txt"`) works at the same depth.
4. Copy `Lab_4_Graph_Enriched_Search/lib/__init__.py` → `Lab_5_MCP_Server/lib/__init__.py`.
   - Update re-exports to reference `lab_5_data_utils` instead of `lab_4_data_utils`.

## Step 2 — Create notebook 01: Intro to Strands + MCP

**Source**: `Lab_4_Graph_Enriched_Search/00_intro_strands_mcp.ipynb`
**Target**: `Lab_5_MCP_Server/01_intro_strands_mcp.ipynb`

Copy the notebook, then trim it:

- **Keep**: pip installs, config loading (`load_dotenv("../CONFIG.txt")`), MCPClient setup, `list_tools_sync()` tool discovery, schema inspection via `get-schema`.
- **Keep**: One simple read query to demonstrate `read-cypher` (e.g., "How many companies are in the database?").
- **Remove**: All the multi-query Text2Cypher demo cells (traversals, aggregations, multi-relationship queries, portfolio analysis). These patterns move to notebook 03.
- **Update markdown**: Remove "Next: Vector Search" link. Add a brief intro explaining that this notebook introduces MCP concepts: connecting to the server, discovering tools, and inspecting the graph schema. Notebook 02 uses those tools for structured vector search, and notebook 03 gives the agent full autonomy.
- **Framing**: This is an introduction to the MCP protocol and the Neo4j MCP Server, not a Text2Cypher demo.

## Step 3 — Create notebook 02: Graph-Enriched Search

**Source**: `Lab_4_Graph_Enriched_Search/02_graph_enriched_search_mcp.ipynb`
**Target**: `Lab_5_MCP_Server/02_graph_enriched_search.ipynb`

Copy the notebook, then update:

- **Update import**: `from lib.lab_4_data_utils import get_embedding` → `from lib.lab_5_data_utils import get_embedding`.
- **Update markdown**: Remove "Next: Lab 5: GraphRAG" link. Update intro text to reference "the previous notebook" (01) rather than any external lab.
- **Framing**: This is the **Cypher Templates** pattern — pre-written queries in `@tool` functions for reliability. Contrast with notebook 03 where the agent writes its own queries.
- **No changes** to config loading (already uses `load_dotenv`), MCP connection, or Cypher queries.

## Step 4 — Create notebook 03: Text2Cypher Agent

**Source**: `Lab_6_Advanced_Agents/neo4j_strands_mcp_agent.ipynb`
**Target**: `Lab_5_MCP_Server/03_text2cypher_agent.ipynb`

Copy the notebook, then update:

- **Replace config parsing**: Remove the manual `open("../CONFIG.txt")` + `line.split("=", 1)` block. Replace with `load_dotenv("../CONFIG.txt")` + `os.getenv()` to match notebooks 01 and 02.
- **Update markdown framing**: Replace all "Unlike Lab 4, where Cypher queries were pre-written..." references. New framing: "Notebook 02 used pre-written Cypher templates in `@tool` functions — reliable but limited to predefined query patterns. This notebook takes the opposite approach: the agent discovers the schema and writes original Cypher from scratch (the Text2Cypher pattern)."
- **Remove** any references to "Lab 4" or "Lab 6" that assume the old workshop structure.

## Step 5 — Create README.md

Create `Lab_5_MCP_Server/README.md` with:

- Lab title: "Lab 5 — Neo4j MCP Server"
- Brief description: Introduction to MCP, Cypher Templates, and Text2Cypher retrieval patterns using Strands Agents SDK and the Neo4j MCP Server.
- Note that LangGraph is a viable alternative framework (per Q12). Point to the archived `neo4j_langgraph_mcp_agent.ipynb` or just mention it conceptually.
- Prerequisites: Lab 1 complete (Aura instance), `CONFIG.txt` with `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`, AWS credentials for Bedrock. No Lab 4 prerequisite — the MCP server is pre-configured by the lab administrator with full embeddings.
- Notebook table:

| Notebook | Title | What You Learn |
|----------|-------|----------------|
| `01_intro_strands_mcp.ipynb` | Intro to Strands + MCP | MCP connection, tool discovery, schema inspection |
| `02_graph_enriched_search.ipynb` | Graph-Enriched Search | Cypher Templates pattern — pre-written vector search + graph traversal via `@tool` functions |
| `03_text2cypher_agent.ipynb` | Text2Cypher Agent | Text2Cypher pattern — agent discovers schema and writes original Cypher from scratch |

## Step 6 — Update site documentation

### 6a — Archive current Lab 5 pages

Move to `site/modules/ROOT/archive_pages/` (these already exist there from a prior archive, so this step may be a no-op — verify):
- `lab5.adoc`
- `lab5-instructions.adoc`
- `lab5-sample-queries.adoc`

### 6b — Create new lab5.adoc

**Base**: archived `site/modules/ROOT/archive_pages/lab6.adoc` (MCP/Text2Cypher content).

Changes from the archived lab6:
- Rename "Lab 6: Advanced Agents" → "Lab 5: Neo4j MCP Server" throughout.
- Replace "Two Framework Options" section — present Strands as the primary path, mention LangGraph as an alternative.
- Replace "Lab 4 vs Lab 6" comparison table — reframe as "Notebook 02 vs Notebook 03" (Cypher Templates vs Text2Cypher), self-contained within Lab 5.
- Replace the "GraphRAG Retrieval Patterns" table — update lab references (Templates = notebook 02, Graph-Enhanced Vector Search = notebook 02, Text2Cypher = notebook 03).
- Add a section on notebook 01 (MCP intro, tool discovery) — not covered in the archived lab6.
- Update "Next Steps" to point to Lab 6 (GraphRAG Pipeline) and remove references to "completing the workshop."
- Keep all the good MCP architecture content: three-component architecture, transport options, Neo4j MCP Server tools (`get-schema`, `read-cypher`), AWS deployment architecture, schema-first approach.

### 6c — Create new lab5-instructions.adoc

**Base**: archived `site/modules/ROOT/archive_pages/lab6-instructions.adoc`.

Changes:
- Rename "Lab 6 Instructions" → "Lab 5 Instructions".
- Replace the two-notebook table with the three-notebook table from Step 5.
- Update directory reference from `Lab_6_Advanced_Agents/` to `Lab_5_MCP_Server/`.
- Keep sample queries section (still relevant).
- Update prerequisites (no Lab 4 dependency — MCP server is pre-configured).
- Update "Next Steps" to point to Lab 6.

### 6d — Handle lab5-sample-queries.adoc

The current `lab5-sample-queries.adoc` contains queries for neo4j-graphrag retrievers (irrelevant). Options:
- **Delete** it and remove from nav (the new lab5-instructions.adoc already has inline sample queries from archived lab6-instructions).
- Or rewrite with MCP-relevant queries.

Recommend: delete and remove from nav. The inline queries in lab5-instructions.adoc are sufficient.

### 6e — Update nav.adoc

```
* Part 3: Advanced GraphRAG Patterns
** xref:lab5.adoc[Lab 5: Neo4j MCP Server]
*** xref:lab5-instructions.adoc[Instructions]
** xref:lab6.adoc[Lab 6: GraphRAG Pipeline]
*** xref:lab6-instructions.adoc[Instructions]
```

Remove `lab5-sample-queries.adoc` from nav.

## Step 7 — Update re-plan.md checklist

Mark Lab 5 tasks complete and update the checklist entries with the agreed filenames and ordering.

---

## Files created or modified

| Action | File |
|--------|------|
| **Create** | `Lab_5_MCP_Server/` directory |
| **Create** | `Lab_5_MCP_Server/lib/__init__.py` |
| **Create** | `Lab_5_MCP_Server/lib/lab_5_data_utils.py` |
| **Create** | `Lab_5_MCP_Server/01_intro_strands_mcp.ipynb` |
| **Create** | `Lab_5_MCP_Server/02_graph_enriched_search.ipynb` |
| **Create** | `Lab_5_MCP_Server/03_text2cypher_agent.ipynb` |
| **Create** | `Lab_5_MCP_Server/README.md` |
| **Rewrite** | `site/modules/ROOT/pages/lab5.adoc` |
| **Rewrite** | `site/modules/ROOT/pages/lab5-instructions.adoc` |
| **Delete** | `site/modules/ROOT/pages/lab5-sample-queries.adoc` |
| **Edit** | `site/nav.adoc` |
| **Edit** | `re-plan.md` (checklist updates) |

## Files NOT modified (deferred to cleanup phase)

- `Lab_4_Graph_Enriched_Search/` — deleted during cleanup
- `Lab_6_Advanced_Agents/` — deleted during cleanup
- `CLAUDE.md` — updated during cleanup
- `setup/README.md` — updated during cleanup

---

## Verification

After all steps:
1. All three notebooks should work with `../CONFIG.txt` (path is valid at the same depth).
2. `lab_5_data_utils.py` should resolve `CONFIG.txt` correctly via `Path(__file__).parent.parent.parent / "CONFIG.txt"`.
3. Notebook 02 import `from lib.lab_5_data_utils import get_embedding` should resolve.
4. Antora site should build with no new errors (`npx antora antora-playbook.yml`).
5. All notebook markdown cross-references should point to valid targets within Lab 5.
