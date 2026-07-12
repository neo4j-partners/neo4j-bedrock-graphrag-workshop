# Fix: Workshop Architecture Diagrams

## Context

The current `slides/images/workshop-architecture.png` (source `images/workshop-architecture.excalidraw`)
shows a clean logical flow (User Query -> AI Agent -> Tool Selection -> retrievers -> Neo4j Aura)
but has two problems for an AWS + Neo4j workshop:

1. **Wrong model label.** The middle tool box reads "Vector Search / Nova Embeddings". The code
   embeds with **Amazon Titan Text Embeddings V2** (`amazon.titan-embed-text-v2:0`, 1024 dims),
   not Nova. See `Lab_4_GraphRAG_Agent/lib/graphrag_agent.py:86-90` and `lib/data_utils.py`
   `get_embedder()`. No "Nova" embeddings exist anywhere in the code, config, or other diagram
   sources.
2. **No AWS infrastructure.** The diagram is purely conceptual. It never shows where the agent
   runs (SageMaker Studio notebooks), that the LLM and embeddings are **Amazon Bedrock**, that the
   Lab 4 agent deploys to **Amazon Bedrock AgentCore Runtime**, or that Lab 6 reaches Neo4j through
   an **AgentCore Gateway** MCP endpoint.

Two clarifications found while tracing this:

- The Excalidraw **source** (`images/workshop-architecture.excalidraw`) already reads "Titan
  Embeddings", so the checked-in PNG is simply **stale** and needs re-exporting. Every other
  diagram source also says Titan; "Nova" survives only as a historical comment in
  `financial_data_load/regenerate_titan_embeddings.py` (the project swapped Nova -> Titan).
- The source diagram shows **three** retrieval strategies (Vector Search, Text2Cypher, Cypher
  Template), because it is the *overall* workshop view spanning Labs 3/4 (vector + graph) and Lab 6
  (Text2Cypher). The diagrams below preserve that three-strategy framing rather than narrowing to
  one lab.

This doc proposes corrected ASCII diagrams that keep the simple teaching flow but layer in the real
AWS product footprint. The ASCII versions are the source of truth for what the redrawn Excalidraw
diagrams should contain.

## AWS product names (verified against AWS docs, July 2026)

From `docs.aws.amazon.com/bedrock-agentcore/latest/devguide/`:

- **Amazon Bedrock** - foundation model service. This workshop uses Claude Sonnet 4.5
  (`us.anthropic.claude-sonnet-4-5-20250929-v1:0`, a cross-region inference profile) for reasoning
  and Titan Text Embeddings V2 for vectors.
- **Amazon Bedrock AgentCore** - a set of services for deploying and operating AI agents in
  production. Component services: **Runtime**, **Gateway**, **Identity**, **Memory**,
  **Observability** (newer additions: Browser, Code Interpreter, Insights, Payments).
- **AgentCore Runtime** - serverless agent hosting. Each session runs in an isolated microVM.
  "Direct code deployment" ships a Python ZIP (no container to build), runs on Python 3.13 / arm64,
  and is invoked over a REST endpoint (`invoke_agent_runtime`, or the `agentcore` CLI).
- **AgentCore Gateway** - turns APIs and Lambda functions into agent tools over the **Model Context
  Protocol (MCP)**, and acts as a single governed (OAuth-gated) entry point in front of a runtime.
  Lab 6 talks to Neo4j through a Gateway MCP URL with a bearer token.
- **Amazon SageMaker Studio** - where the workshop notebooks execute; its execution role is what
  AgentCore deployment reuses/extends.

## Proposed Diagram 1: Workshop architecture with AWS infrastructure

The corrected replacement for `workshop-architecture.png`. Keeps the top-to-bottom teaching flow and
all three retrieval strategies, but adds an AWS Cloud boundary and makes Bedrock, SageMaker Studio,
and Neo4j Aura explicit. Uses the correct Titan label.

