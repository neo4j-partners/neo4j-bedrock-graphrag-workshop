#!/usr/bin/env python3
"""
Strands GraphRAG Agent - AgentCore Runtime Deployment

The same agent built and tested in 01_strands_graphrag_agent.ipynb, wrapped in a
BedrockAgentCoreApp handler for deployment to Amazon Bedrock AgentCore Runtime.

The reusable retrievers and tools come from graphrag_agent.py, which
02_deploy_to_agentcore.ipynb copies into this directory at deploy time (this
directory is the only thing bundled by direct_code_deploy). Two neo4j-graphrag
retrievers are exposed as Strands @tool functions:
- semantic_search: pure vector search over SEC 10-K filing chunks
- graph_enriched_search: vector search plus graph traversal to companies,
  products, and risk factors

The model decides which tool fits each question.
"""

import logging

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

from graphrag_agent import SYSTEM_PROMPT, build_retrievers, make_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

# --- Filled in from CONFIG.txt by 02_deploy_to_agentcore.ipynb ---
NEO4J_URI = "<NEO4J_URI>"
NEO4J_USERNAME = "<NEO4J_USERNAME>"
NEO4J_PASSWORD = "<NEO4J_PASSWORD>"
MODEL_ID = "<MODEL_ID>"
REGION = "<REGION>"

# Module-level initialization: run once and reused across invocations while the
# microVM stays warm. The driver, embedder, retrievers, and tools are expensive
# to build, so they live here rather than inside the request handler. The
# runtime has no CONFIG.txt, so config comes from the deploy-templated constants
# above (not build_graphrag_agent).
_driver, vector_retriever, vector_cypher_retriever = build_retrievers(
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, REGION
)
TOOLS = make_tools(vector_retriever, vector_cypher_retriever)

logger.info("Neo4j driver, embedder, retrievers, and tools initialized")


@app.entrypoint
async def invoke(payload: dict = None):
    """AgentCore Runtime handler."""
    if payload is None:
        payload = {}

    prompt = (
        payload.get("prompt")
        or payload.get("message")
        or payload.get("query")
        or payload.get("input")
    )

    if not prompt:
        yield {
            "type": "error",
            "error": "No prompt provided. Include 'prompt' in your request.",
        }
        return

    logger.info(f"Query: {prompt[:100]}...")

    try:
        model = BedrockModel(
            model_id=MODEL_ID,
            region_name=REGION,
            temperature=0,
        )
        # Build a fresh agent per request so conversation state does not leak
        # between invocations sharing a warm microVM.
        agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=TOOLS,
        )

        response = agent(prompt)
        response_text = str(response)

        yield {"type": "chunk", "data": response_text}
        yield {"type": "complete"}

        logger.info("Request completed successfully")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        yield {"type": "error", "error": f"Error processing request: {str(e)}"}


if __name__ == "__main__":
    app.run(port=8080)
