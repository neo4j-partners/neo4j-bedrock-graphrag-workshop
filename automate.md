# Automating Notebook Validation

Plan to replace the hand-maintained `financial_data_load/solution_srcs/` notebook mirrors with a runner that executes the real `.ipynb` files. The design mirrors `azure-databricks-aura-privatelink/scripts/automate.py`: self-asserting notebooks plus an orchestrator that checks for a clean run.

## Status (2026-07-11)

The runner is built and validated end to end. **Lab 3 passes live** against the loaded graph:
`uv run setup/run_notebooks.py --labs 3` runs both notebooks clean (Neo4j connect, embeddings, LLM answer, GraphRAG grounded context).

| Work item | Status |
|-----------|--------|
| 2. `setup/run_notebooks.py` | **Done.** Live-validated on Lab 3. |
| 3. Runner venv | **Done.** Folded into the runner's PEP 723 inline deps; `uv` caches it, so there is no separate provisioning step. |
| 1. Assertion cells | **Not started.** Notebooks pass by running clean; no explicit self-checks yet. |
| 4. Retire `solution_srcs` | **Not started.** Confirm-gated. |

Two issues surfaced during bring-up and were fixed (both pre-existing, unrelated to the runner):

- **Config loading.** The workshop `lib/data_utils.py` loaded only `CONFIG.txt` (which held placeholder creds) and never the real project-root `.env`, so runs could not reach Neo4j. Fixed across all four workshop copies (Lab 2/3/4/6) to prefer the root `.env`, then `CONFIG.txt`, then `financial_data_load/.env` — exactly one source. `financial_data_load/lib` is intentionally left as-is (it uses its own `.env`).
- **Fork to PyPI API drift.** The lib and the Lab 3 notebooks used the old `neo4j-partners` fork API (`BedrockLLM(model_id=...)`, `llm.model_id`). PyPI `neo4j-graphrag` 1.18.0 renamed the constructor arg to `model_name` and exposes `llm.model_name`. Fixed `get_llm()` in the Lab 2/3/4/5 lib copies and `llm.model_name` in both Lab 3 notebooks. A full sweep confirmed the retrievers, `GraphRAG`, `BedrockEmbeddings` (still `model_id`), index helpers, and Strands `BedrockModel` (a different library, also `model_id`) all match 1.18.0. `financial_data_load` pins 1.14.0, where `model_id` is correct, so it was left untouched.

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
- **Lab 6** `01_mcp_text2cypher_agent.ipynb`. Requires `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`, skipped when those are absent.

Out of scope:
- Lab 2 (`01_data_loading.ipynb`, `02_embeddings.ipynb`), which wipes and rebuilds the graph.
- Appendix (`01_basic_strands_agent.ipynb`, `02_deploy_to_agentcore.ipynb`). Not part of the validation set. The runner still knows about them (`--labs appendix`), but they are not run by default and are not required to pass.

## Work Items

### 1. Add assertion cells to the in-scope notebooks — **Not started**

One validation cell per notebook (decided: one consolidated check cell per notebook, not per step) that raises on wrong results. Examples: Lab 4 asserts NVDA returns products, vector search returns matches, and the agent produces an answer. The check logic is sourced from `solution_srcs/04_00_test_all_sample_queries.py`. These cells double as teaching checkpoints. Until these land, notebooks pass only by running clean (no cell raised), which does not verify result contents.

### 2. Write `setup/run_notebooks.py` — **Done**

The local `automate.py` analog:

