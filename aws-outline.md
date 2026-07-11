# AWS Workshop Revamp Outline

---

## Concerns and Goals for This Revamp

**The core tension:** our tagline promises attendees they will build AI agents powered by knowledge graphs. When most of the session is spent on DBA work, there is a gap between expectations and experience.

* **Goal 1: Lead with the why.** The current intro moves straight to the architecture slide and into the lab. Frame the problem first using the product marketing narrative, then show a short demo of the finished build. The sequence becomes: why this matters, what you'll build, how to build it. Right now we skip the first two.

* **Goal 2: Preview the prototype early.** With provisioning and data loading constraints, it takes about 2.5 hours to reach the exciting part. Rather than fighting the setup time, show attendees the end state right at the top. 

* **Goal 3: Build a real call to action into the close.** The finish line is not "cool, we built a thing." It is attendees walking out ready to book a conversation with an AE or SE about their own use cases. Close with use cases tailored to the companies in the room, proof of where other companies are seeing value, and a clear invitation to take the next step.

---

## The Business Story: Why This Matters

The narrative arc for the opening of every session. This is the script behind the reworked strategic slides and the opening demo.

1. **The stakes.** Enterprises are putting GenAI agents into workflows where a wrong answer has real cost: investment research, compliance, risk reporting. In regulated industries, an answer that cannot be explained is an answer that cannot be used.

2. **The problem.** LLMs hallucinate, know nothing about your private data, and degrade as context grows. Vector-only RAG retrieves similar text but cannot traverse relationships, so it misses exactly what matters in financial data: shared executives across companies, cross-portfolio risk exposure, parent company disclosures.

3. **The shift.** GraphRAG grounds the agent in a knowledge graph. Retrieval returns connected, verifiable facts instead of pattern-matched chunks, and every answer can be traced back through the relationships that produced it. That is decision governance for regulated industries.

4. **The proof.** Hero questions no vector store can answer alone: "Which risk factors expose BlackRock's portfolio across multiple companies?" and "What risks does NVIDIA face, and which asset managers are exposed?"

5. **The payoff.** By end of workshop, attendees have built and deployed exactly this: a GraphRAG agent over real SEC 10-K data, running on Amazon Bedrock with AgentCore and Neo4j Aura.

---

## Section 1: Problems with the Current AWS Workshop

* **Marketplace setup kills momentum:** Lab 1 walks through AWS Marketplace provisioning step by step. It burns 20–30 minutes on operational mechanics before participants touch anything interesting. Databricks just has a sign-in.

* **Agents 101 is table stakes:** Lab 3 builds a basic Strands agent with toy tools (add_numbers, get_current_time). Most people at this workshop already know what an agent is. It delays the real content.

* **Pipeline is buried at the end:** Lab 6 covers data loading and embedding generation. That's the foundation of everything in Lab 4, but it comes last. The learning order is backwards.

* **No audience-adaptive path:** Every lab is sequential regardless of who is in the room. No way to skip basics for an advanced audience or add optional depth for those who want it.

---

## Section 2: New Outline

### Part 1 — Getting Started with Neo4j Aura and the Dataset

Goal: get everyone connected and oriented on the data in under 30 minutes. No marketplace walkthrough; attendees sign up for the Neo4j Aura free trial.

**Strategic Overview Slides** (5–10 minutes, before Lab 0)

Run before Lab 0. Follows the business story sequence: why this matters, what you'll build, how to build it. The problem comes first, the partnership follows the motivation.

* **Slide: The Problem Vectors Don't Solve**
  * Vector search finds similar content; it cannot traverse relationships
  * What vectors miss in financial data: shared executives across companies, cross-portfolio risk exposure, parent company disclosures
  * GraphRAG adds graph traversal on top of vector similarity to return connected, verifiable context

* **Slide: Context Graphs and Decision Governance**
  * Multi-agent systems make decisions across many steps with no record of why
  * Context graphs: Neo4j captures agent decision traces as nodes and relationships
  * Each action recorded with its inputs, tool calls, outputs, and links to prior steps
  * Enables audit trails and explainability for regulated industries

