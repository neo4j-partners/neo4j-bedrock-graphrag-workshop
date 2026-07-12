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

Three Kinds of Memory in One Graph

<!--
This deck covers the model behind agent memory: three connected kinds of
memory, stored as one graph. We focus on the memory concepts, not any managed
memory product.
-->

---

## What This Covers

- **Agents are amnesiacs:** flat context windows forget the plan
- **Three connected layers:** short-term, long-term, reasoning
- **Context graph:** captures the "why," not just the "what"
- **Reasoning traces:** first-class nodes make agents auditable
- **One graph:** memory sits beside the knowledge graph

<!--
Five ideas anchor the whole talk. Agents forget between calls. The fix is
structured memory in three connected layers. Together those layers form a
context graph that records reasoning, not just actions. And it all lives in one
Neo4j instance next to the domain knowledge graph.
-->

---

## Why Stateless Agents Fail

A stateless GraphRAG agent answers each question in isolation.

**Ask two questions in a row:**

1. "Tell me about Apple's risk factors."
2. "What about their competitors?"

- **The gap:** "their" has nothing to resolve against
- **Vector recall is not enough:** similarity gives recall, not understanding

<!--
The second question never names Apple. Continuity lived only in the model's
context window, which resets every call. Stuffing transcripts back in works
until the conversation gets long and facts contradict. Vector search over a
pile of chunks gives you recall by similarity, but not a structured
understanding of what connects to what.
-->

---

## Agent Memory and Context Graphs

- **Agent memory:** durable, queryable record of what an agent knows and has done
- **Context graph:** a knowledge graph that captures decision traces, grounded in real entities
- **The relationship:** the context graph *is* the memory: one model spanning short-term, long-term, and reasoning
- **Composable:** store, query, and scale each layer on its own, yet keep them connected

<!--
Agent memory and context graph are two names for the same thing at different
altitudes. Memory is the capability; the context graph is how you model it.
Jim Webber calls the composable version a Sim City data model: three graphs
that connect, but that you can store, query, and scale on their own.
-->

---

## Three Kinds of Memory

- **Short-term:** conversation and session history
- **Long-term:** durable entities, facts, and preferences
- **Reasoning:** decision traces and tool calls

All three connected as nodes in **one graph**.

<!--
This is the framework for the rest of the deck. Short-term is the conversation.
Long-term is the knowledge the agent accumulates about the world. Reasoning is
the record of how it solved things. The next slide shows how they link.
-->

---

![bg contain](neo4j-agent-memory-diagram.png)

<!--
The green chain is short-term memory: a Conversation and its Messages. Orange is
long-term memory: entities like Person and Organization joined by typed
relationships such as WORKS_AT. Purple is reasoning memory: a Message triggers a
ReasoningTrace, which has steps, which use tool calls. Dashed edges cross the
layers: a Message mentions an entity, a ToolCall retrieved an entity. One graph,
three colors.
-->

---

## Short-Term Memory

- **What it is:** the running conversation, the turns in the current session
- **Like:** working memory, what the agent is actively holding
- **Example:** remembers you were asking about Apple, so the next question lands
- **Scoped:** one session only, then it fades

<!--
Short-term memory is the agent's working memory: ordered conversation turns
scoped to one session. It is what resolves "their" to Apple. It also gives
multi-agent systems a shared view of what each agent is currently working on.

Under the hood it is keyed by session_id and modeled as a linked list of turns,
(Conversation)-[:FIRST_MESSAGE]->(Message)-[:NEXT_MESSAGE]->(Message), recalled
with a call like get_context(session_id=...).
-->

---

## Long-Term Memory

- **What it is:** durable knowledge kept across sessions: entities, facts, preferences
- **Like:** semantic memory, what the agent knows about the world
- **Example:** "Apple competes with Samsung"; the user prefers concise answers
- **Deduplicated:** the same entity resolves to one node, not a new node each time it's mentioned

<!--
Long-term memory is the knowledge graph the agent grows, its semantic memory:
what it knows about the world, held across sessions. This is where memory
augments the model's lossy training with curated ground truth.

Under the hood, entities are classified with the POLE+O model (Person,
Organization, Location, Event, Object) and joined by typed relationships such as
(Entity:Person)-[:WORKS_AT]->(Entity:Organization). Entity resolution keeps John
Mercer one node, not five.
-->

