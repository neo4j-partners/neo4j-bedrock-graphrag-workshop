# ---------------------------------------------------------------------------
# Reusable GraphRAG agent building blocks for the SEC 10-K knowledge graph.
#
# Single source of truth for the two neo4j-graphrag retrievers, their Strands
# @tool wrappers, and the agent factory. Consumers:
#   - agentcore_deploy/agent.py  (AgentCore handler wraps these tools)
#   - Lab 5 notebooks            (memory layer wraps the returned agent)
#
# Lab 4 notebook 01_strands_graphrag_agent.ipynb intentionally keeps this same
# tool/agent code inline as its teaching surface. If you change the tools or
# agent here, update notebook 01 to match (and vice versa).
#
# Nothing is read from the environment or Neo4j at import time. Callers pass
# config in explicitly, or use build_graphrag_agent(), which reads CONFIG.txt
# via data_utils. build_graphrag_agent() imports data_utils lazily so this
# module stays importable in the AgentCore runtime, where neither data_utils
# nor CONFIG.txt exists.
# ---------------------------------------------------------------------------

"""Reusable neo4j-graphrag retrievers, Strands tools, and agent factory."""

from __future__ import annotations

from dataclasses import dataclass

import neo4j
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import BedrockEmbeddings
from neo4j_graphrag.retrievers import VectorCypherRetriever, VectorRetriever
from neo4j_graphrag.types import RetrieverResultItem
from strands import Agent, tool
from strands.models import BedrockModel

SYSTEM_PROMPT = """You are a financial research assistant with access to SEC 10-K filings stored in a Neo4j knowledge graph.

You have two search tools:
- semantic_search: finds relevant text chunks by meaning — use for broad or thematic questions
- graph_enriched_search: finds chunks AND returns connected entities (companies, products, risk factors) — use when the question involves specific companies or relationships

Choose the tool that best fits each question. Always ground your answers in the retrieved data."""

# Retrieval query (from Lab 3, notebook 02). Traverses each matched chunk back to
# its filing document, company, products, and risk factors.
RETRIEVAL_QUERY = """
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (doc)<-[:FILED]-(company:Company)
WITH node, doc, score, company
RETURN node.text AS text,
       score,
       {document: doc.accessionNumber,
        filingType: doc.filingType,
        company: company.name,
        products: collect { MATCH (p:Product)-[:FROM_CHUNK]->(node) RETURN p.name },
        risks: collect { MATCH (r:RiskFactor)-[:FROM_CHUNK]->(node) RETURN r.name }
       } AS metadata
"""


def format_record(record: neo4j.Record) -> RetrieverResultItem:
    """Separate chunk text (content for the LLM) from structured graph metadata."""
    metadata = record.get("metadata") or {}
    metadata["score"] = record.get("score")
    return RetrieverResultItem(
        content=record.get("text", ""),
        metadata=metadata,
    )


def build_retrievers(
    uri: str,
    username: str,
    password: str,
    region: str,
) -> tuple[neo4j.Driver, VectorRetriever, VectorCypherRetriever]:
    """Create the Neo4j driver and both retrievers over the `chunkEmbeddings` index.

    Connectivity is verified before returning. The caller owns the returned
    driver and must close it (see ``GraphRAGAgent.close()``).

    Returns:
        (driver, vector_retriever, vector_cypher_retriever)
    """
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()

    # Titan Text Embeddings V2 (1024 dims), matching the chunkEmbeddings index.
    embedder = BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v2:0",
        region_name=region,
    )

    vector_retriever = VectorRetriever(
        driver=driver,
        index_name="chunkEmbeddings",
        embedder=embedder,
        return_properties=["text"],
    )

    vector_cypher_retriever = VectorCypherRetriever(
        driver=driver,
        index_name="chunkEmbeddings",
        embedder=embedder,
        retrieval_query=RETRIEVAL_QUERY,
        result_formatter=format_record,
    )

    return driver, vector_retriever, vector_cypher_retriever


