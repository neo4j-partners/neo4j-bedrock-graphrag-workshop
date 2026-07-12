# Lab 5: Agent Memory with Neo4j

Add persistent memory to the Lab 4 Strands GraphRAG agent using
[neo4j-agent-memory](https://github.com/neo4j-labs/agent-memory). The memory layer uses the same
Neo4j Aura instance and Amazon Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`) as the earlier
labs, storing `Conversation`, `Message`, `Entity`, `Fact`, and `Preference` nodes alongside the SEC 10-K
knowledge graph.

## Notebooks

1. **`01_short_term_memory.ipynb`**, the conversational recall layer. Wraps the imported Lab 4 agent so
   each turn is written to memory, and injects prior context before each question. The headline demo asks
   about Apple's risk factors, then "their competitors", then a summary, showing cross-turn reference
   resolution.
2. **`02_long_term_memory.ipynb`**, the durable knowledge layer. Persists entities, facts, and
   preferences with `add_entity` / `add_fact` / `add_preference`, then recalls them from a fresh session.
   An optional cell adopts the existing SEC 10-K `Company` nodes as long-term entities.

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
