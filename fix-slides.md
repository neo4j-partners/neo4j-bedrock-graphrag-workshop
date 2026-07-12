# Plan: Align Slides and Site with the Revamped Outline

This plan brings `slides/` and `site/` into line with `course-outline.md`. The lab directories and notebooks were already reorganized to the four-part structure. The slide decks and several site pages still reflect the old numbering, the old AWS-lakehouse pipeline narrative, and the old "lead with architecture" flow. This plan reorders the decks, fixes the stale content, and adds the three segments the outline calls for that have no slides today: the strategic opening, agent memory, and the call-to-action close.

## Target Structure

The outline defines this run of show. Slides and site should match it end to end.

| Segment | Content | Deck |
| --- | --- | --- |
| Opening | Business story: the problem, the shift, the proof, the payoff, partnership, opening demo | New deck |
| Part 1 | Lab 0 AWS/Bedrock sign-in, Lab 1 Aura setup + seed load + exploration | aws-neo4j (reframed) + knowledge-graph |
| Part 2 | Lab 2 pipeline (optional), Lab 3 semantic search + GraphRAG, Lab 4 agent + AgentCore | graphrag + retrievers + new Lab 4 agent deck (split from agents-mcp) |
| Part 3 | Lab 5 agent memory (optional) | New deck |
| Part 4 | Lab 6 MCP server (optional) | New deck (Lab 6 MCP, split from agents-mcp) |
| Close | Technical production path (existing `production-path.adoc`); no sales CTA | none |

## Current-to-Target Lab Numbering

Every deck uses the old numbering. The mapping to apply everywhere:

| Old reference in slides | New |
| --- | --- |
| Lab 3 = Strands intro agent (toy tools) | Appendix: What Is an Agent? |
| Lab 4 = neo4j-graphrag retrievers | Lab 3 = Semantic Search and GraphRAG |
| Lab 4 nb 04 = Strands GraphRAG agent | Lab 4 = GraphRAG Agent + AgentCore |
| Lab 5 = MCP server | Lab 6 = Neo4j MCP Agent |
| Lab 6 = data pipeline (bonus) | Lab 2 = Data Pipeline (optional) |
| (none) | Lab 5 = Agent Memory (new) |

## Resolved Decisions

- **Lab 0 and Lab 1.** Lab 0 stays AWS Console sign-in plus Amazon Bedrock model access. Lab 1 is Neo4j Aura setup, the seed dataset load, and graph exploration. The outline (`course-outline.md`) was updated to match this current state.
- **Pipeline narrative.** Keep the S3 + Iceberg + Glue/Spark + Neo4j Spark Connector lakehouse pipeline in the decks as the production pattern for how data reaches the graph. Frame the workshop hands-on version as the optional Lab 2 that rebuilds from `financial_data.json` with Titan embeddings.
- **Agents/MCP deck.** Split the `overview-agents-mcp` deck into two: a Lab 4 deck (GraphRAG agent + AgentCore) and a Lab 6 deck (MCP patterns).
- **Opening and close.** Surface the business-story opening as a slide deck only. No new Antora pages.
- **Call to action.** Skip the sales CTA close. No CTA deck and no CTA page. `production-path.adoc` remains the technical closer.

---

## Part A: Slide Decks (`slides/`)

Five decks exist today: `overview-aws-neo4j`, `overview-knowledge-graph`, `overview-graphrag`, `overview-retrievers`, `overview-agents-mcp`. The plan keeps and fixes four of them, splits `overview-agents-mcp` into two, and adds two new decks, for eight total: business story (new), aws-neo4j, knowledge-graph, graphrag, retrievers, agent + AgentCore (new, from the split), MCP (new, from the split), agent memory (new). Each new deck must be registered in `slides/scripts/build-slides.mjs` (`decks` array: `key`, `dir`, `source`, `title`, `description`) and described in `slides/README.md`. The old `agents-mcp` key is retired.

### A1. New deck: `overview-business-story` (opening)

The outline's highest-priority gap. Leads with the why before any architecture. Slides, following the business-story arc:

1. **The stakes.** Enterprises put GenAI agents into investment research, compliance, and risk reporting where a wrong or unexplainable answer has real cost.
2. **The problem vectors do not solve.** Vector search finds similar text but cannot traverse relationships. In financial data it misses shared executives across companies, cross-portfolio risk exposure, and parent company disclosures.
3. **The shift to GraphRAG.** Retrieval returns connected, verifiable facts instead of pattern-matched chunks, and every answer traces back through the relationships that produced it.
4. **Context graphs and decision governance.** Neo4j captures agent decision traces as nodes and relationships, giving audit trails and explainability for regulated industries.
5. **The proof: hero questions.** "Which risk factors expose BlackRock's portfolio across multiple companies?" and "What risks does NVIDIA face, and which asset managers are exposed?"
6. **What we are building today.** A GraphRAG agent over real SEC 10-K data, deployed to Amazon Bedrock AgentCore, extended with neo4j-agent-memory and the Neo4j MCP Server.
7. **Neo4j + AWS partnership.** Joint partnership focused on reducing hallucinations, Aura on AWS Marketplace, key integrations, and the 2026 roadmap.
8. **Opening demo (instructor).** A holder slide plus speaker notes for running the hero questions live against the pre-deployed Lab 4 agent, showing tool calls and an optional vector-only vs GraphRAG comparison.

