"""
Graph-Enriched Search via MCP

This solution demonstrates vector search enriched with graph context
(documents, neighboring chunks, entities) through the Neo4j MCP server
using @tool wrappers that encapsulate embedding generation and Cypher
execution, keeping embeddings off the LLM context window.

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

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(_env_path)

MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-6")
REGION = os.getenv("AWS_REGION", os.getenv("REGION", "us-east-1"))
MCP_GATEWAY_URL = os.getenv("MCP_GATEWAY_URL")
MCP_ACCESS_TOKEN = os.getenv("MCP_ACCESS_TOKEN")


# ---------------------------------------------------------------------------
# 2. System Prompts
# ---------------------------------------------------------------------------

VECTOR_ONLY_PROMPT = """You are a retrieval assistant that performs semantic vector search against a Neo4j database containing SEC 10-K filing data.

You have a vector_search tool that finds semantically similar text chunks. Call it with a natural language query and an optional top_k parameter.

For each result, show the similarity score and a preview of the chunk text."""

GRAPH_ENRICHED_PROMPT = """You are a retrieval assistant that performs graph-enriched vector search against a Neo4j database containing SEC 10-K filing data.

You have a graph_enriched_search tool that finds similar chunks and enriches them with the source document name and neighboring chunk text for additional context.

For each result, show:
- Similarity score
- Source document name
- The matched chunk text
- Context from neighboring chunks (if available)"""

ENTITY_ENRICHED_PROMPT = """You are a retrieval assistant that performs entity-enriched vector search against a Neo4j database containing SEC 10-K filing data.

You have an entity_enriched_search tool that finds similar chunks and enriches them with connected companies, products, and risk factors from the knowledge graph.

For each result, show:
- Similarity score
- Source document name
- The matched chunk text
- Companies, products, and risk factors connected to the chunk"""

QA_PROMPT = """You are a financial analysis assistant with access to a Neo4j knowledge graph containing SEC 10-K filing data.

You have an entity_enriched_search tool that searches for relevant chunks enriched with companies, products, and risk factors.

