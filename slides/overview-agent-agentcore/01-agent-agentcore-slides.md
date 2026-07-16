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
- **No tool access**: cannot query databases or call APIs on their own
- **No private data**: trained on public data, not your knowledge graph
- **Static knowledge**: training data has a cutoff date

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

**Cycle 1.** Reason: need NVIDIA's risk factors → Act: query graph → Observe: Supply Chain Disruption, Cybersecurity Threats

**Cycle 2.** Reason: need asset managers holding NVIDIA → Act: query graph → Observe: BlackRock, Vanguard, State Street

**Synthesize**: "NVIDIA faces supply chain and cybersecurity risks. BlackRock, Vanguard, and State Street hold positions, making their portfolios exposed."

---

## Strands Agents SDK

- **Open-source SDK from AWS** (Apache 2.0), Python and TypeScript
- **Model-driven**: the model plans and calls tools; you write no control flow
- **Model-agnostic**: Bedrock (default), Anthropic, OpenAI, Google, Ollama
- **Few primitives**: an `Agent`, a model provider, and `@tool` functions
- **Production-tested** inside Amazon: Q Developer, AWS Glue

<!--
Strands is AWS's open-source agent framework, licensed Apache 2.0 and
available in Python and TypeScript. Model-driven means the model does the
planning: it reads the tool docstrings, decides what to call, and sequences
the steps. You don't write routing logic. It's model-agnostic, so Bedrock is
the default but you can swap in Anthropic, OpenAI, Google, or Ollama without
touching your tools. And it isn't a toy: Amazon runs it in Q Developer and
AWS Glue. For this workshop we use it with Bedrock and just three primitives.
-->

---

## What's New in Strands 1.0

- **Multi-agent primitives**: Swarm, Graph, Workflow, Agents-as-Tools
- **Model-driven or deterministic**: a single agent lets the model plan; Graph and Workflow let you define control flow when you want it
- **A2A protocol**: agents interoperate across platforms and vendors
- **Durable sessions**: persist conversation state to file or Amazon S3
- **Native MCP client**: connect to MCP tool servers directly
- **Async streaming + lifecycle hooks**: stream events, intercept each step
- **OpenTelemetry tracing**: observability built in, no extra wiring

<!--
Strands hit 1.0 in mid-2025 and added the pieces you need past a single agent.

The four multi-agent primitives are different ways to coordinate more than one
agent:
- Swarm: a flat team of peer agents sharing context. Any agent can hand off
  control to another via a built-in handoff tool, and the order is emergent,
  not pre-planned. Good when you don't know the path up front.
- Graph: a deterministic workflow you define as nodes and directed edges, with
  optional conditions on each edge. Execution order is fixed and auditable.
  Good when you want a repeatable, testable flow.
- Workflow: orchestrates a set of tasks with dependencies. It resolves the
  order, runs independent tasks in parallel, and persists progress by id.
  Good for pipelines of dependent steps.
- Agents-as-Tools: the pattern we lean on here. Wrap a specialist agent inside
  the @tool decorator so an orchestrator agent calls it like any other tool.
  Control returns to the orchestrator after each delegation. This is how a
  supervisor routes to the graph agent versus a SQL agent.

A2A lets Strands agents talk to agents on other platforms over an open
protocol. Durable sessions persist conversation state to file or S3, so a warm
agent survives restarts. MCP is a first-class client, which is exactly what
Lab 6 uses. Async streaming, lifecycle hooks, and OpenTelemetry tracing round
out the production story. We use the single-agent core here, but the same SDK
scales to all of this.
-->

---

## Building the Agent

```python
from strands import Agent
from strands.models import BedrockModel

# The model: temperature=0 for deterministic, repeatable answers
bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    region_name=REGION,
    temperature=0,
)

# The agent: system_prompt sets its role,
# tools=[...] lists what the model is allowed to call
agent = Agent(
    model=bedrock_model,
    system_prompt="You are a financial research assistant.",
    tools=[semantic_search, graph_enriched_search],  # two tools
)
```

---

## Tools with the @tool Decorator

- **Tool**: a Python function the LLM can call
- **Docstring**: becomes the tool description the LLM reads to decide when to call it
- **Return value**: text the agent interprets, then reasons over

This agent exposes **two** tools, each wrapping a different retriever. The model reads both docstrings and chooses per question.

```python
@tool
def semantic_search(query: str, top_k: int = 5) -> str:
    """Search filing chunks by meaning. Use for broad or
    thematic questions where the text alone answers."""

@tool
def graph_enriched_search(query: str, top_k: int = 5) -> str:
    """Search chunks AND return connected entities. Use for
    questions about specific companies, products, or risks."""
```

---

## Two Retrieval Strategies, One Agent

The agent wraps **two** retrievers from Lab 3 as separate tools:

- **`semantic_search`** (plain vector search, `VectorRetriever`): returns chunks ranked by meaning. Best for broad or thematic questions where the text alone answers.
- **`graph_enriched_search`** (vector plus Cypher, `VectorCypherRetriever`): returns those chunks *and* the entities each one connects to (companies, products, risk factors). Best when the question names specific companies or relationships.

The system prompt describes both strategies. The model reasons about the question and calls the one that fits, so the choice is the model's, not hand-written routing logic.

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

Each session runs in an **isolated microVM** with dedicated CPU, memory, and filesystem. No infrastructure to manage, and the endpoint scales on demand.

---

![bg contain](agentcore-deployment.svg)

---

## The AgentCore Handler Contract

Deployment wraps the same agent code in two AgentCore primitives:

- **`app = BedrockAgentCoreApp()`**: the application object the runtime hosts
- **`@app.entrypoint`**: marks the one handler the runtime calls for every request

```python
app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload: dict = None):
    prompt = payload.get("prompt")
    agent = Agent(model=model, system_prompt=SYSTEM_PROMPT, tools=TOOLS)
    response = agent(prompt)
    yield {"type": "chunk", "data": str(response)}
    yield {"type": "complete"}
```

The handler pulls the `prompt` out of the request payload and **yields** result events the runtime streams back to the caller.

---

## Warm microVM: Build Once, Fresh Agent Per Request

The runtime keeps a microVM **warm** between requests, so the code splits work by lifetime:

- **Module level, once per microVM**: build the Neo4j driver, embedder, and both retrievers. These are expensive, so they are created when the module loads and reused across invocations while the microVM stays warm.
- **Per request, inside the handler**: build a **fresh `Agent`** each time. A new agent means no conversation state leaks between requests that happen to share the same warm microVM.

Expensive shared resources persist; per-conversation state does not.

---

## Summary

- **ReAct pattern**: reason, act, observe, repeat, the foundation for the GraphRAG agent
- **Strands SDK**: model-driven, AWS-native, tools defined with the `@tool` decorator
- **Two retrieval tools**: `semantic_search` (plain vector) and `graph_enriched_search` (vector plus Cypher); the model picks per question
- **Specialized graph agent**: one focused job, ready to slot behind a supervisor in production
- **AgentCore Runtime**: an app plus an `@app.entrypoint` handler; retrievers built once on a warm microVM, a fresh agent per request

You build the agent, then deploy the exact artifact from the opening demo.