```
                                User Question
                                      |
                                      v
+================================= AWS Cloud (us-east-1) ==========================+
|                                                                                  |
|  +------------------------ Amazon SageMaker Studio -------------------------+    |
|  |   Strands Agent  (ReAct loop)                                            |    |
|  |   +------------------------------------------------------------------+   |    |
|  |   |  BedrockModel -> Claude Sonnet 4.5    reason + choose a tool      |   |    |
|  |   +------------------------------------------------------------------+   |    |
|  |             |                    |                       |               |    |
|  |             v                    v                       v               |    |
|  |   +-----------------+  +--------------------+  +--------------------+     |    |
|  |   | Vector Search   |  | Graph-Enriched     |  | Text2Cypher        |     |    |
|  |   | VectorRetriever |  | VectorCypher-      |  | (Lab 6, via MCP)   |     |    |
|  |   | (Lab 3/4)       |  | Retriever (Lab3/4) |  | LLM writes Cypher  |     |    |
|  |   +--------+--------+  +---------+----------+  +---------+----------+     |    |
|  +------------|--------------------|-----------------------|----------------+    |
|               |  embed query       |  embed + traversal    |  raw Cypher         |
|               +---------+----------+                       |  (no embedding)     |
|                         v                                  |                     |
|              +--------------------------+                  |                     |
|              |     Amazon Bedrock       |                  |                     |
|              |  Titan Text Embeddings   |                  |                     |
|              |  V2 (1024-dim vectors)   |                  |                     |
|              +------------+-------------+                  |                     |
|                           |  query vector                 |                     |
+===========================|===============================|=====================+
                            v                               v
              +--------------------------------------------------------+
              |                     Neo4j Aura                         |
              |   chunkEmbeddings vector index  +  fulltext indexes     |
              |   graph: Company / Product / RiskFactor / AssetManager  |
              |   (SEC 10-K Knowledge Graph)                            |
              +--------------------------------------------------------+
                            |
                            v
                     Grounded answer
```

Notes:
- Three strategies match the workshop's own architecture table (`overview-aws-neo4j` slides): Vector
  Search and Graph-Enriched come from the Lab 3/4 `neo4j-graphrag` retrievers; Text2Cypher is the
  Lab 6 MCP path where the LLM writes its own Cypher (drawn in full in Diagram 3).
- The two vector paths embed the query through Bedrock (Titan V2) before hitting `chunkEmbeddings`.
  Graph-Enriched then traverses `(:Chunk)-[:FROM_DOCUMENT]->(:Document)<-[:FILED]-(:Company)` to
  attach connected `Product` and `RiskFactor` names. Text2Cypher skips embeddings entirely.
- One-time seed load (Lab 1) is out of band: CSVs are hosted on a private **Amazon S3** bucket
  fronted by **CloudFront (OAC)** and pulled in with `LOAD CSV`. It is not part of the query-time
  flow, so it is omitted here.

## Proposed Diagram 2: Lab 4 deployment to AgentCore Runtime

Shows the "build it in a notebook, then deploy the same artifact to managed infra" story from
`slides/overview-agent-agentcore/01-agent-agentcore-slides.md` and `02_deploy_to_agentcore.ipynb`.

```
+========================== AWS Cloud (us-east-1) ============================+
|                                                                            |
|  +------------- Amazon SageMaker Studio -------------+                      |
|  |  02_deploy_to_agentcore.ipynb                     |                      |
|  |  bedrock-agentcore-starter-toolkit                |                      |
|  |  `agentcore deploy` (direct_code_deploy)          |                      |
|  |                                                   |                      |
|  |  agentcore_deploy/  -> agent.py (BedrockAgentCoreApp)                     |
|  |                        graphrag_agent.py, pyproject.toml                 |
|  +-----------------------+---------------------------+                      |
|                          |  1. zip + upload code                            |
|                          v                                                  |
|                   +-------------+      2. provision runtime                 |
|                   |  Amazon S3  |----------------------+                    |
|                   |  code bundle|                      |                    |
|                   +-------------+                      v                    |
|                                          +--------------------------------+ |
|   IAM: BedrockAgentCoreLabDeployPolicy   |  Amazon Bedrock AgentCore      | |
|   (execution role auto-created) ------>  |  Runtime                       | |
|                                          |  - isolated microVM per session| |
|                                          |  - Python 3.13 / arm64         | |
|                                          |  - retrievers built once (warm)| |
|                                          |  - fresh Agent per request     | |
|                                          +---------------+----------------+ |
|                                                          |  Bedrock calls   |
|                                    +---------------------+----------------+ |
|                                    |  Amazon Bedrock                        |
|                                    |  Claude Sonnet 4.5 + Titan Embeddings V2|
|                                    +---------------------+------------------+ |
+==========================================================|==================+
                                                           v
                                                   +----------------+
   client:  agentcore invoke  ---REST--->          |  Neo4j Aura    |
            boto3 invoke_agent_runtime             | vector + graph |
            (agentRuntimeArn, prompt payload)      +----------------+
```