* **Slide: What We're Building Today**
  * A GraphRAG agent grounded in a real financial knowledge graph built from SEC 10-K filings
  * Deployed to Amazon Bedrock AgentCore Runtime for production hosting
  * Extended with persistent memory across conversation turns via neo4j-agent-memory
  * Accessible from any agent framework via the Neo4j MCP Server

* **Slide: Neo4j + AWS Strategic Partnership**
  * Neo4j and AWS have a Strategic Collaboration Agreement focused on reducing AI hallucinations in enterprise agents
  * Neo4j Aura is available on AWS Marketplace today
  * Key integrations this workshop covers: Amazon Bedrock AgentCore, Bedrock embeddings, Neo4j MCP Server
  * 2026 roadmap: AgentCore Memory connector, Bedrock Knowledge Bases GraphRAG backend, Marketplace Quick Launch

**Opening Demo: See the Finished Build**

Runs immediately after the strategic slides, before Lab 0. About 5 minutes. This is the answer to the 2.5-hour gap: attendees see the end state before any setup work begins.

* **What it is:** The instructor runs two or three hero questions live against the finished Lab 4 GraphRAG agent, pre-deployed to AgentCore Runtime before the event. Attendees watch the exact artifact they will build today, already deployed and answering questions.
* **Demo script:**
  * "Which risk factors expose BlackRock's portfolio across multiple companies?"
  * "What risks does NVIDIA face, and which asset managers are exposed?"
  * Show the agent's tool calls so attendees see the graph traversal happening, not just the final answer
  * Optional: run one question against vector-only retrieval, then against GraphRAG, and compare the two answers side by side
* **Pre-event checklist for the instructor:**
  * Deploy the Lab 4 agent to AgentCore against the instructor's own Aura instance, loaded with the seed dataset
  * Verify the hero questions return strong answers
  * Keep the endpoint live all day so attendees can hit the REST API during breaks
* **Callbacks during the day:** Each lab points back to this demo. Lab 3 builds the retriever behind the answers attendees saw this morning; Lab 4 deploys the same agent they watched run. Setup work reads as progress toward a known destination instead of DBA busywork.

---

* **Lab 0 — Aura Free Trial Sign-Up:** Sign up for the Neo4j Aura free trial, create an instance, save credentials to CONFIG.txt, and load the seed dataset so the graph and embeddings are ready for the labs.

  **Slides:**
  * Aura free trial sign-up: create the instance, capture the connection URL and password, save credentials to CONFIG.txt along with the Bedrock region
  * Seed data load: one provided load step brings in the 10-K graph, embeddings, and vector index
  * Architecture diagram: what the seed load provides (10-K graph, embeddings, vector index) vs. what participants build today
  * The dataset: SEC 10-K filings from S&P 500 companies, chunked, embedded, and loaded into the graph

* **Lab 1 — Explore the SEC 10-K Knowledge Graph:** Run introductory Cypher queries, explore companies, products, risk factors, executives, and relationships using the Neo4j browser.

  **Slides:**
  * Graph schema: node types (Company, Chunk, RiskFactor, Executive, Product) and the relationships connecting them
  * Why SEC filings are naturally graph-shaped: entities cross-referenced across filings, companies, and years
  * Sample traversal: from one company, follow relationships to shared executives at competitors and overlapping disclosed risk factors

* **Lecture — Why graphs for financial data:** Relationships that vectors miss: shared executives, overlapping risk factors, asset manager holdings across portfolios.

> Note: Aura Agents (current Lab 2) is removed. The no-code demo interrupts flow for engineers, and the workshop now goes straight from graph exploration into code.

---

### Part 2 — AWS ETL, Semantic Search, and GraphRAG

Goal: build GraphRAG end to end. This is the core of the workshop.

**Lab 2 — Data Pipeline (Optional — audience-dependent)**

Skip if the audience is non-technical or time is short. The rest of Part 2 uses the embeddings from the Lab 0 seed load and works without it.

