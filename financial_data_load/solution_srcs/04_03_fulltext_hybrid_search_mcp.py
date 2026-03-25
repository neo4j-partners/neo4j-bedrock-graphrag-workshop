"""
Fulltext and Hybrid Search via MCP

This solution demonstrates fulltext keyword search and agent-driven hybrid
search with custom @tool wrappers through the Neo4j MCP server using
the Strands Agents SDK.

Run with: uv run python main.py solutions <N>
"""

import os
import sys

from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

# Add financial_data_load to sys.path so lib imports work
FINANCIAL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, FINANCIAL_DATA_DIR)

from lib.data_utils import get_embedding  # noqa: E402


# =============================================================================
# Fulltext Search Agent
# =============================================================================

FULLTEXT_PROMPT = """You are a retrieval assistant that performs fulltext keyword search against a Neo4j database containing SEC 10-K filing data.

You have MCP tools to execute Cypher queries. Use the fulltext index on Chunk text:

CALL db.index.fulltext.queryNodes('search_chunks', $search_term)
YIELD node, score
RETURN node.text AS text, score
ORDER BY score DESC
LIMIT $limit

SEARCH OPERATORS (use these in the search term string):
- Fuzzy: append ~ to handle typos (e.g., 'revnue~' matches 'revenue')
- Wildcard: append * for prefix matching (e.g., 'risk*' matches 'risks', 'risky')
- Boolean AND: both terms required (e.g., 'revenue AND growth')
- Boolean NOT: exclude terms (e.g., 'revenue NOT decline')

For each result, show the Lucene relevance score and a preview of the chunk text."""

# =============================================================================
# Fulltext + Graph Traversal Agent
# =============================================================================

FULLTEXT_GRAPH_PROMPT = """You are a retrieval assistant that performs fulltext search with graph context against a Neo4j database containing SEC 10-K filing data.

When given a search term, use this Cypher to find keyword matches WITH entity context:

CALL db.index.fulltext.queryNodes('search_chunks', $search_term)
YIELD node, score
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (doc)<-[:FILED]-(company:Company)
WITH node, doc, score,
     collect(DISTINCT company.name) AS companies
OPTIONAL MATCH (product:Product)-[:FROM_CHUNK]->(node)
WITH node, doc, score, companies,
     collect(DISTINCT product.name) AS products
RETURN node.text AS text, score, doc.name AS document, companies, products
ORDER BY score DESC
LIMIT $limit

For each result, show the score, document name, matched text, and any connected companies or products."""

# =============================================================================
# Hybrid Agent Prompt
# =============================================================================

HYBRID_PROMPT = """You are a financial analysis assistant that combines vector (semantic) and fulltext (keyword) search to answer questions about SEC 10-K filings.

You have two search tools:
1. vector_search: Finds semantically similar content (good for conceptual questions)
2. fulltext_search_tool: Finds exact keyword matches (good for specific names, terms, tickers)

HYBRID SEARCH STRATEGY:
For comprehensive results, run BOTH search tools with the same query, then synthesize an answer from the combined results. This gives you the benefits of both semantic understanding and keyword precision.

When the query contains specific names or terms (like "Apple", "AAPL"), fulltext search may find more precise matches. When the query is conceptual ("supply chain risks"), vector search captures semantic meaning.

For the best results, always run both searches and compare what each found."""


# =============================================================================
# Main
# =============================================================================