- A `uv run` script with inline PEP 723 dependencies: papermill, nbformat, ipykernel, python-dotenv, plus every lab dependency (see item 3).
- Executes the in-scope notebooks against a chosen env (Option A — see below).
- `--labs 4`, `--labs 3,4,6`, `--labs 4-6`, and `--labs appendix` selection, matching `test_solutions.sh` ergonomics.
- Per notebook: neutralize pip cells, write a temp copy, run papermill (with `cwd` set to the notebook's dir so `lib/` imports resolve), capture pass or fail plus error and traceback.
- Deploy notebooks (Lab 4 `02`, Appendix `02`) are off by default and opt-in via `--include-deploy`.
- MCP notebooks are skipped when `MCP_GATEWAY_URL` or `MCP_ACCESS_TOKEN` is missing or a `your-...` placeholder.
- Nonzero exit on any failure, with a summary table at the end.

**Credentials (Option A).** The runner reads `--env` and injects those keys into `os.environ` before papermill launches the kernel. Because each lab's `lib/data_utils.py` and the notebook cells load config with the default `load_dotenv` (`override=False`), the injected values win and no config file is rewritten. `--env` defaults to the project-root `.env` when it exists, else `CONFIG.txt` — the same precedence the lib now uses, so injection and the lib's own load never conflict.

### 3. Provision the runner venv — **Done**

Folded into item 2's PEP 723 inline dependency block, which lists every lab dependency (`neo4j-graphrag[bedrock]>=1.18.0`, `strands-agents`, `strands-agents-tools`, `mcp`, `httpx`, and the `bedrock-agentcore` deploy deps). `uv` builds and caches this venv on first run, so the neutralized `%pip` cells have nothing left to install. No separate requirements/pyproject file is needed.

### 4. Retire the solution_srcs mirrors — **Not started**

Remove the `04_01` through `06_03` mirrors and the `main.py solutions` and `test_solutions.sh` plumbing that drives them once the notebooks self-validate. `main.py` also drives the real data-load/cleanse/backup pipeline (`load`, `cleanse`, `finalize`, ...), so this is a surgical removal of the `solutions` subcommand and its `solution_srcs` imports only — not deleting `main.py`. Confirm before deleting.

## Proposed Next Steps

In order:

1. **Validate Lab 4 live.** Run `uv run setup/run_notebooks.py --labs 4`. The Lab 4 lib already carries the `get_llm()` fix; confirm the Strands agent notebook runs clean against the loaded graph.
2. **Validate Lab 6 live.** Run `uv run setup/run_notebooks.py --labs 6`. MCP creds are in the root `.env`, so the MCP notebook should execute rather than skip.
3. **Add the assertion cells (item 1).** One consolidated check cell per in-scope notebook, ported from `04_00_test_all_sample_queries.py`. This is the remaining substantive work.
4. **Retire `solution_srcs` (item 4).** Only after the notebooks self-validate, and only the `solutions` subcommand plus mirrors. Confirm before deleting.

Not planned: Appendix validation (out of scope) and the Lab 2 data-load notebooks (destructive, out of scope).

## Update (2026-07-11): solution_srcs migrated to neo4j-graphrag 1.18.0

The `financial_data_load` mirrors were migrated off the `neo4j-partners` fork onto PyPI `neo4j-graphrag[bedrock]>=1.18.0`. This supersedes the earlier note in "Fork to PyPI API drift" above, which recorded `financial_data_load` as pinned to 1.14.0 and left untouched. The mirrors are no longer stale against 1.18.0, so item 4 (retire `solution_srcs`) is still the end goal but the mirrors run clean in the meantime.

Changes made:

- `financial_data_load/pyproject.toml`: bumped to `neo4j-graphrag[bedrock]>=1.18.0` and added the previously undeclared `strands-agents>=0.1.0` and `boto3>=1.42.0`. Six solutions import `strands` or `boto3` but relied on out-of-band venv installs.
- `uv lock` + `uv sync`: regenerated the lock off PyPI. It resolved `neo4j-graphrag 1.18.0`, `strands-agents 1.47.0`, `boto3 1.42.73`, and dropped the local fork reference.
- `solution_srcs/config.py`: `get_llm()` now passes `model_name=` to `BedrockLLM`. The fork used `model_id`, which 1.18.0 forwards into `boto3.client(...)` and raises `Session.client() got an unexpected keyword argument 'model_id'`.
- `04_02`, `04_03`, `06_03`: `llm.model_id` prints changed to `llm.model_name`.
- `solution_srcs/06_03_vector_cypher_retriever.py`: added a `result_formatter` so enriched context prints entity metadata instead of a raw `<Record ...>` repr.
- `solution_srcs/test_connection.py`: the model test was leftover OpenAI/Azure code importing `openai` and nonexistent `get_agent_config`/`_get_azure_token`. Rewritten to test Bedrock via the workshop `get_llm()` and `BedrockConfig`.
- `test_solutions.sh`: metadata was stale at 22 solutions with memory/context-provider names. Aligned to `main.py`'s 12 solutions, set `MCP_SOLUTIONS=(7 8 9)`, and replaced the contiguous default-start skip with a `DEFAULT_SKIP=(2 3 10 11)` set for the data-writing solutions.

Tested and validated live against the loaded graph:

| Check | Result |
|-------|--------|
| Solution 4, Vector Retriever | Pass |
| Solution 5, VectorCypher Retriever | Pass |
| Solution 6, Strands GraphRAG Agent | Pass, both tools exercised |
| Solution 12, VectorCypher Retriever (Lab 6) | Pass, formatter output verified |
| `main.py test` (test_connection.py) | Pass, Neo4j schema plus Bedrock LLM reply |
| `test_solutions.sh .env 4` dispatch | Pass |
| Default-skip selection logic | Verified: runs 1,4,5,6,12; skips 2,3,10,11 and MCP 7,8,9 |

What remains untested this session:

- Solutions 1 and 2 (Basic Strands Agent, Deploy to AgentCore). Solution 2 deploys with AWS side effects.
- Solutions 3, 10, 11 (Load Data and Query, Data Loading, Embeddings). Skipped as data-writing per the graph-already-loaded assumption.
- Solutions 7, 8, 9 (MCP). Not run this session; they need valid `MCP_GATEWAY_URL` and `MCP_ACCESS_TOKEN`.
