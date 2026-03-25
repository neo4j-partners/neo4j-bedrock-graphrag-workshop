"""
Vector Search via MCP

This solution demonstrates semantic vector search through the Neo4j
MCP server using a @tool wrapper that encapsulates embedding generation
and Cypher execution, keeping embeddings off the LLM context window.

Run with: uv run python main.py solutions <N>
"""

import os
import sys

from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

# Add financial_data_load to sys.path so local lib imports work
FINANCIAL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, FINANCIAL_DATA_DIR)

from lib.data_utils import get_embedding  # noqa: E402

# ---------------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------------

# Load .env from financial_data_load directory (same as config.py)
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(_env_path)

MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
REGION = os.getenv("AWS_REGION", os.getenv("REGION", "us-east-1"))
MCP_GATEWAY_URL = os.getenv("MCP_GATEWAY_URL")
MCP_ACCESS_TOKEN = os.getenv("MCP_ACCESS_TOKEN")


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


def main():
    """Run vector search demo."""
    print(f"Model:     {MODEL_ID}")
    print(f"Region:    {REGION}")

    # Test the shared embedding function
    test_embedding = get_embedding("What are Apple's main products?")
    print(f"\nEmbedding dimensions: {len(test_embedding)}")
    print(f"First 5 values: {test_embedding[:5]}")

    # Initialize model
    bedrock_model = BedrockModel(
        model_id=MODEL_ID,
        region_name=REGION,
        temperature=0,
    )

    mcp_client = MCPClient(lambda: streamablehttp_client(
        url=MCP_GATEWAY_URL,
        headers={"Authorization": f"Bearer {MCP_ACCESS_TOKEN}"},
    ))

    with mcp_client:
        # Discover the Cypher query tool
        mcp_tools = mcp_client.list_tools_sync()
        tool_names = [t.tool_name for t in mcp_tools]
        print(f"MCP tools discovered: {tool_names}")

        cypher_tool = next(
            (n for n in tool_names if "read-cypher" in n),
            next((n for n in tool_names if "execute-query" in n), None),
        )
        assert cypher_tool, f"No Cypher query tool found among: {tool_names}"
        print(f"\nModel: {MODEL_ID}")
        print(f"Cypher tool: {cypher_tool}\n")

        # -- Vector search tool (embedding stays on the data plane) --

        @tool
        def vector_search_tool(query: str, top_k: int = 5) -> str:
            """Search for semantically similar chunks using vector embeddings.
            Use this for semantic queries about SEC 10-K filing data."""
            embedding = get_embedding(query)
            top_k = int(top_k)

            cypher = f"""
                CALL db.index.vector.queryNodes('chunkEmbeddings', {top_k}, $query_vector)
                YIELD node, score
                WITH node {{.*, embedding: null}} AS node, score
                RETURN node.text AS text, score
                ORDER BY score DESC
            """
            result = mcp_client.call_tool_sync(
                tool_use_id="vector-search",
                name=cypher_tool,
                arguments={"query": cypher, "params": {"query_vector": embedding}},
            )
            return result["content"][0]["text"]

        agent = Agent(
            model=bedrock_model,
            system_prompt=VECTOR_SEARCH_PROMPT,
            tools=[vector_search_tool],
        )

        def vector_search(query: str, top_k: int = 5):
            """Run vector search through the agent."""
            print(f'Query: "{query}"')
            print(f"Top K: {top_k}")
            print("-" * 60)

            response = agent(f"Search for: {query}\nUse top_k={top_k}.")
            print(f"\n{response}")
            return response

        # --- Run vector searches ---

        # Search for product-related information
        print("=" * 60)
        vector_search("What are Apple's main products?", top_k=5)

        # Search for risk factor information
        print("\n" + "=" * 60)
        vector_search(
            "What are the key risk factors mentioned in SEC filings?",
            top_k=5,
        )

        # Compare top_k values — fewer results for a focused search
        print("\n" + "=" * 60)
        vector_search(
            "What financial metrics indicate company performance?",
            top_k=3,
        )


if __name__ == "__main__":
    main()