def make_tools(
    vector_retriever: VectorRetriever,
    vector_cypher_retriever: VectorCypherRetriever,
) -> list:
    """Build the two Strands @tool functions bound to the given retrievers.

    The tools are closures over the retrievers rather than module-level
    globals, so multiple agents can be built against different connections in
    one process.

    Returns:
        ``[semantic_search, graph_enriched_search]`` ready for ``Agent(tools=)``.
    """

    @tool
    def semantic_search(query: str, top_k: int = 5) -> str:
        """Search SEC 10-K filing chunks by semantic similarity.

        Use this for broad or thematic questions where the text content
        of the filing chunks is sufficient to answer — for example,
        summarizing key themes, finding specific passages, or answering
        questions that don't require knowing which company or product
        is involved.

        Args:
            query: The search query.
            top_k: Number of chunks to return (default 5).

        Returns:
            The matching chunks with similarity scores.
        """
        result = vector_retriever.search(query_text=query, top_k=top_k)
        chunks = []
        for item in result.items:
            score = item.metadata.get("score", 0.0)
            chunks.append(f"[Score: {score:.4f}] {item.content}")
        return "\n\n".join(chunks)

    @tool
    def graph_enriched_search(query: str, top_k: int = 5) -> str:
        """Search SEC 10-K filing chunks with graph-enriched context.

        Use this when the question involves specific companies, products,
        or risk factors. The graph traversal adds structured entity
        information to each chunk — company names, products they offer,
        and risk factors they face — so you can answer entity-specific
        questions with precision.

        Args:
            query: The search query.
            top_k: Number of chunks to return (default 5).

        Returns:
            The matching chunks with similarity scores and entity metadata.
        """
        result = vector_cypher_retriever.search(query_text=query, top_k=top_k)
        chunks = []
        for item in result.items:
            meta = item.metadata or {}
            header = (
                f"[Score: {meta.get('score', 0):.4f}] "
                f"Company: {meta.get('company', 'N/A')} | "
                f"Products: {meta.get('products', [])} | "
                f"Risks: {meta.get('risks', [])}"
            )
            chunks.append(f"{header}\n{item.content}")
        return "\n\n".join(chunks)

    return [semantic_search, graph_enriched_search]


def build_agent(
    model_id: str,
    region: str,
    tools: list,
    *,
    system_prompt: str = SYSTEM_PROMPT,
    temperature: float = 0.0,
) -> Agent:
    """Assemble a ``strands.Agent`` with a ``BedrockModel`` and the given tools.

    Returns:
        A configured ``Agent`` ready to invoke with ``agent(prompt)``.
    """
    model = BedrockModel(
        model_id=model_id,
        region_name=region,
        temperature=temperature,
    )
    return Agent(model=model, system_prompt=system_prompt, tools=tools)


@dataclass
class GraphRAGAgent:
    """The wired agent bundled with the resources it owns."""

    agent: Agent
    tools: list
    driver: neo4j.Driver

    def close(self) -> None:
        """Close the underlying Neo4j driver."""
        self.driver.close()

    def __enter__(self) -> GraphRAGAgent:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def build_graphrag_agent() -> GraphRAGAgent:
    """Read config via ``data_utils`` and wire the full GraphRAG agent.

    One-call convenience for notebooks. ``data_utils`` is imported lazily so
    this module stays importable in the AgentCore runtime, which has neither
    ``data_utils`` nor ``CONFIG.txt``.

    Returns:
        A ``GraphRAGAgent`` bundling the agent, its tools, and the owned driver.
    """
    from lib.data_utils import BedrockConfig, Neo4jConfig

    neo4j_cfg = Neo4jConfig()
    bedrock_cfg = BedrockConfig()

    driver, vector_retriever, vector_cypher_retriever = build_retrievers(
        neo4j_cfg.uri,
        neo4j_cfg.username,
        neo4j_cfg.password,
        bedrock_cfg.region,
    )
    tools = make_tools(vector_retriever, vector_cypher_retriever)
    agent = build_agent(bedrock_cfg.model_id, bedrock_cfg.region, tools)
    return GraphRAGAgent(agent=agent, tools=tools, driver=driver)
