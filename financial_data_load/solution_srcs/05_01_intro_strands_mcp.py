"""
Introduction to Strands Agents with MCP

Demonstrates a Strands Agent connected to a Neo4j MCP Server. The agent
discovers tools at startup, inspects the graph schema, and runs simple
queries — a pure MCP introduction with no custom @tool wrappers.

Run with: uv run python main.py solutions <N>
"""

import os

from botocore.config import Config as BotocoreConfig
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

# ---------------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------------

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(_env_path)

MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
REGION = os.getenv("REGION", os.getenv("AWS_REGION", "us-east-1"))
MCP_GATEWAY_URL = os.getenv("MCP_GATEWAY_URL")
MCP_ACCESS_TOKEN = os.getenv("MCP_ACCESS_TOKEN")


# ---------------------------------------------------------------------------
# 2. System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a helpful assistant with access to a Neo4j knowledge graph containing SEC 10-K financial filing data.

Rules:
1. Always retrieve the database schema before writing any Cypher query.
2. Only use read-only Cypher (MATCH, RETURN, WITH, WHERE, ORDER BY, LIMIT).
3. Keep results concise — limit to 10 rows unless asked otherwise.
"""


# ---------------------------------------------------------------------------
# 3. Main
# ---------------------------------------------------------------------------


def main():
    """Run MCP intro demo."""
    print(f"Model:     {MODEL_ID}")
    print(f"Region:    {REGION}")

    bedrock_model = BedrockModel(
        model_id=MODEL_ID,
        region_name=REGION,
        temperature=0,
        boto_client_config=BotocoreConfig(read_timeout=300),
    )

    mcp_client = MCPClient(lambda: streamablehttp_client(
        url=MCP_GATEWAY_URL,
        headers={"Authorization": f"Bearer {MCP_ACCESS_TOKEN}"},
    ))

    with mcp_client:
        mcp_tools = mcp_client.list_tools_sync()
        tool_names = [t.tool_name for t in mcp_tools]
        print(f"MCP tools discovered: {tool_names}")
        print(f"Model: {MODEL_ID}\n")

        agent = Agent(
            model=bedrock_model,
            system_prompt=SYSTEM_PROMPT,
            tools=mcp_tools,
        )

        def query(question: str):
            """Ask the agent a question about the knowledge graph."""
            print(f'Question: "{question}"')
            print("-" * 60)
            response = agent(question)
            print(f"\n{response}")
            return response

        # --- Run queries ---

        print("=" * 60)
        query(
            "What is the database schema? Give me a brief summary of "
            "the node labels, relationship types, and key properties."
        )

        print("\n" + "=" * 60)
        query("How many companies are in the database?")


if __name__ == "__main__":
    main()
