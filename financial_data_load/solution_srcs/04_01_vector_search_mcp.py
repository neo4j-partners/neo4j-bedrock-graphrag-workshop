"""
Vector Search via MCP

This solution demonstrates semantic vector search through the Neo4j
MCP server using a @tool wrapper that encapsulates embedding generation
and Cypher execution, keeping embeddings off the LLM context window.

Run with: uv run python main.py solutions <N>
"""

import asyncio
import json
import os
import sys

import nest_asyncio
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel

nest_asyncio.apply()

# Add project root to sys.path so lib imports work
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from lib.mcp_utils import MCPConnection  # noqa: E402
from solution_srcs.config import get_embedding  # noqa: E402

# ---------------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------------

# Load .env from financial_data_load directory (same as config.py)
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(_env_path)

MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
REGION = os.getenv("AWS_REGION", os.getenv("REGION", "us-east-1"))


# ---------------------------------------------------------------------------
# 2. System Prompt
# ---------------------------------------------------------------------------

VECTOR_SEARCH_PROMPT = """You are a retrieval assistant that performs semantic vector search against a Neo4j database containing SEC 10-K filing data.

You have a vector_search_tool that finds semantically similar text chunks. Call it with a natural language query and an optional top_k parameter.

FORMAT:
For each result, show:
1. The similarity score (higher = more similar)
2. A preview of the chunk text (first 200 characters)
"""


# ---------------------------------------------------------------------------
# 3. Main
# ---------------------------------------------------------------------------


async def run():
    """Run vector search demo."""
    print(f"Model:     {MODEL_ID}")
    print(f"Region:    {REGION}")

    # Test the shared embedding function
    test_embedding = get_embedding("What are Apple's main products?")
    print(f"\nEmbedding dimensions: {len(test_embedding)}")
    print(f"First 5 values: {test_embedding[:5]}")

    # Initialize model and MCP connection
    bedrock_model = BedrockModel(
        model_id=MODEL_ID,
        region_name=REGION,
        temperature=0,
    )

    mcp_conn = await MCPConnection.create(_env_path)

    print(f"\nModel: {MODEL_ID}")
    print("MCP connection established.\n")

    # -- Vector search tool (embedding stays on the data plane) --

    @tool
    async def vector_search_tool(query: str, top_k: int = 5) -> str:
        """Search for semantically similar chunks using vector embeddings.
        Use this for semantic queries about SEC 10-K filing data."""
        embedding = get_embedding(query)
        top_k = int(top_k)

        return await mcp_conn.execute_query(f"""
            CALL db.index.vector.queryNodes('chunkEmbeddings', {top_k}, {json.dumps(embedding)})
            YIELD node, score
            RETURN node.text AS text, score
            ORDER BY score DESC
        """)

    agent = Agent(
        model=bedrock_model,
        system_prompt=VECTOR_SEARCH_PROMPT,
        tools=[vector_search_tool],
    )

    async def vector_search(query: str, top_k: int = 5):
        """Run vector search through the agent."""
        print(f'Query: "{query}"')
        print(f"Top K: {top_k}")
        print("-" * 60)

        response = await agent.invoke_async(
            f"Search for: {query}\nUse top_k={top_k}."
        )
        print(f"\n{response}")
        return response

    # --- Run vector searches ---

    # Search for product-related information
    print("=" * 60)
    await vector_search("What are Apple's main products?", top_k=5)

    # Search for risk factor information
    print("\n" + "=" * 60)
    await vector_search(
        "What are the key risk factors mentioned in SEC filings?",
        top_k=5,
    )

    # Compare top_k values — fewer results for a focused search
    print("\n" + "=" * 60)
    await vector_search(
        "What financial metrics indicate company performance?",
        top_k=3,
    )

    await mcp_conn.close()


def main():
    """Entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