### A2. `overview-aws-neo4j` (reframe as workshop roadmap)

With the business story moved to its own deck, this deck becomes the architecture and roadmap deck. Required changes:

- **Keep the AWS-lakehouse pipeline narrative as the production pattern.** The "Data Pipeline: AWS Lakehouse to Neo4j" slide, the Glue/EMR/Spark Connector/Iceberg/medallion content in "Why Neo4j + AWS", and `workshop-architecture.svg` stay. Frame this explicitly as how data reaches the graph in production. Add a line noting that the workshop's hands-on version is the optional Lab 2, which rebuilds from `financial_data.json` with Titan embeddings rather than running the full lakehouse job.
- **Fix the roadmap slide.** "Part 2: Labs 3-5" and "Part 3: Bonus Lab 6" are wrong. Use the four-part structure: Part 1 (Labs 0-1), Part 2 (Labs 2-4), Part 3 (Lab 5), Part 4 (Lab 6), plus the appendix.
- **Fix the "Lab Progression" table.** Currently Lab 0 = AWS sign-in, 1 = Aura, 3 = Strands, 4 = retrievers, 5 = MCP, 6 = pipeline. Renumber to the target table above.
- **Fix "From Code-First to Full Autonomy"** and "What Each Platform Brings" lab references to the new numbering.
- **Update the embeddings row** wording is already Titan V2, keep it.

### A3. `overview-knowledge-graph` (Lab 1)

Content is sound. Fixes:

- **"Data Loading Pattern" slide** says "Lab 1 loads the knowledge graph using Cypher." This stays accurate: Lab 1 sets up Aura and loads the seed dataset. Clarify that the seed load is a provided import of the complete graph (structured entities, chunks, embeddings, vector index), and present the MERGE pattern as how that structured layer is built.
- **Vector index slide** references "Labs 4-6"; change to "Lab 2 and Lab 3."
- **"What Comes Next"** lists Lab 1/4/5/6; renumber to Lab 1 explore, Lab 2 pipeline, Lab 3 retrievers, Lab 6 MCP.

### A4. `overview-graphrag` (Lab 3 foundations)

Strong content. Fixes are all numbering and pipeline placement:

- **"Three Retrieval Strategies"** and "Choosing" reference "Labs 4 and 5"; Text2Cypher is now Lab 6, retrievers are Lab 3.
- **"Building the Pipeline"** slide says "Lab 4 loads pre-built data. Lab 6 builds this pipeline." Change to "the Lab 1 seed load provides this data. The optional Lab 2 builds this pipeline from scratch." Note that the full production pipeline is the lakehouse pattern shown in the workshop-overview deck.
- **"What Comes Next"** renumber: Lab 3 retrievers, Lab 6 MCP, Lab 2 pipeline.
- `data-pipeline-v2.png` can keep showing the workshop Lab 2 flow (chunk, Titan embed, index). The lakehouse production diagram stays in the workshop-overview deck.

### A5. `overview-retrievers` (Lab 3)

Technical content is accurate. Fixes:

- **Deck title and framing** reference "Lab 4"; this is now Lab 3.
- **"Lab 4 Notebook Progression"** lists four notebooks (01 Load and Query, 02 VectorRetriever, 03 VectorCypher, 04 Strands agent). The new Lab 3 has two notebooks: `01_vector_retriever.ipynb` and `02_vector_cypher_retriever.ipynb`. The agent moves to Lab 4. Rewrite this slide to the two-notebook Lab 3 layout and point the agent forward to Lab 4.
- **"What the Library Does Under the Hood"** and the closing summary say "In Lab 5 you do each yourself through MCP"; change to Lab 6.
- **Text2Cypher references** labeled "(Lab 5)"; change to Lab 6.

### A6. Split `overview-agents-mcp` into a Lab 4 deck and a Lab 6 deck

The deck currently mixes the toy-agent intro, the GraphRAG agent, AgentCore, and MCP. Split it into two decks. Register both new keys in `build-slides.mjs` and `README.md`, and retire the old combined `agents-mcp` key.

**New deck 1: `overview-agent-agentcore` (Lab 4).** Agent fundamentals as they apply to the GraphRAG agent, plus deployment:

