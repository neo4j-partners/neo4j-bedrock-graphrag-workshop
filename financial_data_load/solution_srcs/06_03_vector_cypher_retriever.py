"""
VectorCypher Retriever (GraphRAG Pipeline)

Combines vector similarity search with Cypher graph traversal to enrich
results with companies, products, and risk factors from the knowledge graph.
Builds a complete GraphRAG pipeline for question answering.

Run with: uv run python main.py solutions <N>
"""

from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.retrievers import VectorCypherRetriever

from config import get_embedder, get_llm, get_neo4j_driver

# Retrieval query enriches vector results with entity context.
# Traverses from matched chunk to document, company, risk factors, and products.
RETRIEVAL_QUERY = """
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (doc)<-[:FILED]-(company:Company)
OPTIONAL MATCH (company)-[:FACES_RISK]->(risk:RiskFactor)
OPTIONAL MATCH (product:Product)-[:FROM_CHUNK]->(node)
WITH node, doc, score,
     collect(DISTINCT company.name) AS companies,
     collect(DISTINCT risk.name)[0..5] AS risks,
     collect(DISTINCT product.name)[0..5] AS products
RETURN node.text AS text,
       score,
       {document: doc.name, companies: companies, products: products, risks: risks} AS metadata
"""


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
        )
        print("\nVectorCypherRetriever initialized!")

        # GraphRAG pipeline
        rag = GraphRAG(llm=llm, retriever=vector_cypher_retriever)

        query = "What are the key risk factors mentioned in Apple's 10-K filing?"
        response = rag.search(query, retriever_config={"top_k": 5}, return_context=True)

        print(f'\nQuery: "{query}"\n')
        print("Answer:")
        print(response.answer)

        print("\n\n=== Enriched Context ===")
        for i, item in enumerate(response.retriever_result.items, 1):
            content_str = str(item.content)
            preview = content_str[:300] + "..." if len(content_str) > 300 else content_str
            print(f"\n[{i}] {preview}")

    print("\n\nConnection closed.")


if __name__ == "__main__":
    main()
