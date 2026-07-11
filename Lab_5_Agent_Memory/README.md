# Lab 5: Agent Memory with Neo4j

Add persistent memory across conversation turns to the Lab 4 Strands GraphRAG agent using
[neo4j-agent-memory](https://github.com/neo4j-labs/agent-memory). The agent uses the same Neo4j Aura
instance and Amazon Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`) already configured in the
earlier labs, storing `Conversation`, `Message`, and `Entity` nodes alongside the SEC 10-K knowledge graph.

> **Status:** the hands-on notebooks for this lab are in development. The conceptual walkthrough is available
> in the workshop site under Part 3: Agent Memory.

## What you build

- Configure a `MemoryClient` against the existing Aura instance, using `bedrock/amazon.titan-embed-text-v2:0`
  for embeddings.
- Wrap the Lab 4 agent to write each turn to short-term memory.
- Call `memory.get_context(query)` before each invocation to inject prior conversation.

## The demo

1. "Tell me about Apple's risk factors" — answered from GraphRAG.
2. "What about their competitors?" — the agent resolves "their" to Apple via memory.
3. "Summarize what we discussed" — a coherent cross-turn summary.
