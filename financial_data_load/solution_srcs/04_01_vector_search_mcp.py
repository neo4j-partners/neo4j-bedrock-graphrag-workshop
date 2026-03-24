"""
Vector Search via MCP

This solution demonstrates semantic vector search through the Neo4j
MCP server using Bedrock Nova embeddings and the Strands Agents SDK.

Run with: uv run python main.py solutions <N>
"""

import json
import os

import boto3
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

# ---------------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------------

# Load configuration from CONFIG.txt at project root
_config_path = os.path.join(os.path.dirname(__file__), "..", "..", "CONFIG.txt")
load_dotenv(_config_path)

MODEL_ID = os.getenv("MODEL_ID")
REGION = os.getenv("REGION", "us-east-1")
MCP_GATEWAY_URL = os.getenv("MCP_GATEWAY_URL")
MCP_ACCESS_TOKEN = os.getenv("MCP_ACCESS_TOKEN")

# ---------------------------------------------------------------------------
# 2. Embedding Helper
# ---------------------------------------------------------------------------

NOVA_MODEL_ID = "amazon.nova-2-multimodal-embeddings-v1:0"
EMBEDDING_DIMENSIONS = 1024

bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)


def get_embedding(text: str) -> list[float]:
    """Generate an embedding vector for the given text using Bedrock Nova."""
    request_body = {
        "taskType": "SINGLE_EMBEDDING",
        "singleEmbeddingParams": {
            "embeddingPurpose": "GENERIC_INDEX",
            "embeddingDimension": EMBEDDING_DIMENSIONS,
            "text": {
                "truncationMode": "END",
                "value": text,
            },
        },
    }
    response = bedrock_runtime.invoke_model(
        modelId=NOVA_MODEL_ID,
        body=json.dumps(request_body),
    )
    result = json.loads(response["body"].read())
    return result["embeddings"][0]["embedding"]


# ---------------------------------------------------------------------------
# 3. System Prompt
# ---------------------------------------------------------------------------

VECTOR_SEARCH_PROMPT = """You are a retrieval assistant that performs semantic vector search against a Neo4j database containing SEC 10-K filing data.

You have access to MCP tools that let you execute Cypher queries against the database.

VECTOR SEARCH INSTRUCTIONS:
When given a query embedding (a list of floats), use this Cypher pattern to find semantically similar text chunks:

CALL db.index.vector.queryNodes('chunkEmbeddings', $top_k, $embedding)
YIELD node, score
RETURN node.text AS text, score
ORDER BY score DESC

- The vector index is named 'chunkEmbeddings' and is on Chunk nodes
- The embedding will be provided in the user's message as a JSON array
- Use the exact embedding provided — do not modify it
- Return the chunk text and similarity score
- Always ORDER BY score DESC

FORMAT:
For each result, show:
1. The similarity score (higher = more similar)
2. A preview of the chunk text (first 200 characters)
"""


# ---------------------------------------------------------------------------
# 4. Vector Search Helper
# ---------------------------------------------------------------------------

bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    region_name=REGION,
    temperature=0,
)

mcp_client = MCPClient(
    lambda: streamablehttp_client(
        url=MCP_GATEWAY_URL,
        headers={"Authorization": f"Bearer {MCP_ACCESS_TOKEN}"},
    )
)


def vector_search(query: str, top_k: int = 5):
    """Embed a query and run vector search through the MCP agent."""
    print(f'Query: "{query}"')
    print(f"Top K: {top_k}")
    print("-" * 60)

    # Generate embedding for the query
    embedding = get_embedding(query)

    # Build the message with the embedding for the agent
    message = (
        f"Run a vector search for the following query. Use top_k={top_k}.\n\n"
        f"Query: {query}\n\n"
        f"Embedding (use this exact array in the Cypher query):\n{json.dumps(embedding)}"
    )

    with mcp_client:
        tools = mcp_client.list_tools_sync()
        print(f"  MCP tools: {[t.tool_name for t in tools]}")

        agent = Agent(
            model=bedrock_model,
            system_prompt=VECTOR_SEARCH_PROMPT,
            tools=tools,
        )

        response = agent(message)
        print(f"\n{response}")
        return response


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------


def main():
    """Run vector search demo."""
    print(f"Model:     {MODEL_ID}")
    print(f"Region:    {REGION}")
    print(
        f"Gateway:   {MCP_GATEWAY_URL[:50]}..."
        if MCP_GATEWAY_URL and len(MCP_GATEWAY_URL) > 50
        else f"Gateway:   {MCP_GATEWAY_URL}"
    )

    # Validate MCP config
    assert MCP_GATEWAY_URL and MCP_GATEWAY_URL != "your-gateway-url-here", \
        "MCP_GATEWAY_URL not configured in CONFIG.txt"
    assert MCP_ACCESS_TOKEN and MCP_ACCESS_TOKEN != "your-access-token-here", \
        "MCP_ACCESS_TOKEN not configured in CONFIG.txt"

    print("\nConfiguration loaded!")

    # Test the embedding function
    test_embedding = get_embedding("What are Apple's main products?")
    print(f"\nEmbedding dimensions: {len(test_embedding)}")
    print(f"First 5 values: {test_embedding[:5]}")

    print(f"\nModel: {MODEL_ID}")
    print("MCP client created.\n")

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