Notes:
- `direct_code_deploy` bundles only the `agentcore_deploy/` directory, which is why the notebook
  copies `lib/graphrag_agent.py` into it and templates `NEO4J_URI`/`MODEL_ID`/`REGION` into
  `agent.py` at deploy time (the runtime has no `CONFIG.txt`).
- ECR is intentionally not used here (`ecr_auto_create: False`); direct code deploy skips the
  container build. Observability streams to CloudWatch.

## Proposed Diagram 3: Lab 6 MCP path through AgentCore Gateway

Shows the Text2Cypher agent reaching Neo4j through an AgentCore Gateway MCP endpoint. The MCP server
itself is deployed from the external `neo4j-partners/aws-starter` repo, so it is drawn as a boundary
box the workshop only consumes.

```
+---------------- Amazon SageMaker Studio ----------------+
|  01_mcp_text2cypher_agent.ipynb                          |
|                                                          |
|  Strands Agent  (ReAct: get schema -> write Cypher)      |
|  +----------------------------------------------------+  |
|  | BedrockModel -> Claude Sonnet 4.5                  |  |
|  +----------------------------------------------------+  |
|  | MCPClient over streamablehttp_client               |  |
|  | Authorization: Bearer <MCP_ACCESS_TOKEN>           |  |
|  +--------------------------+-------------------------+  |
+-----------------------------|----------------------------+
                              |  MCP over HTTPS (MCP_GATEWAY_URL)
                              v
             +-------------------------------------+
             |  Amazon Bedrock AgentCore Gateway   |
             |  managed HTTPS MCP entry point       |
             |  bearer-token gated (MCP_ACCESS_TOKEN)|
             +------------------+------------------+
                                |
                                v
   +--------- pre-deployed from neo4j-partners/aws-starter ---------+
   |  Neo4j MCP Server  (AgentCore-hosted)                          |
   |  tools:  get_neo4j_schema      read_neo4j_cypher               |
   |  Neo4j creds sourced from AWS Secrets Manager                  |
   +----------------------------+-----------------------------------+
                                |  Cypher over Bolt
                                v
                        +----------------+
                        |   Neo4j Aura   |
                        +----------------+
```

Notes:
- This path writes raw Cypher, so there are no embeddings on it (contrast with Diagram 1). The agent
  first calls `get_neo4j_schema`, reasons about it, then calls `read_neo4j_cypher` with read-only,
  LIMIT-bounded Cypher.
- `execute-query` and hybrid/vector tools sometimes shown in older diagram sources are not exposed by
  the deployed server; only the two read-only tools above are used.

## Scope and accuracy notes (so the redraw stays honest)

- **Only two AgentCore services are actually used:** Runtime (Lab 4) and Gateway (Lab 6). Do not add
  AgentCore Memory or Identity boxes. Lab 5 memory is Neo4j-based via the `neo4j-agent-memory` SDK,
  not AWS AgentCore Memory.
- **No Docker / ECR / Lambda.** Lab 4 uses `direct_code_deploy` (no container build); `lambda` and
  `ecr` do not appear as deployed resources.
- **Not part of the runtime footprint:** the AWS Glue / EMR / S3 Iceberg / Lake Formation pipeline is
  described in slides only as an aspirational production pattern; the real data load is CloudFront
  CSV `LOAD CSV`. Leave those out of the query-time diagrams.
- **Auth is a static bearer token** (`MCP_ACCESS_TOKEN`), not Cognito/OAuth. Secrets Manager belongs
  only to the external MCP server stack, not this repo.
- **Model-ID caveat:** `CONFIG.txt` and code use `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
  (Sonnet 4.5), while a few slides reference a `claude-sonnet-4-6` ID. The diagrams follow the code
  (Sonnet 4.5); the slide references should be reconciled separately.

## Suggested edits once these are approved

- Re-export `slides/images/workshop-architecture.png` from its source (the stale PNG still shows
  "Nova"; the source already says "Titan"), then extend `images/workshop-architecture.excalidraw`
  per Diagram 1 to add the AWS Cloud / SageMaker Studio / Bedrock / Neo4j Aura boundaries and
  re-export again.
- Optionally add a new Excalidraw + PNG for Diagram 2 (AgentCore Runtime deployment) to back the
  Lab 4 AgentCore slides, which currently have no matching image.
- Verify `images/mcp-agent-architecture.excalidraw` matches Diagram 3 (it already shows the two
  correct tools); update the stale `images/mcp-retrieval-architecture.excalidraw` that lists a third
  `execute-query` tool.
```