After retrieving results, synthesize a clear answer based on the retrieved context.
Include the companies, products, and risk factors found. Cite the source documents."""


# ---------------------------------------------------------------------------
# 3. Main
# ---------------------------------------------------------------------------


def main():
    """Run graph-enriched search demo."""
    print(f"Model:     {MODEL_ID}")
    print(f"Region:    {REGION}")

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
        print(f"Cypher tool: {cypher_tool}")
        print("MCP connection established.\n")

        # -- Search tools (embeddings stay on the data plane) --

        @tool
        def vector_search(query: str, top_k: int = 3) -> str:
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

        @tool
        def graph_enriched_search(query: str, top_k: int = 3) -> str:
            """Search for similar chunks enriched with document and neighboring chunk context.
            Returns chunk text, source document, and text from adjacent chunks."""
            embedding = get_embedding(query)
            top_k = int(top_k)

            cypher = f"""
                CALL db.index.vector.queryNodes('chunkEmbeddings', {top_k}, $query_vector)
                YIELD node, score
                MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
                OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next:Chunk)
                OPTIONAL MATCH (prev:Chunk)-[:NEXT_CHUNK]->(node)
                WITH node, doc, score,
                     CASE WHEN prev IS NOT NULL THEN prev.text ELSE '' END AS prev_text,
                     CASE WHEN next IS NOT NULL THEN next.text ELSE '' END AS next_text
                WITH node {{.*, embedding: null}} AS node, doc, score, prev_text, next_text
                RETURN node.text AS text, score, doc.name AS document,
                       prev_text AS previous_chunk, next_text AS next_chunk
                ORDER BY score DESC
            """
            result = mcp_client.call_tool_sync(
                tool_use_id="graph-enriched-search",
                name=cypher_tool,
                arguments={"query": cypher, "params": {"query_vector": embedding}},
            )
            return result["content"][0]["text"]

        @tool
        def entity_enriched_search(query: str, top_k: int = 3) -> str:
            """Search for similar chunks enriched with companies, products, and risk factors.
            Returns chunk text, source document, and connected entities."""
            embedding = get_embedding(query)
            top_k = int(top_k)

            cypher = f"""
                CALL db.index.vector.queryNodes('chunkEmbeddings', {top_k}, $query_vector)
                YIELD node, score
                MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
                OPTIONAL MATCH (doc)<-[:FILED]-(company:Company)
                OPTIONAL MATCH (company)-[:FACES_RISK]->(risk:RiskFactor)
                WITH node, doc, score,
                     collect(DISTINCT company.name) AS companies,
                     collect(DISTINCT risk.name)[0..5] AS risks
                OPTIONAL MATCH (product:Product)-[:FROM_CHUNK]->(node)
                WITH node, doc, score, companies, risks,
                     collect(DISTINCT product.name)[0..5] AS products
                WITH node {{.*, embedding: null}} AS node, doc, score, companies, risks, products
                RETURN node.text AS text, score, doc.name AS document,
                       companies, risks, products
                ORDER BY score DESC
            """
            result = mcp_client.call_tool_sync(
                tool_use_id="entity-enriched-search",
                name=cypher_tool,
                arguments={"query": cypher, "params": {"query_vector": embedding}},
            )
            return result["content"][0]["text"]

        # -- Compare: run the same query through all three search levels --

        def compare_search(query: str, top_k: int = 3):
            """Run the same query through all three agents and display results."""
            print(f'Query: "{query}"')
            print("=" * 60)

            print("\n--- VECTOR-ONLY RESULTS ---\n")
            vector_agent = Agent(
                model=bedrock_model,
                system_prompt=VECTOR_ONLY_PROMPT,
                tools=[vector_search],
            )
            print(vector_agent(f"Search for: {query}\nUse top_k={top_k}."))

            print("\n\n--- GRAPH-ENRICHED RESULTS ---\n")
            graph_agent = Agent(
                model=bedrock_model,
                system_prompt=GRAPH_ENRICHED_PROMPT,
                tools=[graph_enriched_search],
            )
            print(graph_agent(f"Search for: {query}\nUse top_k={top_k}."))

            print("\n\n--- ENTITY-ENRICHED RESULTS ---\n")
            entity_agent = Agent(
                model=bedrock_model,
                system_prompt=ENTITY_ENRICHED_PROMPT,
                tools=[entity_enriched_search],
            )
            print(entity_agent(f"Search for: {query}\nUse top_k={top_k}."))

        # -- Q&A --

        def ask(query: str, top_k: int = 5):
            """Ask a question using entity-enriched vector search for context."""
            print(f'Question: "{query}"')
            print("-" * 60)

            qa_agent = Agent(
                model=bedrock_model,
                system_prompt=QA_PROMPT,
                tools=[entity_enriched_search],
            )
            response = qa_agent(
                f"Answer this question using entity-enriched search with top_k={top_k}.\n\n"
                f"Question: {query}"
            )
            print(f"\n{response}")
            return response

        # --- Run searches ---

        print("=" * 60)
        print("COMPARISON 1: Risk factors")
        print("=" * 60)
        compare_search(
            "What are the key risk factors mentioned in Apple's 10-K filing?"
        )

        print("\n")

        print("=" * 60)
        print("COMPARISON 2: Financial performance")
        print("=" * 60)
        compare_search("What financial metrics indicate company performance?")

        print("\n")

        print("=" * 60)
        print("Q&A 1: Apple risk factors")
        print("=" * 60)
        ask("What are the key risk factors mentioned in Apple's 10-K filing?")

        print("\n")

        print("=" * 60)
        print("Q&A 2: Cybersecurity risks")
        print("=" * 60)
        ask("Which companies face cybersecurity-related risks?")


if __name__ == "__main__":
    main()
