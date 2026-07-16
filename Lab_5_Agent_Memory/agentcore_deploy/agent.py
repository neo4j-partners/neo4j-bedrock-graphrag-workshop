#!/usr/bin/env python3
"""
GraphRAG Agent with Short-Term Memory - AgentCore Runtime Deployment

The Lab 4 GraphRAG agent from 01_strands_graphrag_agent.ipynb, wrapped with the
short-term memory layer from Lab 5's 01_short_term_memory.ipynb, deployed to
Amazon Bedrock AgentCore Runtime.

The reusable retrievers and tools come from graphrag_agent.py, which
03_deploy_to_agentcore.ipynb copies into this directory at deploy time from
Lab 4's lib/ (this directory is the only thing bundled by direct_code_deploy).
Two neo4j-graphrag retrievers are exposed as Strands @tool functions:
- semantic_search: pure vector search over SEC 10-K filing chunks
- graph_enriched_search: vector search plus graph traversal to companies,
  products, and risk factors

The memory layer wraps each turn the same way the Lab 5 notebook does: pull
prior conversation with get_context before the turn, and write both sides with
add_message after. Continuity is keyed on the AgentCore session, so consecutive
questions in one playground session build on each other. It lives beside the
SEC 10-K graph in the same Neo4j instance.

Memory is constructed inline here rather than via lib/memory_utils.py, which
reads CONFIG.txt via data_utils at import time; the runtime has neither. See
lib/memory_utils.py for the canonical explanation of the two load-bearing
details reproduced below (the explicit Bedrock embedder and the pinned
dimensions / database).
"""

import asyncio
import logging

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from neo4j_agent_memory import (
    EmbeddingConfig,
    EmbeddingProvider,
    MemoryClient,
    MemorySettings,
)
from neo4j_agent_memory import Neo4jConfig as MemoryNeo4jConfig
from neo4j_agent_memory.config.settings import ExtractionConfig, ExtractorType
from neo4j_agent_memory.embeddings.bedrock import BedrockEmbedder
from pydantic import SecretStr
from strands import Agent
from strands.models import BedrockModel

from graphrag_agent import SYSTEM_PROMPT, build_retrievers, make_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# neo4j-agent-memory issues vector recall via a Cypher call Aura now flags as
# deprecated, logging one WARNING per call. Silence just that logger (see
# lib/memory_utils.py for the full rationale).
logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)

app = BedrockAgentCoreApp()

TITAN_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
TITAN_EMBEDDING_DIMENSIONS = 1024

# --- Filled in from CONFIG.txt by 03_deploy_to_agentcore.ipynb ---
NEO4J_URI = 'neo4j+s://1a2c98cc-staging.databases.neo4j.io'
NEO4J_USERNAME = 'neo4j'
NEO4J_PASSWORD = 'uezRxMa0PW2wPPzWwgaNLCr5j8u3yLqFU53PoTnUyEY'
NEO4J_DATABASE = 'neo4j'
MODEL_ID = 'us.anthropic.claude-sonnet-4-5-20250929-v1:0'
REGION = 'us-east-1'

# Session id used when neither the AgentCore request context nor the payload
# supplies one, so memory still has a stable key to write and read against.
DEFAULT_SESSION_ID = "agentcore-default"


def _build_memory_client() -> MemoryClient:
    """Construct an unconnected MemoryClient from the deploy-templated config.

    Mirrors lib/memory_utils.build_memory_client but reads the templated module
    constants instead of CONFIG.txt (the runtime has no CONFIG.txt). The Bedrock
    embedder is built explicitly and passed via ``embedder=`` because
    neo4j-agent-memory 0.5.0 builds no embedder for Bedrock and would otherwise
    silently write zero-length vectors.
    """
    embedding = EmbeddingConfig(
        provider=EmbeddingProvider.BEDROCK,
        model=TITAN_EMBEDDING_MODEL,
        dimensions=TITAN_EMBEDDING_DIMENSIONS,
        aws_region=REGION,
    )
    settings = MemorySettings(
        neo4j=MemoryNeo4jConfig(
            uri=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=SecretStr(NEO4J_PASSWORD),
            database=NEO4J_DATABASE or "neo4j",
        ),
        embedding=embedding,
        extraction=ExtractionConfig(extractor_type=ExtractorType.NONE),
    )
    embedder = BedrockEmbedder(model=TITAN_EMBEDDING_MODEL, region_name=REGION)
    return MemoryClient(settings, embedder=embedder)


# Module-level initialization: run once and reused across invocations while the
# microVM stays warm. The driver, embedder, retrievers, and tools are expensive
# to build, so they live here rather than inside the request handler.
_driver, vector_retriever, vector_cypher_retriever = build_retrievers(
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, REGION
)
TOOLS = make_tools(vector_retriever, vector_cypher_retriever)

# MemoryClient.connect() is a coroutine, so it cannot run at import time. Build
# the client now (sync, unconnected) and connect lazily on the first request,
# guarded so concurrent invocations on a warm microVM connect exactly once.
_memory = _build_memory_client()
_memory_connected = False
_memory_lock = asyncio.Lock()

logger.info("Neo4j driver, retrievers, tools, and memory client initialized")


async def _ensure_memory_connected() -> None:
    """Connect the memory client once, safely under concurrent invocations."""
    global _memory_connected
    if _memory_connected:
        return
    async with _memory_lock:
        if not _memory_connected:
            await _memory.connect()
            _memory_connected = True
            logger.info("Memory client connected")


def _resolve_session_id(payload: dict, context: object) -> str:
    """Pick the session id that keys short-term memory for this turn.

    Prefers the AgentCore request context (what the console playground varies
    per session, so consecutive questions share memory automatically), then an
    explicit ``session_id`` in the payload, then a stable default.
    """
    return (
        getattr(context, "session_id", None)
        or payload.get("session_id")
        or DEFAULT_SESSION_ID
    )


@app.entrypoint
async def invoke(payload: dict = None, context: object = None):
    """AgentCore Runtime handler with short-term memory."""
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

    session_id = _resolve_session_id(payload, context)
    logger.info(f"Session {session_id} | Query: {prompt[:100]}...")

    try:
        await _ensure_memory_connected()

        # Pull relevant prior conversation and prepend it, so the agent resolves
        # references across turns. Short-term only: continuity here is
        # conversational recall, not long-term knowledge or reasoning traces.
        context_text = await _memory.get_context(
            prompt,
            session_id=session_id,
            include_long_term=False,
            include_reasoning=False,
        )
        full_prompt = (
            f"{context_text}\n\nUser question: {prompt}" if context_text else prompt
        )

        model = BedrockModel(
            model_id=MODEL_ID,
            region_name=REGION,
            temperature=0,
        )
        # Build a fresh agent per request so conversation state does not leak
        # between invocations sharing a warm microVM. Continuity comes only from
        # the memory context injected above.
        agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=TOOLS,
        )

        response = agent(full_prompt)
        answer = str(response)

        # Persist both sides of the turn for the next question to build on.
        await _memory.short_term.add_message(session_id, "user", prompt)
        await _memory.short_term.add_message(session_id, "assistant", answer)

        yield {"type": "chunk", "data": answer}
        yield {"type": "complete"}

        logger.info("Request completed successfully")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        yield {"type": "error", "error": f"Error processing request: {str(e)}"}


if __name__ == "__main__":
    app.run(port=8080)