- ReAct pattern and the Strands Agents SDK, kept from the current deck.
- **Replace the toy-tool example** (`get_current_time`, `add_numbers`) with the GraphRAG `@tool` wrapping `VectorCypherRetriever` so the example matches Lab 4. The toy tools belong to the appendix.
- **AgentCore deployment**, renumbered from "Lab 3" to Lab 4, tied to deploying the GraphRAG agent the attendee built, matching the opening demo. Add the `bedrock-agentcore-starter-toolkit` and REST-invoke detail from the outline.

**New deck 2: `overview-mcp` (Lab 6).** The MCP production pattern:

- MCP architecture, Neo4j MCP Server tools, and the `lab6-mcp-agent-architecture.svg` diagram, kept from the current deck.
- **Cypher Templates** and **Text2Cypher** slides, renumbered from "Lab 5" to Lab 6, including the notebook progression.
- **Add an MCP-as-production-pattern slide**: framework-agnostic, one server for any framework, available on AWS Marketplace, matching the Part 4 slides in the outline.
- Fix the closing summary "knowledge graph from Labs 1-4" to the new numbering.

### A7. New deck: `overview-agent-memory` (Lab 5)

No deck exists for agent memory. Slides from the Part 3 outline:

- Why stateless agents fail across turns: every invocation starts from zero context.
- neo4j-agent-memory: short-term memory for recent turns, long-term memory for extracted entities and facts.
- Memory graph schema: `Conversation`, `Message`, `Entity` nodes in the same Aura instance as the knowledge graph.
- One database, two roles: Neo4j as knowledge graph for retrieval and memory store for agent state.
- Demo arc: turn 1 answers from GraphRAG, turn 2 resolves "their competitors" from memory, turn 3 summarizes the conversation.

### A8. No CTA deck

The sales call-to-action close is out of scope. The technical `production-path.adoc` page stays as the closer. No CTA slide deck is authored.

---

## Part B: Site Pages (`site/`)

### B1. `slides.adoc`

The deck gallery table lists five decks and pairs them to labs with some stale mappings. Changes:

- Update the intro from "Five presentation decks" to eight.
- Add rows for the new decks: business story (pairs with the opening and Part 1), agent + AgentCore (pairs with Lab 4), MCP (pairs with Lab 6), agent memory (pairs with Lab 5).
- Replace the single agents-mcp row with the two split decks.
- Fix the retrievers row, which still describes Lab 4 numbering, to Lab 3.
- Order the table to match the run of show: business story, aws-neo4j, knowledge-graph, graphrag, retrievers, agent + AgentCore, agent memory, MCP.

### B2. `nav.adoc`

- Lab 0 label stays "Lab 0: Sign In to AWS" and Lab 1 stays "Lab 1: Neo4j Aura Setup and Exploration." This already matches the resolved Lab 0 decision, so no relabeling is needed.
- Confirm the "Workshop Slides" entry still points to the gallery. No structural nav change is needed: the new decks surface through `slides.adoc`, and the opening and close stay decks only rather than nav pages.

### B3. Part 1 pages

- No content move is needed. Lab 0 stays AWS sign-in and Bedrock access (`lab0.adoc`, `lab0-instructions.adoc`), and Lab 1 keeps the Aura setup, seed load, and exploration content (`lab1.adoc`, `lab1-instructions.adoc`, `lab1-explore.adoc`). Confirm each page already reflects Titan V2 and the complete seed load.

### B4. `landing/index.html`

The three summary cards use the old three-part framing: "Setup & Visual Exploration," "Python GraphRAG," "Agents & Pipeline," and the phrase "no-code visual exploration." Rewrite to the four-part structure and drop the no-code wording, since the Aura Agents no-code lab was removed.

### B5. Call-to-action page

No change. The sales CTA close is out of scope. `production-path.adoc` stays as the technical closer covering harden the graph, scale retrieval, operate the agent, and grow the pipeline.

---

## Sequencing

1. Fix numbering across the four kept decks: A2 aws-neo4j (keep lakehouse as production, add the Lab 2 note), A3 knowledge-graph, A4 graphrag, A5 retrievers. Mechanical and unblocks everything.
2. Split `overview-agents-mcp` into the Lab 4 agent + AgentCore deck and the Lab 6 MCP deck (A6). Register both keys and retire the old one.
3. Author the two new decks: business story (A1) and agent memory (A7). Register them in `build-slides.mjs` and `README.md`.
4. Update `slides.adoc` and `landing/index.html` (B1, B4).
5. Build the decks with `npm run build` in `slides/` and verify the gallery renders all eight.

---

## Implementation Status

**Parallelization:** The content work fans out to 7 parallel agents, each owning a disjoint set of files. The only write-contention point is the two shared registration files (`slides/scripts/build-slides.mjs` and `slides/README.md`), which the coordinator owns exclusively. Agents are forbidden from touching them. The final build runs serially after all agents complete.

