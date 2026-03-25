"""
Load Data and Query

Adds the unstructured layer — document chunks with vector embeddings — to the
existing knowledge graph. Loads pre-computed chunks from seed data, creates a
vector index, links entities to chunks, and runs test queries.

Run with: uv run python main.py solutions <N>
"""

import csv
import json
from pathlib import Path

from config import get_neo4j_driver, get_embedder

SEED_DIR = Path(__file__).parent.parent.parent / "setup" / "seed-data"


def load_seed_data():
    """Load pre-computed chunks and relationship files from seed data."""
    with open(SEED_DIR / "chunks.jsonl") as f:
        chunks = [json.loads(line) for line in f]

    def load_csv(path):
        with open(path) as f:
            return list(csv.DictReader(f))

    chunk_documents = load_csv(SEED_DIR / "chunk_documents.csv")
    chunk_sequence = load_csv(SEED_DIR / "chunk_sequence.csv")
    entity_chunks = load_csv(SEED_DIR / "entity_chunks.csv")

    return chunks, chunk_documents, chunk_sequence, entity_chunks


def verify_existing_graph(driver):
    """Verify the structured layer from Labs 1-2 is present."""
    with driver.session() as session:
        result = session.run("""
            MATCH (n)
            WITH labels(n)[0] AS label, count(n) AS count
            RETURN label, count ORDER BY label
        """)
        print("=== Existing Graph ===")
        for record in result:
            print(f'  {record["label"]}: {record["count"]}')


def create_chunks(driver, chunks):
    """Create Chunk nodes with pre-computed embeddings."""
    driver.execute_query(
        """UNWIND $chunks AS chunk
           CREATE (c:Chunk {chunkId: chunk.chunkId,
                            index: chunk.index,
                            text: chunk.text,
                            embedding: chunk.embedding})""",
        chunks=chunks,
    )
    print(f"Created {len(chunks)} Chunk nodes with embeddings")


def create_vector_index(driver):
    """Create vector index for cosine similarity search."""
    driver.execute_query("""
        CREATE VECTOR INDEX chunkEmbeddings IF NOT EXISTS
        FOR (c:Chunk) ON (c.embedding)
        OPTIONS {indexConfig: {
            `vector.dimensions`: 1024,
            `vector.similarity_function`: 'cosine'
        }}
    """)
    print("Vector index created!")


def create_from_document(driver, chunk_documents):
    """Link Chunks to Documents via FROM_DOCUMENT relationships."""
    driver.execute_query(
        """UNWIND $rels AS rel
           MATCH (c:Chunk {chunkId: rel.chunkId})
           MATCH (d:Document {documentId: rel.documentId})
           CREATE (c)-[:FROM_DOCUMENT]->(d)""",
        rels=chunk_documents,
    )
    print(f"Created {len(chunk_documents)} FROM_DOCUMENT relationships")


def create_next_chunk(driver, chunk_sequence):
    """Link consecutive Chunks via NEXT_CHUNK relationships."""
    driver.execute_query(
        """UNWIND $rels AS rel
           MATCH (curr:Chunk {chunkId: rel.chunkId})
           MATCH (next:Chunk {chunkId: rel.nextChunkId})
           CREATE (curr)-[:NEXT_CHUNK]->(next)""",
        rels=chunk_sequence,
    )
    print(f"Created {len(chunk_sequence)} NEXT_CHUNK relationships")


def create_from_chunk(driver, entity_chunks):
    """Link entities to Chunks via FROM_CHUNK relationships."""
    entity_type_map = {
        "Product": "productId",
        "RiskFactor": "riskId",
        "FinancialMetric": "metricId",
        "Company": "companyId",
    }

    total = 0
    for entity_type, id_prop in entity_type_map.items():
        rels = [r for r in entity_chunks if r["entityType"] == entity_type]
        if not rels:
            continue
        driver.execute_query(
            f"""UNWIND $rels AS rel
                MATCH (e:{entity_type} {{{id_prop}: rel.entityId}})
                MATCH (c:Chunk {{chunkId: rel.chunkId}})
                CREATE (e)-[:FROM_CHUNK]->(c)""",
            rels=rels,
        )
        print(f"  {entity_type}: {len(rels)} FROM_CHUNK relationships")
        total += len(rels)

    print(f"\nCreated {total} FROM_CHUNK relationships total")


