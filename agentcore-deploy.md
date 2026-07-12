# Lab 4 — AgentCore Deployment Plan

Implementation plan for the missing AgentCore deployment content in Lab 4
(`Lab_4_GraphRAG_Agent/`), the item flagged in `finalize-outline-v2.md`
("Lab 4 — Missing AgentCore Deployment").

## Goal

Attendees deploy the exact GraphRAG agent they build locally in
`01_strands_graphrag_agent.ipynb` to Amazon Bedrock AgentCore Runtime and
invoke it over REST. This is the agent behind the workshop's opening
hero-question demo. The site pages (`lab4.adoc`, `lab4-instructions.adoc`) and
`nav.adoc` already promise this ("Strands GraphRAG Agent **and AgentCore**");
this plan makes the notebooks match.

## Decisions (locked)

- **Two notebooks.** Keep `01_strands_graphrag_agent.ipynb` as the local
  build/test story. Add a new `02_deploy_to_agentcore.ipynb` for deployment,
  mirroring the appendix two-notebook split. Deployment concerns (IAM, REST,
  OneBlink permission caveats) stay isolated in the optional second notebook.
- **Credentials via Option B — notebook writes constants from `CONFIG.txt`.**
  `agent.py` holds template constants for the Neo4j connection at the top. A
  cell in notebook 02 reads `../CONFIG.txt` and rewrites those constant lines
  before deploy, so attendees never retype the credentials they already entered
  in Lab 1. The deployed `agent.py` carries the values (acceptable for
  ephemeral workshop Aura instances).
- **Execution role auto-create.** Notebook 02 uses
  `execution_role_auto_create: True` in the generated
  `.bedrock_agentcore.yaml`, matching the appendix notebook. No dependency on
  the admin having run `setup_agentcore.sh` for the role. (The deploy policy
  check on the SageMaker role still applies — see step 2.)

## Reference material

- `zz_Appendix_What_Is_An_Agent/02_deploy_to_agentcore.ipynb` — deploy notebook
  structure (install, policy check, config generation, deploy, invoke, cleanup).
- `zz_Appendix_What_Is_An_Agent/agentcore_deploy/agent.py` — the
  `BedrockAgentCoreApp` handler shape (basic time/math agent; Lab 4 replaces the
  tools with GraphRAG).
- `zz_Appendix_What_Is_An_Agent/agentcore_deploy/pyproject.toml` — base
  dependency set.
- `Lab_4_GraphRAG_Agent/01_strands_graphrag_agent.ipynb` — the
  `VectorCypherRetriever` + `graph_enriched_search` tool + agent to port into
  `agent.py`.

## Work items

### 1. Create `Lab_4_GraphRAG_Agent/agentcore_deploy/agent.py`

Port the local GraphRAG agent into a `BedrockAgentCoreApp` entrypoint.

- Template constants at the top (rewritten by notebook 02 from `CONFIG.txt`):
  ```python
  # --- Filled in from CONFIG.txt by 02_deploy_to_agentcore.ipynb ---
  NEO4J_URI = "<NEO4J_URI>"
  NEO4J_USERNAME = "<NEO4J_USERNAME>"
  NEO4J_PASSWORD = "<NEO4J_PASSWORD>"
  MODEL_ID = "<MODEL_ID>"
  REGION = "<REGION>"
  ```
  Use distinctive placeholder tokens so the notebook's rewrite is a safe,
  unambiguous string replace.
- Module-level initialization (once, for warm reuse across invocations, not
  per-request): Neo4j driver + `verify_connectivity()`, Titan embedder, the
  `VectorCypherRetriever` with the Lab 3 `RETRIEVAL_QUERY` and `format_record`
  formatter.
- The `graph_enriched_search` `@tool` (same docstring-as-instructions pattern
  as notebook 01).
- The Strands `Agent` with `BedrockModel` and the SEC 10-K analyst system
  prompt.
- `@app.entrypoint` async `invoke(payload)` handler: extract `prompt` (accept
  `prompt`/`message`/`query`/`input`), run the agent, yield chunk/complete/error
  events. Reuse the appendix error-handling shape.
- `if __name__ == "__main__": app.run(port=8080)`.
- The embedder helper: `agent.py` must be self-contained in the deploy package
  (only files in `source_path` are uploaded). Either inline the Titan embedder
  construction or copy the minimal `get_embedder()` logic directly into
  `agent.py` — do **not** import from the notebook's `lib/`.

### 2. Create `Lab_4_GraphRAG_Agent/agentcore_deploy/pyproject.toml`

Extend the appendix base deps with the graph stack:

```toml
[project]
name = "graphrag-strands-agent"
version = "0.1.0"
description = "Strands GraphRAG agent (VectorCypherRetriever) for AgentCore Runtime"
requires-python = ">=3.10"
dependencies = [
    "strands-agents>=0.1.0",
    "strands-agents-tools>=0.1.0",
    "boto3>=1.42.0",
    "bedrock-agentcore>=1.4.7",
    "neo4j>=5.0.0",
    "neo4j-graphrag[bedrock]>=1.18.0",
]
```

