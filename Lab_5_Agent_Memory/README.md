# Lab 5: Agent Memory with Neo4j

Add persistent memory to the Lab 4 Strands GraphRAG agent using
[neo4j-agent-memory](https://github.com/neo4j-labs/agent-memory). The memory layer uses the same
Neo4j Aura instance and Amazon Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`) as the earlier
labs, storing `Conversation`, `Message`, `Entity`, `Fact`, and `Preference` nodes alongside the SEC 10-K
knowledge graph.

> **Run this in Amazon SageMaker AI.** These notebooks are designed to run in Amazon SageMaker AI Studio. Running them locally (e.g. VS Code) or elsewhere is not supported and will fail. Follow the [Environment Setup guide](https://neo4j-partners.github.io/neo4j-bedrock-graphrag-workshop/workshop/neo4j-bedrock-graphrag-workshop/1.0/part2-setup-instructions.html) to launch SageMaker AI Studio first.

## Notebooks

1. **`01_short_term_memory.ipynb`**, the conversational recall layer. Wraps the imported Lab 4 agent so
   each turn is written to memory, and injects prior context before each question. The headline demo asks
   about Apple's risk factors, then "their competitors", then a summary, showing cross-turn reference
   resolution.
2. **`02_long_term_memory.ipynb`**, the durable knowledge layer. Persists entities, facts, and
   preferences with `add_entity` / `add_fact` / `add_preference`, then recalls them from a fresh session.
   An optional cell adopts the existing SEC 10-K `Company` nodes as long-term entities.
3. **`03_deploy_to_agentcore.ipynb`** (optional), deploys the short-term-memory agent to Amazon Bedrock
   AgentCore Runtime, mirroring Lab 4's deployment. The handler wraps the GraphRAG tools with the memory
   layer, keyed on the AgentCore session, and the notebook drives a four-turn demo (and console-playground
   prompts) showing memory carry context across separate invocations.

These two notebooks cover the first two layers of a three-part memory model, short-term and
long-term, which together form a **context graph**. The third layer, reasoning traces (decision
traces and tool calls captured as first-class nodes), is covered as an optional "Going Further"
callout on the workshop site page rather than as a notebook.

## Key facts

- **Async API:** every memory call is a coroutine, so the notebooks prefix each one with `await`.
- **Bolt path against Aura:** the memory client connects with the direct Python driver, which is what
  unlocks the write-Cypher inspection queries and `adopt_existing_graph`.
- **Embedding-only:** Titan V2 supplies the vectors, no LLM is constructed, and entity extraction is
  turned off. The notebooks write memory explicitly, so no extractor model is needed.
- **Reuses the Lab 4 agent:** `01` imports `build_graphrag_agent` from Lab 4's `graphrag_agent` module
  rather than rebuilding the agent, so everything new here is the memory wrapping.

## Setup

Shared setup lives in `lib/memory_utils.py` (`build_memory_client`) and `lib/data_utils.py`. Both notebooks
open with a dependency install cell (`neo4j-agent-memory[bedrock]==0.5.0`) and read `CONFIG.txt` for the
Neo4j and AWS credentials.

## Clearing the memory

The memory layer writes into the **same** Aura database as the SEC 10-K graph, so clear it deliberately.
Run the Cypher below against the database the notebooks use (`NEO4J_DATABASE` in `CONFIG.txt`, which is not
always `neo4j`); in Neo4j Browser switch to it first with `:use <database>`.

### Clear one conversation (short-term)

To reset a single session so you can re-run `01_short_term_memory.ipynb`, delete its `Conversation` and
`Message` nodes:

```cypher
MATCH (c:Conversation {session_id: "<your-session-id>"})-[:HAS_MESSAGE]->(m:Message)
DETACH DELETE c, m
```

Or from Python, without Cypher: `await memory.short_term.clear_session(SESSION)`.

### Clear all memory

This removes everything the memory layer created (short-term, long-term, and the optional reasoning-trace
nodes) while leaving the SEC 10-K graph intact:

```cypher
// Nodes the library owns outright
MATCH (n)
WHERE n:Conversation OR n:Message OR n:Fact OR n:Preference
   OR n:ReasoningTrace OR n:ReasoningStep OR n:ToolCall OR n:Tool
   OR n:ConsolidationRun OR n:MemoryReadAudit OR n:User
DETACH DELETE n;

// Entities the library created, skipping SEC nodes adopted via adopt_existing_graph
MATCH (n:Entity)
WHERE NOT (n:Company OR n:Product OR n:RiskFactor OR n:AssetManager OR n:Document OR n:Chunk)
DETACH DELETE n;
```

> **Careful with `adopt_existing_graph`.** The optional cell in `02_long_term_memory.ipynb` adds the
> `:Entity` label to your existing `Company` nodes rather than creating new ones, so a plain
> `MATCH (n:Entity) DETACH DELETE n` would delete real SEC companies. The `WHERE NOT (...)` filter above
> protects them. If you ran that cell and want to fully undo it, strip the memory label instead of deleting
> the node:
>
> ```cypher
> MATCH (n:Company:Entity)
> REMOVE n:Entity, n.type, n.canonical_name, n.embedding
> ```