---

## Reasoning Memory and Traces

- **What it is:** a record of how the agent reached an answer: its decisions and tool calls, saved as nodes
- **Like:** procedural memory, how the agent did something
- **Example:** a search tool ran, found Samsung, and that shaped the competitors answer
- **Auditable:** answers "why did the agent decide this?"

<!--
Reasoning memory is the agent's procedural memory: how it solved something, not
just what it concluded. Traces are not log lines, they are graph nodes with
typed edges to the entities and messages that informed each decision. That is
what turns an agent from a black box into an auditable system, the question
regulators always ask.

Under the hood: (Message)-[:TRIGGERED]->(ReasoningTrace)-[:HAS_STEP]->
(ReasoningStep), each step (ReasoningStep)-[:USED_TOOL]->(ToolCall)-[:CALL_OF]->
(Tool), and a ToolCall links back with RETRIEVED to the entity it touched.
-->

---

## One Graph, Connected Layers

Traverse across all three layers in one query:

```
(Message) -[:MENTIONED_IN]-> (Entity) <-[:RETRIEVED]- (ToolCall)
```

- **Deterministic:** graph traversal, not a similarity threshold
- **Provenance chain:** one agent's reasoning links to another's findings

<!--
Because the layers share one graph, you can walk from a message to the entity it
mentioned to the tool call that retrieved it. That traversal is guaranteed, not
probabilistic. In multi-agent setups every agent reads and writes the same
graph, so a flag one agent raises is visible to the next with no message
passing.
-->

---

## Best Practices

- **Design memory explicitly:** separate working from durable state
- **Capture the why:** reasoning and causal chains, not just actions
- **Traces as first-class nodes:** for explainability and audit
- **Deduplicate entities:** exact, then fuzzy, then semantic
- **Curate and compress:** messages to observations to a reflection

<!--
Treat memory as a first-class part of the architecture. Store durable state in a
form you can query, audit, and update. Keep reasoning as graph nodes. Resolve
duplicate entities with a cascade. And compress continuously so memory does not
grow without bound: raw messages summarize into observations, observations into
a single active reflection.
-->

---

## Why Memory Makes an Agent

| Dimension | Without memory | With memory |
|---|---|---|
| **Continuity** | forgets you were discussing Apple | carries Apple into the next question |
| **Knowledge** | re-derived every call | long-term accumulates facts |
| **Accountability** | opaque black box | reasoning traces show *why* |

Memory is what turns a generative model into an agent.

<!--
Each row maps to one of the three layers. Without short-term memory the second
question has nothing to resolve "their" against. Without long-term memory the
agent re-derives the same facts every call instead of accumulating them. Without
reasoning memory its decisions are opaque. A generative model ends with text to
read; an agent ends with work done, and that requires state that persists.
-->

---

## Summary

- **Memory is a graph:** short-term, long-term, and reasoning, connected
- **Context graph:** records the reasoning behind decisions
- **Reasoning traces:** first-class nodes make the agent auditable
- **One database, two roles:** knowledge graph and memory store

**Next:** serve graph retrieval as remote tools over the Neo4j MCP Server.

<!--
Structured memory in three connected layers is what lets an agent hold a plan,
ground its answers, and explain its decisions. It all runs in the same Neo4j
instance as the SEC knowledge graph, no second datastore to keep in sync.
-->

---

## Appendix: References

1. Context graphs: why AI agents need three types of memory (Webber) - neo4j.com/blog/agentic-ai/context-graph-ai-agent-memory/
2. Agentic AI vs. generative AI (Krüger) - neo4j.com/blog/agentic-ai/agentic-ai-vs-generative-ai/
3. Modeling agent memory (Gilmore) - neo4j.com/blog/developer/modeling-agent-memory/
4. Hands on with context graphs and Neo4j (Lyon) - neo4j.com/blog/agentic-ai/hands-on-with-context-graphs-and-neo4j/
5. When your agents share a brain: multi-agent memory (Lyon) - medium.com/neo4j
6. Agent Memory, Neo4j Labs - neo4j.com/labs/agent-memory/
7. A tour of the Neo4j Agent Memory Service (Lyon, concepts only) - medium.com/neo4j
