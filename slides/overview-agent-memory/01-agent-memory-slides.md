---
marp: true
theme: default
paginate: true
---

<style>
section {
  --marp-auto-scaling-code: false;
}

li {
  opacity: 1 !important;
  animation: none !important;
  visibility: visible !important;
}

/* Disable all fragment animations */
.marp-fragment {
  opacity: 1 !important;
  visibility: visible !important;
}

ul > li,
ol > li {
  opacity: 1 !important;
}
</style>

# Agent Memory with Neo4j

Giving the GraphRAG Agent Continuity Across Turns

---

## Why Stateless Agents Fail

The Lab 4 GraphRAG agent answers each question in isolation. Every invocation starts from zero context.

**Ask two questions in a row:**

1. "Tell me about Apple's risk factors."
2. "What about their competitors?"

The second question never names Apple. A stateless agent has nothing to resolve "their" against, so the follow-up falls apart.

**The gap:** continuity lives only in the language model's context window, which resets on every call.

---

## neo4j-agent-memory

The [`neo4j-agent-memory`](https://github.com/neo4j-labs/agent-memory) library adds a memory layer backed by Neo4j.

| Layer | Holds | Recalled by |
|-------|-------|-------------|
| **Short-term** | Recent conversation turns | `get_context(session_id=...)` |
| **Long-term** | Extracted entities, facts, preferences | `search_entities`, `search_facts` |

- Short-term memory recalls the current conversation, scoped to a `session_id`
- Long-term memory persists durable knowledge that survives across sessions
- Uses the same Aura instance and Amazon Titan Text Embeddings V2 as the earlier labs

---

## The Memory Graph Schema

Memory is stored as nodes and relationships in the **same Aura instance** as the SEC 10-K knowledge graph.

| Node | Role |
|------|------|
| **Conversation** | A session, keyed by `session_id` |
| **Message** | One user or assistant turn, ordered by timestamp |
| **Entity** | A durable thing worth remembering (deduplicated) |
| **Fact** | A subject, predicate, object statement |
| **Preference** | How the user likes answers shaped |

```cypher
(:Conversation {session_id})-[:HAS_MESSAGE]->(:Message {role, content, timestamp})
```

---

## One Database, Two Roles

Neo4j serves two jobs from a single graph:

- **Knowledge graph for retrieval:** companies, products, risk factors, chunks, embeddings, and the `chunkEmbeddings` vector index (Labs 1 through 4)
- **Memory store for agent state:** conversations, messages, entities, facts, and preferences

**Why this matters:**

- No second datastore to run, secure, or keep in sync
- Agent memory is queryable in Cypher right beside the domain data
- `adopt_existing_graph` layers memory over existing `Company` nodes instead of creating duplicates

---

## Wrapping the Agent

Two lines of memory work wrap each agent call:

```python
async def ask(question: str, session_id: str) -> str:
    # Before: pull relevant prior conversation, prepend it
    context = await memory.get_context(question, session_id=session_id)
    prompt = f"{context}\n\nUser question: {question}" if context else question

    agent.messages = []          # clear in-process history on purpose
    answer = str(agent(prompt))  # continuity now comes from Neo4j, not the model

    # After: persist both sides of the turn
    await memory.short_term.add_message(session_id, "user", question)
    await memory.short_term.add_message(session_id, "assistant", answer)
    return answer
```

Clearing `agent.messages` each turn proves the continuity comes from Neo4j-backed memory, not the model's own window.

---

## The Demo Arc

Three questions in one session, each building on the last:

| Turn | Question | What memory does |
|------|----------|------------------|
| 1 | "Tell me about Apple's risk factors." | GraphRAG retriever answers, turn written to memory |
| 2 | "What about their competitors?" | Prior context resolves "their" to Apple |
| 3 | "Summarize what we discussed." | Recalls the whole conversation from the graph |

Turn 2 and turn 3 only work because turn 1 was written to Neo4j and injected back in. The pattern survives a restart and scales across sessions and machines.

---

## Summary

- **Stateless agents lose the thread:** every call starts from zero context, so follow-ups have nothing to resolve against
- **neo4j-agent-memory** adds short-term memory for recent turns and long-term memory for entities and facts
- **Memory is a graph:** `Conversation`, `Message`, and `Entity` nodes in the same Aura instance as the knowledge graph
- **One database, two roles:** Neo4j as the retrieval knowledge graph and the agent memory store
- **The demo proves it:** cross-turn reference resolution and conversation summary, all from Neo4j

**Next:** Lab 6 serves graph retrieval as remote tools over the Neo4j MCP Server.