* **What it covers:** Load SEC 10-K chunks into Neo4j, generate embeddings with Amazon Titan via Bedrock, create a vector index, link chunks to graph entities.
* **When to run it:** Advanced audience, full-day format, or when the instructor wants participants to understand where embeddings come from before using them.
* **When to skip it:** Half-day format, mixed audience, or when the goal is GraphRAG patterns rather than pipeline mechanics.

  **Slides:**
  * Pipeline overview: PDF text → chunks → Amazon Titan Embed → Neo4j vector index
  * Amazon Titan Text Embeddings V2: model ID `amazon.titan-embed-text-v2:0`, 1024 dimensions, text-only, called via Bedrock API
  * Neo4j vector index: creation syntax, cosine similarity metric, how Chunk nodes link to Company nodes via PART_OF

**Lab 3 — Semantic Search and GraphRAG**

Core lab. Uses loaded data (either from Lab 2 or from the Lab 0 seed load).

* **VectorRetriever:** Find relevant SEC chunks by semantic similarity.
* **VectorCypherRetriever:** Combine vector similarity with graph traversal — retrieve chunks, then follow relationships to companies, products, risk factors.
* **What participants see:** Why graph traversal returns richer context than vector search alone.

  **Slides:**
  * VectorRetriever: query → embedding → cosine similarity → top-k chunks returned as LLM context
  * VectorCypherRetriever: vector match first, then Cypher traversal extends results with connected graph context
  * Side by side: same question, vector-only context vs. GraphRAG context passed to the LLM
  * Why richer context reduces hallucination: the LLM answers from connected, verifiable facts rather than pattern-matched text

**Lab 4 — Strands GraphRAG Agent + AgentCore Deployment**

* **Build a Strands agent with GraphRAG tools:** Wire the VectorCypherRetriever into a Strands agent that answers natural-language questions about the SEC 10-K graph.
* **Run multi-hop queries:** Ask questions that span entities the agent must traverse to answer.
* **Deploy to AgentCore Runtime:** Deploy the GraphRAG agent built in the first notebook to Amazon Bedrock AgentCore using bedrock-agentcore-starter-toolkit. Participants invoke their own deployed agent via REST. This is a production deployment of a real artifact, not a placeholder.

  **Slides:**
  * Strands agent anatomy: `@tool` decorator, `BedrockModel` config, agent loop
  * Wiring GraphRAG as a tool: wrapping `VectorCypherRetriever` in a `@tool` function
  * AgentCore Runtime: microVM isolation, auto-scaling, REST endpoint, no infrastructure to manage
  * The key distinction: participants deploy the GraphRAG agent they built, not a toy example

---

### Part 3 — Agent Memory (Optional / Advanced)

Designed for all-day sessions or take-home completion. Builds directly on Part 2.

* **Lab 5 — Agent Memory with Neo4j:** Add `neo4j-agent-memory` to the Lab 4 Strands agent so it remembers across questions. Uses the same Neo4j Aura instance and Bedrock Titan embeddings already configured.
* **What participants build:**
  * Configure `MemoryClient` against the existing Aura instance (`bedrock/amazon.titan-embed-text-v2:0` for embeddings — no new models)
  * Wrap the Lab 4 agent to write messages to short-term memory after each turn
  * Call `memory.get_context(query)` before each invocation to inject prior conversation
* **What participants see:**
  * Turn 1: "Tell me about Apple's risk factors" — agent answers from GraphRAG
  * Turn 2: "What about their competitors?" — agent knows "their" means Apple because of memory
  * Turn 3: "Summarize what we discussed" — agent returns a coherent cross-turn summary
  * In Neo4j Browser: memory nodes (`Conversation`, `Message`, `Entity`) alongside the 10-K graph nodes in the same database

  **Slides:**
  * Why stateless agents fail in multi-turn conversations: every invocation starts from zero context
  * neo4j-agent-memory: short-term memory for recent turns, long-term memory for extracted entities and facts
  * Memory graph schema: `Conversation`, `Message`, and `Entity` nodes stored in the same Aura instance as the knowledge graph
  * One database, two roles: Neo4j as knowledge graph for GraphRAG retrieval and memory store for agent state

---

### Part 4 — MCP Server: The Production Integration Pattern (Optional / Advanced)

MCP is the recommended pattern for connecting agents to Neo4j in production. Strands, LangChain, Claude Desktop, and custom frameworks all connect to the same MCP server without embedding driver code in each application. Designed for all-day sessions or take-home completion. Builds directly on Parts 2 and 3.

