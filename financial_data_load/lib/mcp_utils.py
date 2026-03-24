# ---------------------------------------------------------------------------
# COPIED from root lib/mcp_utils.py to simplify env loading.
# financial_data_load uses .env (not CONFIG.txt), so this local copy loads
# from the financial_data_load/.env instead of the project-root CONFIG.txt.
#
# If you change this file, update the root lib/mcp_utils.py as well.
# If you change the root lib/mcp_utils.py, update this file as well.
# ---------------------------------------------------------------------------

"""MCP connection and query utilities for Neo4j MCP server."""

import os
from datetime import timedelta

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class MCPConnection:
    """Manages a persistent MCP server connection for query execution.

    Wraps a raw MCP ClientSession over Streamable HTTP transport.
    Provides execute_query() for running Cypher directly through the
    MCP execute-query tool.

    Usage::

        mcp = await MCPConnection.create("../.env")
        result = await mcp.execute_query("MATCH (n) RETURN count(n)")
    """

    def __init__(self, gateway_url: str, access_token: str):
        self.gateway_url = gateway_url
        self.access_token = access_token
        self._transport_cm = None
        self._session_cm = None
        self._session = None

    @classmethod
    async def create(cls, config_path: str = "../.env") -> "MCPConnection":
        """Create and initialize an MCP connection from config file."""
        load_dotenv(config_path)
        gateway_url = os.getenv("MCP_GATEWAY_URL")
        access_token = os.getenv("MCP_ACCESS_TOKEN")
        assert gateway_url and gateway_url != "your-gateway-url-here", \
            "MCP_GATEWAY_URL not configured in .env"
        assert access_token and access_token != "your-access-token-here", \
            "MCP_ACCESS_TOKEN not configured in .env"
        conn = cls(gateway_url, access_token)
        await conn.connect()
        return conn

    async def connect(self):
        """Connect to MCP server and verify tools are available."""
        self._transport_cm = streamablehttp_client(
            url=self.gateway_url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=timedelta(seconds=30),
        )
        read_stream, write_stream, _ = await self._transport_cm.__aenter__()

        self._session_cm = ClientSession(read_stream, write_stream)
        self._session = await self._session_cm.__aenter__()
        await self._session.initialize()

        tools_result = await self._session.list_tools()
        tool_names = [t.name for t in tools_result.tools]
        print(f"MCP tools discovered: {tool_names}")

        # Discover the read-cypher tool name (may be prefixed by gateway)
        self._query_tool = next(
            (n for n in tool_names if "read-cypher" in n),
            next((n for n in tool_names if "execute-query" in n), None),
        )
        assert self._query_tool, (
            f"No query tool found among: {tool_names}. "
            "Expected a tool containing 'read-cypher' or 'execute-query'."
        )

    async def execute_query(self, cypher: str) -> str:
        """Execute a Cypher query via the MCP read-cypher tool."""
        result = await self._session.call_tool(self._query_tool, {"query": cypher})
        if result.content:
            return result.content[0].text
        return ""

    async def close(self):
        """Close the MCP connection."""
        if self._session_cm:
            await self._session_cm.__aexit__(None, None, None)
        if self._transport_cm:
            await self._transport_cm.__aexit__(None, None, None)
