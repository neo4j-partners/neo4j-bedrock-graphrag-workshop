# Lab 4 - Strands GraphRAG Agent

Wrap the retrievers you built in Lab 3 as agent tools and let a Strands agent decide which retrieval strategy to use for each question. Instead of the developer hardcoding vector search or graph-enriched search, the model reads each tool's description and picks the right one.

## What You'll Learn

- **Retrievers as Tools**: Wrap `VectorRetriever` and `VectorCypherRetriever` as Strands `@tool` functions
- **Agent-Driven Retrieval**: Build an agent with `BedrockModel` that chooses the retrieval strategy per question
- **Tool Selection Reasoning**: Inspect the ReAct loop to see which tool the agent called and why
- **Deploy to AgentCore**: Package the same agent and deploy it to Amazon Bedrock AgentCore Runtime with `direct_code_deploy`, then invoke it over REST

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
| [02_deploy_to_agentcore.ipynb](02_deploy_to_agentcore.ipynb) | Deploy to AgentCore Runtime | The same agent deployed to Bedrock AgentCore Runtime with `direct_code_deploy`, invoked over REST via the CLI and boto3 |

Notebook 02 reads your Neo4j credentials from `CONFIG.txt` and writes them into the deployment package (`agentcore_deploy/agent.py`), so you never retype the values from Lab 1. The repo copy of `agent.py` is a template with placeholder tokens; the notebook rewrites it in place with your real values at deploy time. Do not commit that filled copy back, and the generated `.bedrock_agentcore.yaml` is already git-ignored.

> **Note:** Notebook 02 is optional. In hosted OneBlink environments the SageMaker role may lack the IAM permissions to create the AgentCore runtime. If the deploy step fails, review the code to understand each step, then run the full deploy later in your own AWS account.

## Next Steps

After completing this lab, continue to [Lab 5 - Agent Memory with Neo4j](../Lab_5_Agent_Memory) to give the agent memory across conversation turns, or to [Lab 6 - Neo4j MCP Server](../Lab_6_MCP_Server) to serve the tools over MCP.