* **Lab 6 — Neo4j MCP Agent:** Use the pre-deployed MCP server for schema discovery and read-only Cypher. Build Strands agents that access the graph through MCP tools instead of a direct driver connection.
* **Three MCP patterns:**
  * **Intro + schema discovery:** Explore what tools the MCP server exposes, run simple queries.
  * **Cypher Templates:** Tool wrappers with vector search + graph traversal via MCP.
  * **Text2Cypher:** Autonomous agent writes its own Cypher against the live schema.

  **Slides:**
  * Why MCP is the production integration pattern: framework-agnostic, no driver code per application, schema-aware tools
  * Neo4j MCP Server tools: `get_schema`, `execute_cypher`, `vector_search`
  * Three patterns from simple to autonomous: schema exploration, Cypher templates, Text2Cypher with live schema
  * Neo4j MCP Server is available on AWS Marketplace: deploy once, connect from any framework

---

### Production Path and Call to Action

Closer for all sessions. Run after whichever lab ends the day. The goal is conversion, not applause: attendees walk out ready to book a conversation with an AE or SE about their own use case.

* **Slide: Running This in Production**
  * AWS Marketplace Quick Launch: Neo4j Aura provisioned via CloudFormation, no manual console setup required
  * The AgentCore deployment from Lab 4 runs in production without changes to the agent code
  * Monitoring: CloudWatch for AgentCore invocations, Aura built-in metrics for query performance

* **Slide: What This Looks Like for You**
  * Use cases mapped to the companies in the room. Pre-event step for the AE/SE: identify attendee companies and prepare two or three tailored GraphRAG use cases
  * Patterns to draw from: fraud ring detection, supply chain risk, customer 360, compliance and audit trails
  * Template per use case: [company or industry], [the question their graph could answer], [what vectors alone would miss]

* **Slide: Where Others Are Seeing Value**
  * Proof points from companies already running GraphRAG in production [placeholder slots for approved customer stories and metrics]
  * Recurring themes: reduced hallucination in customer-facing agents, explainability in regulated industries, cross-entity questions that vector search alone cannot answer

* **Slide: Your Next Step**
  * Direct invitation: book a conversation with your AE or SE about your use case [QR code or calendar link placeholder]
  * What a follow-up engagement looks like: use-case discovery workshop, architecture review, Neo4j + AWS SCA co-build for enterprise engagements
  * Resources: Neo4j Aura on AWS Marketplace Quick Launch, Neo4j MCP Server Marketplace listing, neo4j-agent-memory at github.com/neo4j-labs/agent-memory, bedrock-agentcore-starter-toolkit

---

### Appendix — What Is an Agent?

Move Lab 3's basic agent content here. Reference for attendees who want the foundations.

* **Strands Agent basics:** Tool definitions with `@tool`, BedrockModel configuration, agent loop.
* **AgentCore deployment:** Deploy a Strands agent to AgentCore Runtime for serverless hosting. Include as optional for attendees who want a production deployment target.

---

## Section 3: Implementation Plan

This section translates the new outline into concrete repository changes. It exists to fix the ordering problem: the pipeline lab that loads data and generates embeddings currently runs last, even though the workshop instance is already loaded during setup and every earlier lab depends on the embeddings existing.

### The Core Problem in Concrete Terms

Tracing the current repo, the data flow is out of order:

1. **Lab 1 (Aura Setup)** loads only the structured layer through `LOAD CSV` in the Aura console: Company, Product, RiskFactor, AssetManager, Document, FinancialMetric, plus the `search_entities` fulltext index. No Chunk nodes, no embeddings, no vector index.
2. **Lab 4, notebook 01** (`01_load_and_query.ipynb`) adds the unstructured layer on top: it loads chunks and embeddings from `setup/seed-embeddings`, creates the `chunkEmbeddings` vector index, and links entities to chunks with `FROM_CHUNK`.
3. **Lab 6 (GraphRAG Pipeline, the last lab)** wipes the graph and rebuilds everything from `financial_data.json`, generating embeddings from scratch in an isolated sandbox.

