"""
Hybrid RAG: HybridRetriever + GraphRAG

Demonstrates how hybrid search (vector + fulltext) improves RAG answer quality
compared to vector-only search. Uses HybridRetriever as the retriever inside
GraphRAG for LLM-generated answers grounded in retrieved context.

Key concepts:
- HybridRetriever combines vector (semantic) and fulltext (keyword) search
- Alpha parameter controls the balance: 1.0=pure vector, 0.0=pure fulltext
- GraphRAG orchestrates retrieval + LLM answer generation
- Comparing vector-only vs hybrid shows when each approach excels

Usage:
    uv run python main.py solutions 12
"""

from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.retrievers import VectorRetriever, HybridRetriever

from config import get_neo4j_driver, get_embedder, get_llm

# Index names
VECTOR_INDEX = "chunkEmbeddings"
FULLTEXT_INDEX = "search_chunks"


def vector_only_rag(llm, retriever: VectorRetriever, query: str) -> str:
    """RAG using vector-only retrieval."""
    rag = GraphRAG(llm=llm, retriever=retriever)
    response = rag.search(query, retriever_config={"top_k": 5}, return_context=True)

    print(f"  Retrieved {len(response.retriever_result.items)} chunks")
    return response.answer


def hybrid_rag(llm, retriever: HybridRetriever, query: str, alpha: float = 0.5) -> str:
    """RAG using hybrid retrieval with configurable alpha."""
    rag = GraphRAG(llm=llm, retriever=retriever)
    response = rag.search(
        query,
        retriever_config={"top_k": 5, "alpha": alpha},
        return_context=True,
    )

    print(f"  Retrieved {len(response.retriever_result.items)} chunks (alpha={alpha})")
    return response.answer


def compare_rag(llm, vector_retriever, hybrid_retriever, query: str) -> None:
    """Compare vector-only vs hybrid RAG answers for the same query."""
    print(f"\nQuery: {query}")
    print("=" * 60)

    print("\n[VECTOR-ONLY RAG]")
    vector_answer = vector_only_rag(llm, vector_retriever, query)
    print(f"  Answer: {vector_answer}\n")

    print("[HYBRID RAG - alpha=0.5]")
    hybrid_answer = hybrid_rag(llm, hybrid_retriever, query, alpha=0.5)
    print(f"  Answer: {hybrid_answer}\n")


def demo_alpha_sweep(llm, retriever: HybridRetriever, query: str) -> None:
    """Show how alpha affects RAG answers for the same query."""
    print(f"\nQuery: {query}")
    print("=" * 60)

    for alpha in [1.0, 0.7, 0.5, 0.3, 0.0]:
        label = {
            1.0: "Pure Vector",
            0.7: "Vector-heavy",
            0.5: "Balanced",
            0.3: "Fulltext-heavy",
            0.0: "Pure Fulltext",
        }[alpha]

        print(f"\n[alpha={alpha} — {label}]")
        answer = hybrid_rag(llm, retriever, query, alpha=alpha)
        print(f"  Answer: {answer[:300]}...")


def main() -> None:
    """Run hybrid RAG examples."""
    with get_neo4j_driver() as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j")

        embedder = get_embedder()
        llm = get_llm()
        print(f"Embedder: {embedder.model_id}")
        print(f"LLM: {llm.model_id}")

        # Check indexes exist
        with driver.session() as session:
            result = session.run(
                "SHOW FULLTEXT INDEXES YIELD name WHERE name = $name RETURN name",
                name=FULLTEXT_INDEX,
            )
            if not result.single():
                print(f"\nError: Fulltext index '{FULLTEXT_INDEX}' not found.")
                print("Run: uv run python main.py load --clear to create indexes.")
                return

            result = session.run(
                "SHOW VECTOR INDEXES YIELD name WHERE name = $name RETURN name",
                name=VECTOR_INDEX,
            )
            if not result.single():
                print(f"\nError: Vector index '{VECTOR_INDEX}' not found.")
                print("Run: uv run python main.py load --clear to create indexes.")
                return

        # Create retrievers
        vector_retriever = VectorRetriever(
            driver=driver,
            index_name=VECTOR_INDEX,
            embedder=embedder,
            return_properties=["text"],
        )

        hybrid_retriever = HybridRetriever(
            driver=driver,
            vector_index_name=VECTOR_INDEX,
            fulltext_index_name=FULLTEXT_INDEX,
            embedder=embedder,
            return_properties=["text"],
        )

        # Comparison 1: Specific entity query — fulltext helps find exact names
        compare_rag(
            llm,
            vector_retriever,
            hybrid_retriever,
            "What risk factors does Apple face?",
        )

        # Comparison 2: Conceptual query — vector captures semantic meaning
        compare_rag(
            llm,
            vector_retriever,
            hybrid_retriever,
            "How do companies manage supply chain disruptions?",
        )

        # Comparison 3: Mixed query — hybrid shines with both names and concepts
        compare_rag(
            llm,
            vector_retriever,
            hybrid_retriever,
            "What products does Microsoft offer related to cloud computing?",
        )

        # Alpha sweep — show how tuning alpha changes the answer
        demo_alpha_sweep(
            llm,
            hybrid_retriever,
            "What are Nvidia's key financial risks?",
        )

    print("\nConnection closed")


if __name__ == "__main__":
    main()


# Example queries to try:
# - What risk factors does Apple face?
# - How do companies manage supply chain disruptions?
# - What products does Microsoft offer related to cloud computing?
# - What are Nvidia's key financial risks?
# - Which companies mention cybersecurity in their filings?
