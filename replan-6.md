# Lab 6 — Building a GraphRAG Data Pipeline (Replan)

## Questions / Comments

18. **Fulltext index `search_chunks` is never created.** Notebook 04 (Hybrid RAG, source: `05_hybrid_rag.ipynb`) asserts that the `search_chunks` fulltext index exists, but none of the four source notebooks create it. Notebook 01 creates nodes, notebook 02 creates only the vector index. Since Lab 6 wipes the graph (Q3 answer), any indexes from `setup/` or earlier labs are gone. Options:
    - **Option A**: Add a fulltext index creation cell to notebook 02 (Embeddings) after the vector index — keeps all index creation in one notebook.
    - **Option B**: Add it to notebook 01 (Data Loading) alongside the graph build.
    - **Option C**: Add it as a setup step at the top of notebook 04 (Hybrid RAG) so it's self-contained.

Answer: Drop `05_hybrid_rag.ipynb` entirely. Moot.

19. **VectorRetriever notebook (03) is excluded — confirm intentional.** The checklist skips `03_vector_retriever.ipynb` because new Lab 4 already covers `VectorRetriever` and `GraphRAG` pipeline construction. The `04_vector_cypher_retriever` source notebook does create a basic `VectorRetriever` inline for comparison, so students still see it. However, the Hybrid RAG notebook's summary references "four retriever configurations across this lab" and the progression "Notebook 03 onward" — both need updating if VectorRetriever is dropped. Confirm this is the right call, or should we include it as notebook 03 and shift the others to 04/05?

Answer: Confirmed. Simplify — students see VectorRetriever in other labs.

20. **`pyproject.toml` / dependency file.** Lab 5 has `src/pyproject.toml` with `neo4j-graphrag[bedrock]` from the fork, `python-dotenv`, `pydantic-settings`, and `nest-asyncio`. Should Lab 6 get its own copy under `Lab_6_GraphRAG_Pipeline/src/pyproject.toml`? Or is `%pip install` in each notebook sufficient?

Answer: `%pip install` in each notebook is sufficient. No `pyproject.toml`.

21. **Cross-lab framing in site docs.** The archived `lab5.adoc` (source for new Lab 6 site page) says: _"In Lab 4 you wrote every retrieval query by hand — vector search Cypher and graph traversal joins."_ After the restructure, new Lab 4 is GraphRAG Search (neo4j-graphrag library, not hand-written Cypher). This framing is backwards — the new Lab 6 pipeline lab builds data from scratch using the same library Lab 4 uses for querying. The site page needs rewriting to frame Lab 6 as: "Lab 4 queried a pre-built graph. This lab builds that graph from scratch and explores additional retriever patterns (hybrid search)."

Answer: Yes, fix and adjust framing.

22. **Narrative arc after dropping VectorRetriever.** If VectorRetriever is excluded, the notebook progression is: Data Loading → Embeddings → VectorCypherRetriever → Hybrid RAG. Students jump from "create embeddings" to "vector search enriched with graph traversal" without first seeing plain vector search in isolation. The VectorCypherRetriever notebook does include a side-by-side comparison, but the pedagogical step is compressed. Is that acceptable given Lab 4 covered the basics?

Answer: Fine. Also simplify VectorCypherRetriever to remove the inline VectorRetriever comparison — students have already seen it in earlier labs.

23. **"Next Steps" links.** The current Lab 5 Hybrid RAG notebook ends with "Continue to Lab 6 to build MCP agents." After the restructure, Lab 6 IS this lab, and Lab 5 is MCP Server. The "Next Steps" should either point back to Lab 5 (if done out of order) or say "Workshop complete" or similar. What's the intended lab ordering — must students do Lab 5 (MCP) before Lab 6 (Pipeline), or are they independent?

Answer: Say "Workshop complete."

24. **`slides/` directory.** Lab 5 has an empty `slides/` directory with `.gitkeep`. Copy to Lab 6 or skip?

Answer: Skip.

---

## Source → Target Mapping

| Target (Lab 6) | Source (Lab 5) | Key Changes Needed |
|-----------------|----------------|--------------------|
| `01_data_loading.ipynb` | `Lab_5_GraphRAG/01_data_loading.ipynb` | Already wipes graph (matches Q3). Update "Next" link. Update lab references in markdown. |
| `02_embeddings.ipynb` | `Lab_5_GraphRAG/02_embeddings.ipynb` | Update "Next" link to point to `03_vector_cypher_retriever.ipynb`. Update summary text. |
| `03_vector_cypher_retriever.ipynb` | `Lab_5_GraphRAG/04_vector_cypher_retriever.ipynb` | Rename from 04→03. Remove inline VectorRetriever comparison (Q22). Update "Next" to "Workshop complete." |
| `financial_data.json` | `Lab_5_GraphRAG/financial_data.json` | Direct copy, no changes. |
| `lib/data_utils.py` | `Lab_5_GraphRAG/lib/data_utils.py` | Copy as-is. `load_dotenv('../CONFIG.txt')` path stays correct (one level deep). |
| `lib/__init__.py` | `Lab_5_GraphRAG/lib/__init__.py` | Copy, remove `MCPConnection` import (not needed). |
| `README.md` | New | Write from scratch for the pipeline lab. |

