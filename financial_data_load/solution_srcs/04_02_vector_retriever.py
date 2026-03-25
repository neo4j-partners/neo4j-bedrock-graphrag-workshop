"""
Vector Retriever

Demonstrates semantic search using VectorRetriever and GraphRAG from
neo4j-graphrag. The retriever finds similar chunks by cosine similarity,
and GraphRAG passes those chunks to the LLM for answer generation.

Run with: uv run python main.py solutions <N>
"""

from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.retrievers import VectorRetriever

from config import get_embedder, get_llm, get_neo4j_driver


def demo_vector_search(retriever: VectorRetriever, query: str) -> None:
    """Demo direct vector search without LLM."""
    print(f'\nQuery: "{query}"')
    result = retriever.search(query_text=query, top_k=5)
    print(f"Results returned: {len(result.items)}\n")

    for i, item in enumerate(result.items, 1):
        score = item.metadata.get("score", 0.0)
        content_preview = str(item.content)[:150]
        print(f"{i}. Score: {score:.4f}")
        print(f"   {content_preview}...\n")


def demo_graphrag(llm, retriever: VectorRetriever, query: str) -> None:
    """Demo GraphRAG search with LLM answer generation."""
    rag = GraphRAG(llm=llm, retriever=retriever)
    response = rag.search(query, retriever_config={"top_k": 5}, return_context=True)

    print(f'Query: "{query}"')
    print(f"Chunks retrieved: {len(response.retriever_result.items)}\n")
    print("Answer:")
    print(response.answer)

    print("\n\n=== Retrieved Context ===")
    for i, item in enumerate(response.retriever_result.items, 1):
        score = item.metadata.get("score", 0.0)
        content_str = str(item.content)
        preview = content_str[:200] + "..." if len(content_str) > 200 else content_str
        print(f"\n[{i}] Score: {score:.4f}")
        print(f"    {preview}")


def main():
    """Run vector retriever demo."""
    with get_neo4j_driver() as driver:
        driver.verify_connectivity()
        embedder = get_embedder()
        llm = get_llm()

        print("Connected to Neo4j!")
        print(f"LLM: {llm.model_id}")
        print(f"Embedder: {embedder.model_id}")

        vector_retriever = VectorRetriever(
            driver=driver,
            index_name="chunkEmbeddings",
            embedder=embedder,
            return_properties=["text"],
        )
        print("\nVector retriever initialized!")

        # Direct vector search
        print("\n=== Direct Vector Search ===")
        demo_vector_search(vector_retriever, "What are Apple's main products?")

        # GraphRAG pipeline
        print("\n=== GraphRAG Pipeline ===")
        demo_graphrag(
            llm,
            vector_retriever,
            "What are the key risk factors mentioned in Apple's 10-K filing?",
        )

        # Experiment with another query
        print("\n=== Experiment ===")
        rag = GraphRAG(llm=llm, retriever=vector_retriever)
        query = "What financial metrics indicate Apple's performance?"
        response = rag.search(query, retriever_config={"top_k": 3})

        print(f'Query: "{query}"\n')
        print("Answer:")
        print(response.answer)

    print("\n\nConnection closed.")


if __name__ == "__main__":
    main()