**Fixed deck registry** (coordinator writes this; agents must use these exact dir/source names):

| Order | key | dir | source | title |
| --- | --- | --- | --- | --- |
| 1 | `business-story` | `overview-business-story` | `01-business-story-slides.md` | Business Story |
| 2 | `aws-neo4j` | `overview-aws-neo4j` | `01-aws-neo4j-workshop-slides.md` | Workshop Architecture & Roadmap |
| 3 | `knowledge-graph` | `overview-knowledge-graph` | `01-knowledge-graph-foundations-slides.md` | Knowledge Graph Foundations |
| 4 | `graphrag` | `overview-graphrag` | `01-graphrag-foundations-slides.md` | GraphRAG Foundations |
| 5 | `retrievers` | `overview-retrievers` | `01-retrievers-overview-slides.md` | Retrievers Overview |
| 6 | `agent-agentcore` | `overview-agent-agentcore` | `01-agent-agentcore-slides.md` | GraphRAG Agent & AgentCore |
| 7 | `agent-memory` | `overview-agent-memory` | `01-agent-memory-slides.md` | Agent Memory |
| 8 | `mcp` | `overview-mcp` | `01-mcp-slides.md` | Neo4j MCP Agent |

Old `agents-mcp` key / `overview-agents-mcp` dir retired.

| Item | Owner | Parallel? | Status |
| --- | --- | --- | --- |
| A2 aws-neo4j numbering + Lab 2 note | Agent 1 | yes | DONE |
| A3 knowledge-graph numbering | Agent 2 | yes | DONE |
| A4 graphrag numbering + pipeline placement | Agent 3 | yes | DONE |
| A5 retrievers numbering + 2-notebook layout | Agent 4 | yes | DONE |
| A1 new business-story deck | Agent 5 | yes | DONE (9 slides, no em-dashes) |
| A6 split agents-mcp → agent-agentcore + mcp | Agent 6 | yes | DONE (agent-agentcore 9 slides, mcp 13 slides, png git-moved, old dir removed) |
| A7 new agent-memory deck | Agent 7 | yes | DONE (8 slides, no em-dashes) |
| build-slides.mjs registration (shared) | Coordinator | serial | DONE (8 decks, run-of-show order, agents-mcp retired) |
| README.md deck list (shared) | Coordinator | serial | DONE |
| B1 slides.adoc gallery | Coordinator | yes | DONE (8 rows, run-of-show order) |
| B4 landing/index.html four-part | Coordinator | yes | DONE (4 cards, no-code wording dropped) |
| B2 nav.adoc | Coordinator | confirm-only | DONE (already matches, no change) |
| B3 Part 1 pages | Coordinator | confirm-only | DONE (already Titan V2 + complete seed load + correct numbering) |
| Final `npm run build` + verify | Coordinator | serial (last) | DONE (built under Node 22; gallery renders all 8) |

### Quality review (post-implementation)
- **Cross-deck lab numbering:** swept all 8 decks; fully consistent with the target mapping, no stale patterns (`Labs 3-5`, `Bonus`, `agents-mcp`, `no-code`, `four notebooks`) remain.
- **agent-memory deck:** verified API and schema against the real Lab 5 notebooks (`get_context`, `short_term.add_message`, `search_entities/facts`, `adopt_existing_graph`, `HAS_MESSAGE`, `github.com/neo4j-labs/agent-memory`). Accurate.
- **FIXED — business-story partnership slide:** the three specific "2026 roadmap" bullets (AgentCore Memory connector, Bedrock Knowledge Bases GraphRAG backend, Marketplace Quick Launch) were agent-invented; not in `course-outline.md` (which only says "joint partnership and 2026 roadmap"). Replaced with sourced/generic framing plus an instructor speaker-note placeholder to insert the real, publicly announced roadmap.
- **FIXED — agent-agentcore "Why a Specialized Graph Agent":** relocated slide described "inspect schema, write Cypher, execute it" (that is the Lab 6 Text2Cypher agent). Reworded to graph retrieval, matching the Lab 4 retriever-based agent.
- Rebuilt after fixes: clean, 8 cards.

### Notes / follow-ups
- **Build requires Node 22** (`brew install node@22`); Marp breaks on Node 25+. Built with `PATH="/opt/homebrew/opt/node@22/bin:$PWD/node_modules/.bin:$PATH" node scripts/build-slides.mjs`.
- **Em-dashes:** the two new decks (business-story, agent-memory) are em-dash-free per the project style rule. The six kept/split decks still contain pre-existing em-dashes in content that was only renumbered or relocated verbatim (out of scope for the requested numbering fixes). Strip them repo-wide only if requested.
