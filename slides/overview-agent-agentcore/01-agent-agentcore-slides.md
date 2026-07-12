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

# GraphRAG Agent and AgentCore

Building the Strands GraphRAG agent and deploying it to Amazon Bedrock AgentCore

---

## Why Agents?

Foundation models have gaps:
- **No tool access** — cannot query databases or call APIs on their own
- **No private data** — trained on public data, not your knowledge graph
- **Static knowledge** — training data has a cutoff date

**Agents** bridge these gaps by giving LLMs the ability to **reason about what to do** and **act by calling tools**. The model decides which tool to call, interprets the result, and decides what to do next.

---

## The ReAct Pattern

**ReAct** = Reason + Act. Every agent in this workshop follows this loop:

1. **Reason**: The LLM examines the question and current state
2. **Act**: The LLM issues a tool call (or produces a final answer)
3. **Observe**: The tool executes and the result is appended
4. **Repeat**: The LLM decides whether to call another tool or finish

The number of cycles depends on the question's complexity, not a predetermined plan.

---

## ReAct Example: SEC Data

**User**: "What risks does NVIDIA face and which asset managers are exposed?"

**Cycle 1** — Reason: need NVIDIA's risk factors → Act: query graph → Observe: Supply Chain Disruption, Cybersecurity Threats

**Cycle 2** — Reason: need asset managers holding NVIDIA → Act: query graph → Observe: BlackRock, Vanguard, State Street

**Synthesize**: "NVIDIA faces supply chain and cybersecurity risks. BlackRock, Vanguard, and State Street hold positions, making their portfolios exposed."

---

## Strands Agents SDK

AWS-native agent framework. **Model-driven**: the model decides what to do, not developer-defined control flow.

```python
from strands import Agent
from strands.models import BedrockModel
from strands.tools import tool

bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    region_name=REGION,
    temperature=0,
)

agent = Agent(
    model=bedrock_model,
    system_prompt="You are a financial research assistant.",
    tools=[graphrag_search],
)
```

---

## Tools with the @tool Decorator

A tool is a Python function the LLM can call. Here the tool wraps a `VectorCypherRetriever` so the agent retrieves graph-enriched context:

```python
@tool
def graphrag_search(query: str, top_k: int = 5) -> str:
    """Search SEC 10-K filings with graph-enriched context.

    Use for questions about specific companies, products, or
    risk factors. Graph traversal adds connected entities to
    each retrieved chunk.
    """
    result = vector_cypher_retriever.search(query_text=query, top_k=top_k)
    chunks = []
    for item in result.items:
        meta = item.metadata or {}
        header = (f"Company: {meta.get('company')} | "
                  f"Products: {meta.get('products', [])} | "
                  f"Risks: {meta.get('risks', [])}")
        chunks.append(f"{header}\n{item.content}")
    return "\n\n".join(chunks)
```

The docstring becomes the tool description. The LLM reads it, decides when to call the tool, and interprets the chunks plus connected entities it returns.

---

## Why a Specialized Graph Agent

An agent handling both SQL and Cypher in one prompt must hold:
- Two query languages
- Two data models
- Two sets of conventions

Mixing dilutes focus. The graph agent in this workshop handles **only graph retrieval**: it calls graph-aware tools and reasons over the connected entities they return.

In production, a **supervisor agent** routes questions to specialists: relationship traversals go to the graph agent, aggregations go to a SQL agent.

---

## AgentCore Deployment (Lab 4)

Lab 4 deploys the **GraphRAG agent you just built** to **AgentCore Runtime**, the same artifact from the opening demo:

1. Agent code (`agent.py`) plus dependencies (`pyproject.toml`) in `agentcore_deploy/`
2. Use the **`bedrock-agentcore-starter-toolkit`** to configure and package the agent
3. Run the toolkit's deploy step: it uploads to S3 and provisions an isolated microVM
4. Invoke the deployed agent over a **REST endpoint**, via the `agentcore` CLI or `boto3`

Each session runs in an **isolated microVM** with dedicated CPU, memory, and filesystem, terminated and sanitized after completion. No infrastructure to manage, and the endpoint scales on demand.

---

## Summary

- **ReAct pattern**: reason, act, observe, repeat, the foundation for the GraphRAG agent
- **Strands SDK**: model-driven, AWS-native, tools defined with the `@tool` decorator
- **GraphRAG tool**: wraps the `VectorCypherRetriever` so the agent answers from chunks plus connected entities
- **Specialized graph agent**: one focused job, ready to slot behind a supervisor in production
- **AgentCore Runtime**: deploy your own agent with the `bedrock-agentcore-starter-toolkit` and invoke it over REST

You build the agent, then deploy the exact artifact from the opening demo.