So embedding generation, the conceptual foundation, is taught last, and the "how the data got here" story arrives after attendees have already used the data. The fix is to make the seed load complete and to move the pipeline forward as an optional early lab.

### Current to Target Lab Mapping

[cols="1,2,2"]
|===
| Current | Target | Action

| `Lab_0_Sign_In`
| Lab 0: Aura Free Trial Sign-Up + full seed load
| Repurpose from AWS sign-in to Aura sign-up. Fold the seed load in.

| `Lab_1_Aura_Setup`
| Lab 1: Explore the Knowledge Graph
| Keep exploration content. Move the CSV load into the Lab 0 seed step.

| `Lab_3_Intro_to_Bedrock_and_Agents`
| Appendix: What Is an Agent?
| Move out of the main path. Basic agent plus AgentCore deploy become reference.

| `Lab_4_GraphRAG_Search` nb 02, 03
| Lab 3: Semantic Search and GraphRAG
| VectorRetriever and VectorCypherRetriever notebooks become the core lab.

| `Lab_4_GraphRAG_Search` nb 04
| Lab 4: Strands GraphRAG Agent + AgentCore Deployment
| The GraphRAG agent notebook becomes its own lab with deployment.

| `Lab_4_GraphRAG_Search` nb 01
| Folds into Lab 0 seed load (see open decision 1)
| The chunk/embedding/index load moves into setup so downstream labs work without the pipeline.

| (new)
| Lab 5: Agent Memory with Neo4j
| Net-new lab built on `neo4j-agent-memory`. Does not exist in the repo yet.

| `Lab_5_MCP_Server`
| Lab 6: Neo4j MCP Agent
| Renumber. Content stays: intro, Cypher templates, Text2Cypher.

| `Lab_6_GraphRAG_Pipeline`
| Lab 2: Data Pipeline (Optional)
| Move forward to Lab 2. This is the "move lab 6 to lab 2" change.
|===

### The Data-Load Fix

The reordering only works if the seed load is self-sufficient. The plan:

1. **Extend the Lab 0 seed load to include the unstructured layer.** Add Chunk nodes, embeddings, and the `chunkEmbeddings` vector index to what setup provides, using the logic currently in `Lab_4/01_load_and_query.ipynb`. After Lab 0, the graph is complete: structured entities, chunks, embeddings, indexes. Embeddings are delivered as a provided data import, not generated live, so setup stays fast.
2. **Reposition the pipeline as optional Lab 2.** With the seed load complete, Lab 2 becomes a "here is how the embeddings were made" lab that any audience can skip. Labs 3 and 4 run on the seed-loaded data regardless.
3. **The pipeline wipes and rebuilds the shared workshop instance.** Lab 2 keeps the current Lab 6 behavior: it clears the graph and rebuilds the complete graph from `financial_data.json`, regenerating embeddings with Titan Text Embeddings V2. The rebuild must reproduce the full graph that Labs 3 and 4 expect: structured entities, chunks, embeddings, and the `chunkEmbeddings` vector index. Attendees who run Lab 2 replace the seed load with a freshly built, equivalent graph.

### Embedding Model Decision

The workshop standardizes on **Amazon Titan Text Embeddings V2** (`amazon.titan-embed-text-v2:0`) at **1024 dimensions**.

* Amazon Nova embeddings are multimodal (text, image, document, video), which the text-only SEC filings do not need.
* Titan Text Embeddings V2 is text-only, has an 8K-token context window, and supports configurable output dimensions of 256, 512, or 1024.
* 1024 dimensions matches the existing `chunkEmbeddings` vector index, so the index definition is unchanged. Only the model swaps from Nova to Titan v2.
* This requires updating `lib/data_utils.py` (`get_embedder`), the lab notebooks, the provided seed embeddings, and any slide or doc references that currently say Nova or 1536 dimensions.

### Repository Changes

