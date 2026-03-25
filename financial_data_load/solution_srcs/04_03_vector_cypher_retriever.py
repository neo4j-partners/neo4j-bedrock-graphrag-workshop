"""
VectorCypher Retriever

Combines vector similarity search with custom Cypher graph traversal.
After the vector index finds matching chunks, a Cypher query traverses
to related nodes (documents, companies, products, risk factors) to
enrich the context sent to the LLM.

Run with: uv run python main.py solutions <N>
"""

import neo4j
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.retrievers import VectorCypherRetriever
from neo4j_graphrag.types import RetrieverResultItem

from config import get_embedder, get_llm, get_neo4j_driver

# Retrieval query traverses from matched chunk to document, company, and
# uses COLLECT subqueries to gather products and risk factors linked to
# the specific chunk via FROM_CHUNK.
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
    """Separate chunk text (content for LLM) from structured graph metadata."""
    metadata = record.get("metadata") or {}
    metadata["score"] = record.get("score")
    return RetrieverResultItem(
        content=record.get("text", ""),
        metadata=metadata,
    )


def main():
    """Run vector cypher retriever demo."""
    with get_neo4j_driver() as driver:
        driver.verify_connectivity()
        embedder = get_embedder()
        llm = get_llm()

        print("Connected to Neo4j!")
        print(f"LLM: {llm.model_id}")
        print(f"Embedder: {embedder.model_id}")

        vector_cypher_retriever = VectorCypherRetriever(
            driver=driver,
            index_name="chunkEmbeddings",
            embedder=embedder,
            retrieval_query=RETRIEVAL_QUERY,
            result_formatter=format_record,
        )
        print("\nVectorCypherRetriever initialized!")

        # Search with graph context
        print("\n=== VectorCypherRetriever Search ===")
        query = "What are the financial risks?"
        cypher_result = vector_cypher_retriever.search(query_text=query, top_k=2)

        print(f'Query: "{query}"\n')
        for i, item in enumerate(cypher_result.items, 1):
            meta = item.metadata or {}
            print(f"[{i}] Score: {meta.get('score', 0):.4f}")
            print(f"    Company: {meta.get('company', 'N/A')}")
            print(f"    Products: {meta.get('products', [])}")
            print(f"    Risks: {meta.get('risks', [])}")
            content_preview = str(item.content)[:200]
            print(f"    Text: {content_preview}...\n")

        # GraphRAG with enriched context
        print("\n=== GraphRAG with Graph Context ===")
        rag = GraphRAG(llm=llm, retriever=vector_cypher_retriever)

        query = "What are the key risk factors mentioned in Apple's 10-K filing?"
        response = rag.search(query, retriever_config={"top_k": 5}, return_context=True)

        print(f'Query: "{query}"\n')
        print("Answer:")
        print(response.answer)

        print("\n\n=== Enriched Context ===")
        for i, item in enumerate(response.retriever_result.items, 1):
            meta = item.metadata or {}
            print(f"\n[{i}] Score: {meta.get('score', 0):.4f} | Company: {meta.get('company', 'N/A')}")
            print(f"    Products: {meta.get('products', [])} | Risks: {meta.get('risks', [])}")
            content_preview = str(item.content)[:200]
            print(f"    Text: {content_preview}...")

    print("\n\nConnection closed.")


if __name__ == "__main__":
    main()