**Dropped:**
- `03_vector_retriever.ipynb` — covered in Lab 4 (Q19)
- `05_hybrid_rag.ipynb` — dropped entirely (Q18)
- `lib/mcp_utils.py` — Lab 6 doesn't use MCP
- `src/pyproject.toml` — `%pip install` per notebook instead (Q20)
- `slides/` directory — skip (Q24)

## Notebook-Level Change Details

### Notebook 01 — Data Loading (`01_data_loading.ipynb`)

**Source**: `Lab_5_GraphRAG/01_data_loading.ipynb`

Changes needed:
- **Summary markdown**: Update "Next: Embeddings" link to `02_embeddings.ipynb` (same filename, verify link text matches new lab context).
- **Intro/title**: Currently says "Data Loading" with no lab number. Fine as-is.
- **`clear_graph()`**: Already present and matches the "wipe the graph" requirement.
- **`lib.data_utils` import**: `split_text` — needs `lib/data_utils.py` copied to Lab 6.
- **`financial_data.json` path**: Loads from same directory (`'financial_data.json'`) — works after copy.
- **CONFIG.txt path**: Uses `load_dotenv('../CONFIG.txt')` — correct for one-level-deep lab directory.

### Notebook 02 — Embeddings (`02_embeddings.ipynb`)

**Source**: `Lab_5_GraphRAG/02_embeddings.ipynb`

Changes needed:
- **"Next" link**: Currently points to `03_vector_retriever.ipynb` — update to `03_vector_cypher_retriever.ipynb`.
- **Summary text**: Says "the next notebook, the VectorRetriever" — update to reference VectorCypherRetriever.

### Notebook 03 — VectorCypher Retriever (`03_vector_cypher_retriever.ipynb`)

**Source**: `Lab_5_GraphRAG/04_vector_cypher_retriever.ipynb`

Changes needed:
- **Remove VectorRetriever comparison**: Drop the inline `VectorRetriever` creation and side-by-side comparison cells (Q22). Students have seen VectorRetriever in Lab 4.
- **Summary text**: Remove references to "pure vector and vector-cypher approaches" comparison. Update to focus solely on VectorCypherRetriever's graph traversal capability.
- **"Next" link / Summary ending**: Replace "Next: Hybrid RAG" with "Workshop complete" messaging (Q23).

## Checklist

### Lab 6 — Building a GraphRAG Data Pipeline (reshuffled)

- [ ] Create `Lab_6_GraphRAG_Pipeline/` directory
- [ ] **Notebook 01 — Data Loading**: Copy from `Lab_5_GraphRAG/01_data_loading.ipynb`, update next-notebook links
- [ ] **Notebook 02 — Embeddings**: Copy from `Lab_5_GraphRAG/02_embeddings.ipynb`, update next-notebook link and summary to reference VectorCypherRetriever
- [ ] **Notebook 03 — Vector Cypher Retriever**: Copy from `Lab_5_GraphRAG/04_vector_cypher_retriever.ipynb`, renumber, remove VectorRetriever comparison, update summary and next-steps to "Workshop complete"
- [ ] Copy `financial_data.json` into `Lab_6_GraphRAG_Pipeline/`
- [ ] Copy `lib/data_utils.py` and `lib/__init__.py` (skip `mcp_utils.py`)
- [ ] Write `Lab_6_GraphRAG_Pipeline/README.md`
- [ ] Update internal cross-references across all three notebooks (next/previous links, lab number references)

### Site Documentation

- [ ] Write `site/modules/ROOT/pages/lab6.adoc` — base on archived `lab5.adoc`, reframe for new Lab 6 context (Q21: "Lab 4 queried a pre-built graph; this lab builds it from scratch")
- [ ] Write `site/modules/ROOT/pages/lab6-instructions.adoc` — base on archived `lab5-instructions.adoc`, update notebook table (three notebooks, not five) and links
- [ ] Update `site/nav.adoc` — Lab 6 title from "Advanced Agents" to "GraphRAG Pipeline" or similar
- [ ] Update "Next Steps" in Lab 5 site docs to point to Lab 6 correctly (once Lab 5 restructure is done)
