# Align solution_srcs with Notebooks

Goal: solution source filenames use `{lab}_{notebook_num}_{name}.py` convention matching notebooks.

## Status Key

- [ ] Not started
- [x] Done

---

## Phase 1: Delete Microsoft Agent Framework files (9 files)

These have no matching notebooks and use the deprecated MS Agent Framework:

- [x] `05_01_simple_agent.py`
- [x] `05_02_context_provider.py`
- [x] `06_01_fulltext_context_provider.py`
- [x] `06_02_vector_context_provider.py`
- [x] `06_03_graph_enriched_provider.py`
- [x] `07_01_memory_context_provider.py`
- [x] `07_02_entity_extraction.py`
- [x] `07_03_memory_tools_agent.py`
- [x] `07_04_reasoning_memory.py`

## Phase 2: Rename Lab 5 files to `05_{nn}` convention

Labs 3 and 4 already follow the convention (`03_01_...`, `04_00_...`). Lab 5 files need renaming:

| Current File | New File | Matching Notebook | Status |
|---|---|---|---|
| `01_01_data_loading.py` | `05_01_data_loading.py` | `Lab_5/01_data_loading.ipynb` | [x] |
| `01_02_embeddings.py` | `05_02_embeddings.py` | `Lab_5/02_embeddings.ipynb` | [x] |
| `02_01_vector_retriever.py` | `05_03_vector_retriever.py` | `Lab_5/03_vector_retriever.ipynb` | [x] |
| `02_02_vector_cypher_retriever.py` | `05_04_vector_cypher_retriever.py` | `Lab_5/04_vector_cypher_retriever.ipynb` | [x] |
| `05_01_hybrid_rag.py` | `05_05_hybrid_rag.py` | `Lab_5/05_hybrid_rag.ipynb` | [x] |
| `05_02_hybrid_search.py` | `05_06_hybrid_search.py` | `Lab_5/06_hybrid_search.ipynb` | [x] |

## Phase 3: Delete orphan files (no matching notebook, not MS Agent Framework)

Decision: **delete** (user confirmed)

- [x] `01_03_entity_extraction.py`
- [x] `01_04_full_dataset_queries.py`
- [x] `02_03_text2cypher_retriever.py`

## Phase 4: Update references

- [x] `financial_data_load/main.py` — SOLUTIONS list, AGENT_QUERIES dict, comments
- [x] `financial_data_load/README.md` — solution tables
- [x] `financial_data_load/FIX_GRAPH.md` — file references
- [x] `financial_data_load/solution_srcs/05_02_embeddings.py` — internal comment referencing old filename

## Notes

- `01_test_full_data_load.py` — standalone test, not a solution. Left as-is.
- `config.py`, `test_connection.py`, `__init__.py` — utilities. Left as-is.
- Lab 3 files (`03_01_`, `03_02_`) already matched notebooks. No changes needed.
- Lab 4 files (`04_00_`, `04_01_`, `04_02_`) already matched notebooks. `04_03_` was removed (notebook deleted).
