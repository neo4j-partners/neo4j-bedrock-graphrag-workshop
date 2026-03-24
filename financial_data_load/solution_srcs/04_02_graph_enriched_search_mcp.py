"""
Graph-Enriched Search via MCP

This solution demonstrates vector search enriched with graph context
(documents, neighboring chunks, entities) through the Neo4j MCP server
using the Strands Agents SDK.

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
# 3. System Prompts
# ---------------------------------------------------------------------------

VECTOR_ONLY_PROMPT = """You are a retrieval assistant that performs vector search against a Neo4j database.

When given a query embedding, use this Cypher to find similar chunks:

CALL db.index.vector.queryNodes('chunkEmbeddings', $top_k, $embedding)
YIELD node, score
RETURN node.text AS text, score
ORDER BY score DESC

Return the chunk text and similarity score. Use the exact embedding provided."""

GRAPH_ENRICHED_PROMPT = """You are a retrieval assistant that performs graph-enriched vector search against a Neo4j database containing SEC 10-K filing data.

When given a query embedding, use this Cypher to find similar chunks WITH graph context:

CALL db.index.vector.queryNodes('chunkEmbeddings', $top_k, $embedding)
YIELD node, score
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next:Chunk)
OPTIONAL MATCH (prev:Chunk)-[:NEXT_CHUNK]->(node)
WITH node, doc, score,
     CASE WHEN prev IS NOT NULL THEN prev.text ELSE '' END AS prev_text,
     CASE WHEN next IS NOT NULL THEN next.text ELSE '' END AS next_text
RETURN node.text AS text,
       score,
       doc.name AS document,
       prev_text AS previous_chunk,
       next_text AS next_chunk
ORDER BY score DESC

This query:
1. Finds the most similar chunks via vector search
2. Traverses FROM_DOCUMENT to get the source document name
3. Follows NEXT_CHUNK relationships to get neighboring chunk text
4. Returns the enriched context alongside each match

Use the exact embedding provided. For each result, show:
- Similarity score
- Source document name
- The matched chunk text
- Context from neighboring chunks (if available)"""

ENTITY_ENRICHED_PROMPT = """You are a retrieval assistant that performs entity-enriched vector search against a Neo4j database containing SEC 10-K filing data.

When given a query embedding, use this Cypher to find similar chunks WITH entity context:

CALL db.index.vector.queryNodes('chunkEmbeddings', $top_k, $embedding)
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
RETURN node.text AS text,
       score,
       doc.name AS document,
       companies,
       risks,
       products
ORDER BY score DESC

This query:
1. Finds the most similar chunks via vector search
2. Traverses FROM_DOCUMENT to get the source document
3. Follows FILED to find the company that filed the document
4. Follows FACES_RISK from companies to find their risk factors

Use the exact embedding provided. For each result, show:
- Similarity score
- Source document name
- The matched chunk text
- Companies, products, and risk factors connected to the chunk"""

QA_PROMPT = """You are a financial analysis assistant with access to a Neo4j knowledge graph containing SEC 10-K filing data.

You have MCP tools to execute Cypher queries. Use entity-enriched vector search to answer questions:

CALL db.index.vector.queryNodes('chunkEmbeddings', $top_k, $embedding)
YIELD node, score
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (doc)<-[:FILED]-(company:Company)
OPTIONAL MATCH (company)-[:FACES_RISK]->(risk:RiskFactor)
OPTIONAL MATCH (product:Product)-[:FROM_CHUNK]->(node)
WITH node, doc, score,
     collect(DISTINCT company.name) AS companies,
     collect(DISTINCT risk.name)[0..5] AS risks,
     collect(DISTINCT product.name)[0..5] AS products
RETURN node.text AS text, score, doc.name AS document,
       companies, risks, products
ORDER BY score DESC

After retrieving results, synthesize a clear answer based on the retrieved context.
Include the companies, products, and risk factors found. Cite the source documents.
Use the exact embedding provided."""


# ---------------------------------------------------------------------------
# 4. Initialize Model and MCP Client
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


# ---------------------------------------------------------------------------
# 5. Compare Search Helper
# ---------------------------------------------------------------------------


def compare_search(query: str, top_k: int = 3):
    """Run the same query through all three agents and display results."""
    embedding = get_embedding(query)

    message = (
        f"Run a vector search for the following query. Use top_k={top_k}.\n\n"
        f"Query: {query}\n\n"
        f"Embedding (use this exact array in the Cypher query):\n{json.dumps(embedding)}"
    )

    print(f'Query: "{query}"')
    print("=" * 60)

    with mcp_client:
        tools = mcp_client.list_tools_sync()

        # Vector-only search
        print("\n--- VECTOR-ONLY RESULTS ---\n")
        vector_agent = Agent(
            model=bedrock_model,
            system_prompt=VECTOR_ONLY_PROMPT,
            tools=tools,
        )
        print(vector_agent(message))

        # Graph-enriched search
        print("\n\n--- GRAPH-ENRICHED RESULTS ---\n")
        graph_agent = Agent(
            model=bedrock_model,
            system_prompt=GRAPH_ENRICHED_PROMPT,
            tools=tools,
        )
        print(graph_agent(message))

        # Entity-enriched search
        print("\n\n--- ENTITY-ENRICHED RESULTS ---\n")
        entity_agent = Agent(
            model=bedrock_model,
            system_prompt=ENTITY_ENRICHED_PROMPT,
            tools=tools,
        )
        print(entity_agent(message))


# ---------------------------------------------------------------------------
# 6. Q&A Helper
# ---------------------------------------------------------------------------


def ask(query: str, top_k: int = 5):
    """Ask a question using graph-enriched vector search for context."""
    embedding = get_embedding(query)

    message = (
        f"Answer this question using graph-enriched vector search with top_k={top_k}.\n\n"
        f"Question: {query}\n\n"
        f"Embedding:\n{json.dumps(embedding)}"
    )

    print(f'Question: "{query}"')
    print("-" * 60)

    with mcp_client:
        tools = mcp_client.list_tools_sync()
        qa_agent = Agent(
            model=bedrock_model,
            system_prompt=QA_PROMPT,
            tools=tools,
        )
        response = qa_agent(message)
        print(f"\n{response}")
        return response


# ---------------------------------------------------------------------------
# 7. Main
# ---------------------------------------------------------------------------


def main():
    """Run graph-enriched search demo."""
    print(f"Model:     {MODEL_ID}")
    print(f"Region:    {REGION}")
    print()

    # Compare: risk factors query
    print("=" * 60)
    print("COMPARISON 1: Risk factors")
    print("=" * 60)
    compare_search(
        "What are the key risk factors mentioned in Apple's 10-K filing?"
    )

    print("\n")

    # Compare: financial performance query
    print("=" * 60)
    print("COMPARISON 2: Financial performance")
    print("=" * 60)
    compare_search("What financial metrics indicate company performance?")

    print("\n")

    # Q&A: risk factors
    print("=" * 60)
    print("Q&A 1: Apple risk factors")
    print("=" * 60)
    ask("What are the key risk factors mentioned in Apple's 10-K filing?")

    print("\n")

    # Q&A: cybersecurity risks
    print("=" * 60)
    print("Q&A 2: Cybersecurity risks")
    print("=" * 60)
    ask("Which companies face cybersecurity-related risks?")


if __name__ == "__main__":
    main()