def main():
    # -------------------------------------------------------------------------
    # 1. Configuration and Setup
    # -------------------------------------------------------------------------
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path)
    MODEL_ID = os.getenv('MODEL_ID', 'us.anthropic.claude-sonnet-4-6')
    REGION = os.getenv('AWS_REGION', os.getenv('REGION', 'us-east-1'))
    MCP_GATEWAY_URL = os.getenv('MCP_GATEWAY_URL')
    MCP_ACCESS_TOKEN = os.getenv('MCP_ACCESS_TOKEN')

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

    # Test embedding function
    test_emb = get_embedding('test')
    print(f'Model:     {MODEL_ID}')
    print(f'Embedding: {len(test_emb)} dimensions')
    print('Setup complete!')

    with mcp_client:
        # Discover tools once for the entire session
        mcp_tools = mcp_client.list_tools_sync()
        tool_names = [t.tool_name for t in mcp_tools]
        print(f"MCP tools discovered: {tool_names}")

        cypher_tool = next(
            (n for n in tool_names if "read-cypher" in n),
            next((n for n in tool_names if "execute-query" in n), None),
        )
        assert cypher_tool, f"No Cypher query tool found among: {tool_names}"

        # ---------------------------------------------------------------------
        # 2. Basic Fulltext Search (agent uses raw MCP tools)
        # ---------------------------------------------------------------------
        def fulltext_search(term: str, limit: int = 5):
            """Run a fulltext keyword search through the MCP agent."""
            print(f'Search term: "{term}"')
            print('-' * 60)

            agent = Agent(
                model=bedrock_model,
                system_prompt=FULLTEXT_PROMPT,
                tools=mcp_tools,
            )
            response = agent(f"Search for chunks containing '{term}'. Use limit={limit}.")
            print(response)
            return response

        fulltext_search('revenue')

        # ---------------------------------------------------------------------
        # 3. Search Operators
        # ---------------------------------------------------------------------
        # Fuzzy search — handles typos
        fulltext_search('revnue~', limit=3)

        # Wildcard search — prefix matching
        fulltext_search('risk*', limit=3)

        # Boolean AND — both terms must appear
        fulltext_search('revenue AND growth', limit=3)

        # ---------------------------------------------------------------------
        # 4. Fulltext + Graph Traversal
        # ---------------------------------------------------------------------
        def fulltext_graph_search(term: str, limit: int = 5):
            """Run fulltext search with graph traversal."""
            print(f'Search term: "{term}" (with graph context)')
            print('-' * 60)

            agent = Agent(
                model=bedrock_model,
                system_prompt=FULLTEXT_GRAPH_PROMPT,
                tools=mcp_tools,
            )
            response = agent(f"Search for chunks containing '{term}' with graph context. Use limit={limit}.")
            print(response)
            return response

        fulltext_graph_search('iPhone')

        # ---------------------------------------------------------------------
        # 5. Agent-Driven Hybrid Search with @tool Wrappers
        # ---------------------------------------------------------------------
        @tool
        def vector_search(query: str, top_k: int = 5) -> str:
            """Search for semantically similar chunks using vector embeddings.
            Use this for conceptual or semantic queries where exact words may differ."""
            embedding = get_embedding(query)
            top_k = int(top_k)

            cypher = f"""
                CALL db.index.vector.queryNodes('chunkEmbeddings', {top_k}, $query_vector)
                YIELD node, score
                MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
                WITH node {{.*, embedding: null}} AS node, score, doc
                RETURN node.text AS text, score, doc.name AS document
                ORDER BY score DESC
            """
            result = mcp_client.call_tool_sync(
                tool_use_id="vector-search",
                name=cypher_tool,
                arguments={"query": cypher, "params": {"query_vector": embedding}},
            )
            return result["content"][0]["text"]

        @tool
        def fulltext_search_tool(term: str, limit: int = 5) -> str:
            """Search for chunks containing specific keywords.
            Use this for exact terms, company names, tickers, or partial matches.
            Supports operators: fuzzy (term~), wildcard (term*), AND, NOT."""
            limit = int(limit)

            cypher = f"""
                CALL db.index.fulltext.queryNodes('search_chunks', $search_term)
                YIELD node, score
                MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
                RETURN node.text AS text, score, doc.name AS document
                ORDER BY score DESC
                LIMIT {limit}
            """
            result = mcp_client.call_tool_sync(
                tool_use_id="fulltext-search",
                name=cypher_tool,
                arguments={"query": cypher, "params": {"search_term": term}},
            )
            return result["content"][0]["text"]

        print('Custom tools created:')
        print('  - vector_search')
        print('  - fulltext_search_tool')

        # Agent gets ONLY the custom tools — never sees raw embeddings or MCP tools
        hybrid_agent = Agent(
            model=bedrock_model,
            system_prompt=HYBRID_PROMPT,
            tools=[vector_search, fulltext_search_tool],
        )
        print('Hybrid agent ready!')

        # ---------------------------------------------------------------------
        # 6. Hybrid Search
        # ---------------------------------------------------------------------
        def hybrid_search(query: str):
            """Run hybrid search using both vector and fulltext tools."""
            print(f'Question: "{query}"')
            print('=' * 60)

            response = hybrid_agent(
                f"Answer this question using BOTH vector search and fulltext search: {query}"
            )
            print(f'\n{response}')
            return response

        hybrid_search("What are Apple's key risk factors?")

        hybrid_search('Which companies face cybersecurity-related risks?')

        hybrid_search('What products does Apple offer?')


if __name__ == '__main__':
    main()
