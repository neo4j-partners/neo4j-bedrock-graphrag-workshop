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

# The Business Case for GraphRAG

Why enterprises ground their AI agents in a knowledge graph

---

## The Stakes

Enterprises are putting GenAI agents into workflows where a wrong answer has real cost:

- **Investment research**: recommendations driven by incomplete signals
- **Compliance**: obligations missed or misread
- **Risk reporting**: exposure understated to auditors and regulators

In regulated industries, an answer that cannot be explained is an answer that cannot be used.

---

## The Problem Vectors Do Not Solve

Vector search finds text that is **similar**, but it cannot **traverse relationships**.

In financial data, that gap hides exactly what matters:

- **Shared executives** across companies never surface from chunk similarity
- **Cross-portfolio risk exposure** spans filings vectors treat as unrelated
- **Parent company disclosures** stay disconnected from their subsidiaries

Similar text is not the same as connected fact.

---

## The Shift to GraphRAG

GraphRAG grounds the agent in a knowledge graph:

- Retrieval returns **connected, verifiable facts**, not pattern-matched chunks
- Graph traversal adds entity context on top of vector similarity
- Every answer **traces back** through the relationships that produced it

The LLM answers from evidence the graph can defend, not from statistical guesses.

---

## Context Graphs and Decision Governance

Multi-agent systems make decisions across many steps with no record of why.

**Context graphs** close that gap:

- Neo4j captures agent decision traces as **nodes and relationships**
- Each action records its inputs, tool calls, outputs, and links to prior steps
- Result: **audit trails and explainability** for regulated industries

Governance is not bolted on afterward. It lives in the same graph as the data.

---

## The Proof: Hero Questions

Questions no vector store can answer alone:

- "Which risk factors expose **BlackRock's portfolio** across multiple companies?"
- "What risks does **NVIDIA** face, and which **asset managers** are exposed?"

Both require following relationships across companies, portfolios, and risk factors. That is graph traversal, not text similarity.

---

## What We Are Building Today

By the end of the workshop, you will have built and deployed exactly this:

- A **GraphRAG agent** over real SEC 10-K filing data
- Deployed to **Amazon Bedrock AgentCore** for production hosting
- Extended with persistent memory via **neo4j-agent-memory**
- Reachable from any framework through the **Neo4j MCP Server**

The demo you are about to see is the artifact you will build.

---

## Neo4j + AWS Partnership

- **Joint partnership** focused on grounding enterprise AI agents to reduce hallucinations
- **Neo4j Aura** is available on AWS Marketplace, deployable into your own account
- Key integrations this workshop uses: Amazon Bedrock (Claude and Titan embeddings), Bedrock AgentCore, and the Neo4j MCP Server
- A shared **2026 roadmap** continues to deepen the Bedrock and AgentCore integration

<!--
Instructor: replace the roadmap line with the current, approved Neo4j + AWS
roadmap talking points for your event. Keep any forward-looking product
claims to what has been publicly announced.
-->

---

## Opening Demo

See the finished build answer the hero questions live.

<!--
Instructor run instructions:

Run the two hero questions live against the pre-deployed Lab 4 GraphRAG agent (deployed to AgentCore Runtime before the event, against the instructor's own Aura instance loaded with the seed dataset):

1. "Which risk factors expose BlackRock's portfolio across multiple companies?"
2. "What risks does NVIDIA face, and which asset managers are exposed?"

Show the agent's tool calls so attendees see the graph traversal happening, not just the final answer.

Optional: run one question against vector-only retrieval, then against GraphRAG, and compare the two answers side by side.

Keep the endpoint live all day so attendees can hit the REST API during breaks. Point back to this demo from each lab: Lab 3 builds the retriever behind these answers, Lab 4 deploys the same agent.
-->