**Use the released PyPI wheel** `neo4j-graphrag[bedrock]>=1.18.0`. As of 1.18.0
the Bedrock support (`BedrockEmbeddings`, `BedrockLLM`, and the retrievers) is
upstreamed and released, so the neo4j-partners git fork is no longer needed.
This is the same dependency the Lab 2/3/4 notebooks install, so the deployed
agent stays consistent with the local agent. A git dependency will not work
here: `direct_code_deploy` cross-compiles for Linux ARM64 using prebuilt wheels
and refuses source builds, so the dependency must resolve to a wheel. The pure
Python `neo4j-graphrag` wheel installs cleanly under that cross-compilation.

### 3. Author `Lab_4_GraphRAG_Agent/02_deploy_to_agentcore.ipynb`

Structure follows the appendix deploy notebook, adapted for GraphRAG:

1. **Intro** (markdown) — what AgentCore Runtime provides, the
   `direct_code_deploy` path, and the OneBlink permission caveat (copy the
   hosted-workshop note from the appendix).
2. **Setup** — `%pip install bedrock-agentcore-starter-toolkit ... pyyaml
   python-dotenv`. Detect the SageMaker role and verify
   `BedrockAgentCoreLabDeployPolicy` is attached (reuse the appendix cell).
3. **Fill agent.py from CONFIG.txt** — read `../CONFIG.txt` with `dotenv`, then
   string-replace the placeholder tokens in `agentcore_deploy/agent.py` with the
   real values. Print a confirmation (mask the password). This is the Option B
   step.
4. **Review the deployment package** — `ls -la agentcore_deploy/` and show
   `agent.py` so attendees see the GraphRAG tool that will be deployed.
5. **Configure and deploy** — generate `.bedrock_agentcore.yaml` programmatically
   with `execution_role_auto_create: True`, `s3_auto_create: True`,
   `ecr_auto_create: False`, relative-resolved `entrypoint`/`source_path`
   (`os.path.abspath("agentcore_deploy")`), `AGENT_NAME = "graphrag_strands_agent"`.
   Install `zip` if missing, then `agentcore deploy --auto-update-on-conflict`.
6. **Invoke via CLI** — `agentcore invoke '{"prompt": "<hero question>"}'` using
   the workshop hero question (an entity-specific 10-K question that exercises
   `graph_enriched_search`).
7. **Invoke via boto3** — read the agent ARN from the generated yaml, call
   `invoke_agent_runtime`, decode the streamed response.
8. **Cleanup** — commented-out `agentcore destroy` cell.

Notes:
- Do **not** commit a populated `.bedrock_agentcore.yaml` with absolute paths or
  a real ARN (the appendix's committed yaml has stale
  `Lab_3_Intro_to_Bedrock_and_Agents` paths). The notebook generates it at run
  time. Add it to `.gitignore` if not already covered, or commit only a
  placeholder.
- Ensure the rewritten `agent.py` (with real credentials) is **not** committed —
  keep the repo copy as the template with placeholder tokens. Confirm
  `.gitignore` handling so participant secrets don't get staged.

### 4. Update `Lab_4_GraphRAG_Agent/README.md`

- Add the AgentCore deploy objective to "What You'll Learn."
- Expand the Notebooks table to list both notebooks (01 build/test, 02 deploy).
- Note the OneBlink permission caveat and the `CONFIG.txt`-driven credential
  fill.

### 5. Reconcile the site pages

- `lab4.adoc` and `lab4-instructions.adoc` currently describe a **single**
  notebook. Update the Notebook sections/tables to list two notebooks (01 local
  build/test, 02 deploy). The conceptual AgentCore sections already present stay.
- Verify the `agent_tools.png` image referenced at `lab4.adoc:22` exists under
  `site/modules/ROOT/images/`; add or fix the reference if missing.

### 6. Verification

- Run notebook 01 end to end locally against Aura (unchanged; sanity check).
- Run notebook 02: confirm the CONFIG.txt fill rewrites `agent.py`, the deploy
  succeeds (own AWS account with the deploy policy), and both CLI and boto3
  invocations return grounded answers citing graph entities.
- Confirm no real credentials or generated ARNs are left staged for commit.

## Hero question

Use the same question in the opening demo and the notebook 02 invoke cells so
they match. All are entity-specific so the agent picks `graph_enriched_search`
and traverses company -> products and company -> risk factors.

**Primary:**

> What are NVIDIA's biggest risk factors, and which of its products are most
> exposed?

NVIDIA has the deepest graph (78 products, 161 risks). The answer needs the
traversal — products (A100, A800, China-export variants) linked to risks like
*AI Market Competition*, *China Market Risk*, *China Operations Transition*, and
*Channel Inventory* — so it showcases graph enrichment over plain semantic
search.

**Fallbacks:**

1. > What cybersecurity and business-interruption risks does Apple face?

   Apple-specific and consistent with the example already in `lab4.adoc:24`.
   Grounded in *Business Interruption* / *Catastrophic Events* risks.

2. > What wildfire and climate-related risks does PG&E disclose, and how do they
   > connect to its operations?

   The most distinctive answer in the dataset — *2017 Northern California
   Wildfire Claims*, *Aging Infrastructure*, *Air Quality and Climate Change
   Regulation* — with no overlap with the tech companies.
