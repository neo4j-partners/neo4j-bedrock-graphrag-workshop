"""
Embeddings and Vector Index

Generates embeddings for Chunk nodes created by 06_01_data_loading, creates
a vector index for semantic similarity search, and tests with VectorRetriever.

Run with: uv run python main.py solutions <N>
"""

from neo4j_graphrag.indexes import create_vector_index, upsert_vectors
from neo4j_graphrag.retrievers import VectorRetriever

from config import get_neo4j_driver, get_embedder, BedrockConfig

INDEX_NAME = "chunkEmbeddings"


def generate_and_store_embeddings(driver, embedder) -> int:
    """Generate embeddings for all chunks that don't have one yet."""
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Chunk)
            WHERE c.embedding IS NULL
            RETURN elementId(c) AS chunk_id, c.text AS text, c.index AS index
            ORDER BY c.index
        """)
        chunks = list(result)

    if not chunks:
        print("All chunks already have embeddings")
        return 0

    print(f"Found {len(chunks)} chunks without embeddings\n")

    # Generate embeddings
    ids = []
    embeddings = []
    for chunk in chunks:
        embedding = embedder.embed_query(chunk["text"])
        ids.append(chunk["chunk_id"])
        embeddings.append(embedding)
        print(f"Embedded Chunk {chunk['index']} ({len(embedding)} dimensions)")

    # Batch upsert all embeddings
    upsert_vectors(
        driver,
        ids=ids,
        embedding_property="embedding",
        embeddings=embeddings,
    )

    return len(chunks)


def create_index(driver) -> None:
    """Create vector index for similarity search."""
    config = BedrockConfig()

    create_vector_index(
        driver=driver,
        name=INDEX_NAME,
        label="Chunk",
        embedding_property="embedding",
        dimensions=config.embedding_dimensions,
        similarity_fn="cosine",
    )


def verify_index(driver) -> None:
    """Verify the vector index was created."""
    with driver.session() as session:
        result = session.run("""
            SHOW VECTOR INDEXES
            YIELD name, labelsOrTypes, properties, state
            RETURN name, labelsOrTypes, properties, state
        """)
        for record in result:
            print(f"  Index: {record['name']} on {record['labelsOrTypes']}.{record['properties']} ({record['state']})")


def demo_search(driver, embedder) -> None:
    """Demo vector similarity search using VectorRetriever."""
    retriever = VectorRetriever(
        driver=driver,
        index_name=INDEX_NAME,
        embedder=embedder,
        return_properties=["text"],
    )

    query = "What are Apple's main risk factors?"
    print(f'Query: "{query}"\n')
    print("=== Vector Search Results ===")

    results = retriever.search(query_text=query, top_k=3)
    for i, item in enumerate(results.items, 1):
        score = item.metadata.get("score", 0)
        content = item.content if isinstance(item.content, str) else str(item.content)
        print(f"\n{i}. Score: {score:.4f}")
        print(f"   {content[:150]}...")


def main():
    """Run embeddings demo."""
    with get_neo4j_driver() as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j!")

        embedder = get_embedder()
        print(f"Embedder: {embedder.model_id}")

        # Test embedding
        sample_text = "Apple's iPhone revenue grew 5% year-over-year"
        embedding = embedder.embed_query(sample_text)
        print(f'\nText: "{sample_text}"')
        print(f"Dimensions: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")

        # Generate embeddings for existing chunks
        print("\nGenerating embeddings...")
        count = generate_and_store_embeddings(driver, embedder)
        print(f"\nAll {count} chunks embedded!")

        # Create index
        print("\nCreating vector index...")
        create_index(driver)
        print("Vector index created!")
        verify_index(driver)

        # Demo search
        print("\n")
        demo_search(driver, embedder)

    print("\n\nConnection closed.")


if __name__ == "__main__":
    main()
