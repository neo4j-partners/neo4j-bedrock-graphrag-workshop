# Lab 4 - Strands GraphRAG Agent

Wrap the retrievers you built in Lab 3 as agent tools and let a Strands agent decide which retrieval strategy to use for each question. Instead of the developer hardcoding vector search or graph-enriched search, the model reads each tool's description and picks the right one.

## What You'll Learn

- **Retrievers as Tools**: Wrap `VectorRetriever` and `VectorCypherRetriever` as Strands `@tool` functions
- **Agent-Driven Retrieval**: Build an agent with `BedrockModel` that chooses the retrieval strategy per question
- **Tool Selection Reasoning**: Inspect the ReAct loop to see which tool the agent called and why

## Prerequisites

Before starting this lab, make sure you have:

- Completed **Lab 3** (Semantic Search and GraphRAG), so you understand both retrievers
- `CONFIG.txt` at the project root filled in with `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `MODEL_ID`, and `REGION`
- A running environment (SageMaker Studio or GitHub Codespace)

> **Note:** This lab uses the same Neo4j Aura instance from the earlier labs. The knowledge graph — including document chunks, chunk embeddings, and the `chunkEmbeddings` vector index — must already be loaded. New to Strands agents? See the [Appendix - What Is an Agent?](../zz_Appendix_What_Is_An_Agent) for the basics.

## Notebooks

| Notebook | Title | What You Build |
|----------|-------|----------------|
| [01_strands_graphrag_agent.ipynb](01_strands_graphrag_agent.ipynb) | Strands GraphRAG Agent | An agent that wraps both retrievers as tools and selects the right one based on the question |

## Next Steps

After completing this lab, continue to [Lab 5 - Agent Memory with Neo4j](../Lab_5_Agent_Memory) to give the agent memory across conversation turns, or to [Lab 6 - Neo4j MCP Server](../Lab_6_MCP_Server) to serve the tools over MCP.
