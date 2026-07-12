# Automating Notebook Validation

Plan to replace the hand-maintained `financial_data_load/solution_srcs/` notebook mirrors with a runner that executes the real `.ipynb` files. The design mirrors `azure-databricks-aura-privatelink/scripts/automate.py`: self-asserting notebooks plus an orchestrator that checks for a clean run.

## Reference Pattern

The azure-databricks project drives notebook execution with two pieces working together:

1. **Notebooks assert their own correctness.** `notebooks/01_validate_connectivity.py` has inline `assert` statements and queries that raise on failure. The notebook is the test.
2. **`automate.py` executes it and checks for a clean run.** It uploads the notebook, submits a one-time serverless job, waits for completion, collects output, and treats `result_state == "SUCCESS"` as a pass, meaning no cell raised.

The only difference for this workshop is the executor. The reference runs on Databricks serverless. This workshop runs notebooks locally or in SageMaker Studio, so the local analog of the Databricks jobs API is papermill.

## Key Assumption

**The graph is already loaded.** The runner does no data loading and runs no data-load notebooks. It validates the read, retrieval, and agent notebooks against a pre-populated Neo4j instance. Lab 2 (the optional pipeline that wipes and rebuilds the graph) is out of scope. Lab 1 CSV load coverage is dropped, not folded into any notebook.

## Decisions

| Topic | Decision |
|-------|----------|
| Coverage | Notebooks self-validate via inline `assert` cells. Port the check logic from `solution_srcs/04_00_test_all_sample_queries.py` into the notebooks. A clean run is a pass. |
| Executor | papermill. It is the most popular tool for programmatic notebook execution and is the standard for this pattern. |
| Scope and location | One runner in `setup/`, covering all in-scope labs, with a `--labs` selector for a single lab, a list, or a range. |
| Data loading | None. The runner assumes the graph is already loaded and skips all data-load notebooks. |
| `%pip` cells | Left in the notebooks as-is. Participants see and run them normally. |
| Runner dependencies | One pre-provisioned venv with every lab dependency, including `neo4j-graphrag[bedrock]>=1.18.0` from PyPI. |
| Skipping installs at run time | The runner pre-processes each notebook in memory, neutralizing `%pip` and `!pip` cells by replacing their source with a no-op, writes a temp copy, and runs papermill on the temp copy. Originals are never modified. papermill has no native skip-by-tag, so the runner owns this step. |
| solution_srcs mirrors | Retired once the notebooks self-validate. |

## In-Scope Notebooks

The runner validates notebooks that read against a pre-loaded graph:

- **Lab 3** `01_vector_retriever.ipynb`, `02_vector_cypher_retriever.ipynb`. Read-only retrieval.
- **Lab 4** `01_strands_graphrag_agent.ipynb`. Read-only agent. `02_deploy_to_agentcore.ipynb` is a deploy with AWS side effects, off by default and opt-in via a flag.
- **Lab 6** `01_intro_strands_mcp.ipynb`, `02_graph_enriched_search.ipynb`, `03_text2cypher_agent.ipynb`. Require `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`, skipped when those are absent.
- **Appendix** `01_basic_strands_agent.ipynb`. `02_deploy_to_agentcore.ipynb` is a deploy, off by default.

Out of scope: Lab 2 (`01_data_loading.ipynb`, `02_embeddings.ipynb`), which wipes and rebuilds the graph.

## Work Items

### 1. Add assertion cells to the in-scope notebooks

One validation cell per notebook, or per key step, that raises on wrong results. Examples: Lab 4 asserts NVDA returns products, vector search returns matches, and the agent produces an answer. The check logic is sourced from `solution_srcs/04_00_test_all_sample_queries.py`. These cells double as teaching checkpoints.

### 2. Write `setup/run_notebooks.py`

The local `automate.py` analog:

- A `uv run` script with inline dependencies: papermill, nbformat, python-dotenv.
- Executes the in-scope notebooks against a chosen env. `--env` defaults to the repo-root `CONFIG.txt`.
- `--labs 4`, `--labs 3,4,6`, and `--labs 4-6` selection, matching `test_solutions.sh` ergonomics.
- Per notebook: neutralize pip cells, write a temp copy, run papermill, capture pass or fail plus error and traceback.
- Deploy notebooks (Lab 4 `02`, Appendix `02`) are off by default and opt-in via a flag.
- MCP notebooks are skipped when `MCP_GATEWAY_URL` or `MCP_ACCESS_TOKEN` is missing.
- Nonzero exit on any failure, with a summary table at the end.

### 3. Provision the runner venv

A `setup/` requirements or pyproject entry, or a documented `uv` invocation, that installs all lab dependencies once so the neutralized `%pip` cells have nothing left to install at run time.

### 4. Retire the solution_srcs mirrors

Remove the `04_01` through `06_03` mirrors and the `main.py solutions` and `test_solutions.sh` plumbing that drives them once the notebooks self-validate. Confirm before deleting.
