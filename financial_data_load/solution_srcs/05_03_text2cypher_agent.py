"""
Text2Cypher Agent

Demonstrates the Text2Cypher pattern: a Strands Agent connected to a Neo4j
MCP Server that writes its own Cypher queries autonomously. The agent
discovers MCP tools at startup and uses them to explore and query the
knowledge graph — no custom @tool wrappers needed.

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

SYSTEM_PROMPT = """You are a Neo4j database assistant with access to a knowledge graph \
containing SEC 10-K financial filing data (companies, products, services, risk factors, \
financial metrics, executives, asset manager holdings).

Rules:
1. Always retrieve the database schema before writing Cypher queries.
2. Only use read-only Cypher (MATCH, RETURN, WITH, WHERE, ORDER BY, LIMIT).
3. Include LIMIT clauses to avoid excessive results.
4. Use COALESCE() or IS NOT NULL for properties that might be missing.
5. Format results clearly and cite actual data from query results.
6. Modern Cypher syntax:
   - Use elementId(n) instead of id(n) — id() is removed in Neo4j 5+
   - Use COUNT{ pattern } instead of size((pattern)) for counting pattern occurrences
   - Use EXISTS{ pattern } instead of exists((pattern)) for checking pattern existence
   - Always use $parameter syntax for dynamic values, never string concatenation
"""


# ---------------------------------------------------------------------------
# 3. Main
# ---------------------------------------------------------------------------


def main():
    """Run Text2Cypher agent demo."""
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
        query("What is the database schema?")

        print("\n" + "=" * 60)
        query("How many nodes are there by label?")

        print("\n" + "=" * 60)
        query("Show 5 sample records from the most populated node type.")


if __name__ == "__main__":
    main()