def verify_complete_graph(driver):
    """Verify both structured and unstructured layers."""
    with driver.session() as session:
        result = session.run("""
            MATCH (n)
            WITH labels(n)[0] AS label, count(n) AS count
            RETURN label, count ORDER BY label
        """)
        print("=== Node Counts ===")
        for record in result:
            print(f'  {record["label"]}: {record["count"]}')

        result = session.run("""
            MATCH ()-[r]->()
            WITH type(r) AS type, count(r) AS count
            RETURN type, count
            ORDER BY type
        """)
        print("\n=== Relationship Counts ===")
        for record in result:
            print(f'  {record["type"]}: {record["count"]}')


def test_queries(driver):
    """Run test queries on the connected graph."""
    with driver.session() as session:
        # Companies with filing chunks
        print("\n=== Companies with Filing Chunks ===")
        result = session.run("""
            MATCH (c:Company)-[:FILED]->(d:Document)<-[:FROM_DOCUMENT]-(chunk:Chunk)
            WITH c, d, count(chunk) AS chunks
            RETURN c.name AS company, c.ticker AS ticker,
                   d.accessionNumber AS filing, chunks
            ORDER BY chunks DESC
        """)
        for record in result:
            print(f'{record["company"]} ({record["ticker"]}): {record["chunks"]} chunks — filing {record["filing"]}')

        # Products mentioned in chunks
        print("\n=== Top Products by Chunk Mentions ===")
        result = session.run("""
            MATCH (p:Product)-[:FROM_CHUNK]->(chunk:Chunk)
            WITH p, count(chunk) AS mentions
            RETURN p.name AS product, mentions
            ORDER BY mentions DESC
            LIMIT 10
        """)
        for record in result:
            print(f'  {record["product"]}: {record["mentions"]} chunk(s)')

        # Traverse from chunk to company and products
        print("\n=== Chunk Traversal (CH001) ===")
        result = session.run("""
            MATCH (chunk:Chunk {chunkId: 'CH001'})-[:FROM_DOCUMENT]->(doc:Document)
            OPTIONAL MATCH (doc)<-[:FILED]-(company:Company)
            WITH chunk, doc, company
            RETURN chunk.text AS text,
                   company.name AS company,
                   doc.accessionNumber AS filing,
                   collect { MATCH (p:Product)-[:FROM_CHUNK]->(chunk) RETURN p.name } AS products
        """)
        for record in result:
            print(f'Company: {record["company"]}')
            print(f'Filing: {record["filing"]}')
            print(f'Products mentioned: {record["products"]}')
            print(f"\nChunk text (first 200 chars):")
            print(f'  {record["text"][:200]}...')


def test_vector_search(driver):
    """Test vector similarity search."""
    embedder = get_embedder()
    query = "What are the main risk factors for technology companies?"
    query_embedding = embedder.embed_query(query)

    with driver.session() as session:
        result = session.run("""
            CALL db.index.vector.queryNodes('chunkEmbeddings', 3, $embedding)
            YIELD node, score
            MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)<-[:FILED]-(company:Company)
            RETURN company.name AS company,
                   score,
                   left(node.text, 150) AS preview
        """, embedding=query_embedding)

        print("\n=== Vector Search ===")
        print(f'Query: "{query}"\n')
        for record in result:
            print(f'{record["company"]} (score: {record["score"]:.4f})')
            print(f'  {record["preview"]}...\n')


def main():
    """Run load and query demo."""
    # Load seed data
    print("Loading seed data...")
    chunks, chunk_documents, chunk_sequence, entity_chunks = load_seed_data()
    print(f"Chunks: {len(chunks)} (with {len(chunks[0]['embedding'])}-dim embeddings)")
    print(f"FROM_DOCUMENT links: {len(chunk_documents)}")
    print(f"NEXT_CHUNK links: {len(chunk_sequence)}")
    print(f"FROM_CHUNK entity links: {len(entity_chunks)}")

    with get_neo4j_driver() as driver:
        driver.verify_connectivity()
        print("\nConnected to Neo4j!")

        # Verify existing graph
        verify_existing_graph(driver)

        # Create chunks with embeddings
        print("\nCreating chunks...")
        create_chunks(driver, chunks)

        # Create vector index
        create_vector_index(driver)

        # Create relationships
        print("\nLinking chunks to documents...")
        create_from_document(driver, chunk_documents)

        print("\nLinking consecutive chunks...")
        create_next_chunk(driver, chunk_sequence)

        print("\nLinking entities to chunks...")
        create_from_chunk(driver, entity_chunks)

        # Verify
        print()
        verify_complete_graph(driver)

        # Test queries
        test_queries(driver)

        # Vector search
        test_vector_search(driver)

    print("\nConnection closed.")


if __name__ == "__main__":
    main()