* **Directory renames:** `Lab_6_GraphRAG_Pipeline` to a Lab 2 name, `Lab_4_GraphRAG_Search` split into Lab 3 and Lab 4, `Lab_5_MCP_Server` to Lab 6, `Lab_3_Intro_to_Bedrock_and_Agents` to an appendix location. Old `Lab_2_Aura_Agents` is already deleted.
* **Notebook moves:** Split `Lab_4_GraphRAG_Search` (nb 01 into seed, nb 02+03 into Lab 3, nb 04 into Lab 4).
* **Site (Antora):** Renumber `site/modules/ROOT/pages/lab*.adoc`, update `site/nav.adoc`, and rewrite `part1/part2/part3` pages to match the four-part structure. Add a `lab2.adoc` and a Lab 5 memory page.
* **New authoring:** Lab 5 Agent Memory notebooks and pages, built on `neo4j-agent-memory`.

### Resolved Decisions

1. **Seed-load scope.** Lab 0 loads the full graph: structured entities plus chunks, embeddings, and the vector index. Embeddings ship as a provided data import, not live generation.
2. **Pipeline target.** The optional Lab 2 wipes and rebuilds the shared workshop instance, reproducing the complete graph from `financial_data.json`.
3. **Embedding model.** Amazon Titan Text Embeddings V2 at 1024 dimensions. Nova is dropped because it is multimodal and unnecessary for text-only filings.
4. **Renumbering.** Rename the physical directories and Antora pages now, in this pass.

### Renaming Execution Order

Directory renames run in an order that avoids collisions with existing names:

1. `Lab_6_GraphRAG_Pipeline` to `Lab_2_Data_Pipeline` (frees Lab_6, the headline move).
2. `Lab_5_MCP_Server` to `Lab_6_MCP_Server`.
3. `Lab_3_Intro_to_Bedrock_and_Agents` to `Appendix_What_Is_An_Agent` (frees Lab_3).
4. `Lab_4_GraphRAG_Search` split: notebooks 02 and 03 to `Lab_3_GraphRAG_Search`, notebook 04 to `Lab_4_GraphRAG_Agent`, notebook 01's chunk/embedding/index logic folds into the Lab 0 seed load.
5. Reconstitute Lab 0 and Lab 1 from `Lab_0_Sign_In` and `Lab_1_Aura_Setup`: Lab 0 becomes Aura sign-up plus full seed load, Lab 1 becomes graph exploration.
6. Author `Lab_5_Agent_Memory` as net-new.

Site changes follow the same numbering: rename `site/modules/ROOT/pages/lab*.adoc`, update `site/nav.adoc`, and rewrite the part pages to the four-part structure.

---

## Section 4: Status and Progress

Status as of 2026-07-10, from a review of the working tree against the plan above. The structural reorganization is largely complete and staged; the remaining work is code migration, two unbuilt artifacts, and stale text cleanup.

### Done

* **Directory renames complete (staged).** All moves in the Renaming Execution Order are on disk and staged: `Lab_6_GraphRAG_Pipeline` to `Lab_2_Data_Pipeline`, `Lab_5_MCP_Server` to `Lab_6_MCP_Server`, `Lab_3_Intro_to_Bedrock_and_Agents` to `Appendix_What_Is_An_Agent`, and `Lab_4_GraphRAG_Search` split into `Lab_3_GraphRAG_Search` (nb 01 vector retriever, nb 02 vector-cypher retriever) and `Lab_4_GraphRAG_Agent` (nb 01 strands agent). `Lab_5_Agent_Memory` exists as a new directory. The old `Lab_4_GraphRAG_Search` directory has since been removed.
* **Antora site restructured to the four-part layout.** `site/nav.adoc` matches the target: Part 1 (Lab 0, Lab 1), Part 2 (Lab 2 optional, Lab 3, Lab 4), Part 3 (Lab 5 Agent Memory), Part 4 (Lab 6 MCP), plus the Appendix. `lab2.adoc`, `lab5.adoc`, and `lab6.adoc` all exist with matching instruction pages.
* **Documentation migrated to Titan embeddings.** Every `.adoc` page consistently references Amazon Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`) at 1024 dimensions. No `nova` or `1536` references remain in the docs.
* **Dimensions standardized at 1024 in code.** Every config defaults `embedding_dimensions` to 1024. No `1536` reference exists anywhere in code or notebooks; the dimension half of the embedding decision is effectively done.
* **Lab 3 notebook content is sound.** `01_vector_retriever.ipynb` covers semantic search through the full GraphRAG QA pipeline; `02_vector_cypher_retriever.ipynb` covers the custom Cypher retrieval query with a vector-only comparison. Both correctly assume the seed load already populated the graph and do not load data themselves.
* **Lab 4 agent notebook wires GraphRAG as tools.** `01_strands_graphrag_agent.ipynb` wraps both retrievers as Strands `@tool` functions and builds the agent with `BedrockModel`.
* **Lab 6 MCP notebook content is sound.** All three notebooks are present and cover intro/schema discovery, Cypher Templates, and Text2Cypher.
* **Strategic slides drafted.** `slides/overview-agents-mcp/` and `slides/images/` hold overview slide content and architecture diagrams; a `landing/index.html` and slide build script are committed.
* **Stale numbering and titles fixed (2026-07-11).** Root `README.md`, `Lab_3_GraphRAG_Search/README.md`, the `Lab_4_GraphRAG_Agent` notebook, and `Lab_6_MCP_Server` (README title, the `lib/lab_5_data_utils.py` → `lib/data_utils.py` rename with importers updated, and the "This completes Lab 6" cell) now carry the current numbering. A `Lab_4_GraphRAG_Agent/README.md` was added and the lab-to-lab "Next Steps" flow completed.

### Remaining Work (prioritized)

1. **Complete the Nova to Titan swap in code (highest priority, blocks correctness).** The docs say Titan but all executable code still uses Amazon Nova. `get_embedder`/`get_embedding` in `Lab_2_Data_Pipeline/lib/data_utils.py`, `Lab_3_GraphRAG_Search/lib/data_utils.py`, `Lab_4_GraphRAG_Agent/lib/data_utils.py`, and `financial_data_load/lib/data_utils.py` all return `BedrockNovaEmbeddings`. `Lab_6_MCP_Server/lib/lab_5_data_utils.py` hardcodes `amazon.nova-2-multimodal-embeddings-v1:0` with a Nova-specific request body. `financial_data_load/src/embeddings/bedrock.py` and `src/config.py` also reference Nova. Prose in `Lab_2_Data_Pipeline/02_embeddings.ipynb` and the model-access step in `setup/README.md` still name Nova. Until this is fixed, the code contradicts every slide and page.

2. **Make the Lab 0 seed load self-sufficient.** `setup/01_load_and_query.ipynb` loads only the unstructured layer (Chunk nodes with pre-computed embeddings, the `chunkEmbeddings` vector index, and the `FROM_DOCUMENT`/`NEXT_CHUNK`/`FROM_CHUNK` relationships). It `MATCH`es pre-existing Company, Product, RiskFactor, and Document nodes and assumes Lab 1 loaded the structured layer. The plan (Resolved Decision 1) requires Lab 0 to produce the complete graph on its own, and the `.adoc` pages already claim it does. The structured CSVs exist in `setup/seed-data/` but this notebook never reads them. Also fix the import path: the notebook imports `from lib.data_utils import get_embedder` but there is no `lib/` under `setup/`.

3. **Add AgentCore deployment to Lab 4.** `Lab_4_GraphRAG_Agent` has no `agentcore_deploy/` directory and no references to `bedrock-agentcore-starter-toolkit`. The revamp's core promise is that attendees deploy the GraphRAG agent they built and invoke it over REST, matching the opening demo. This is currently unfulfilled.

4. **Author the Lab 5 Agent Memory notebooks.** `Lab_5_Agent_Memory/` contains only a `README.md` marked "in development." The hands-on notebooks built on `neo4j-agent-memory` do not exist yet.

5. **Add the missing site pages.** There is no dedicated strategic-overview-slides page and no Production Path / Call to Action closer page in the Antora site. The slide content exists under `slides/` but is not surfaced as workshop pages, and the CTA closer from the outline has no page at all.

### Open Question for the Author

The Nova to Titan code swap and the self-sufficient seed load both touch shared `data_utils.py` copies and the seed data itself. Confirm before implementing: should the swap regenerate the provided `setup/seed-data/chunks.jsonl` embeddings with Titan (they were produced with Nova), or is the intent to keep the stored vectors and only change the query-time embedder to match? These must use the same model, or vector search returns garbage.
