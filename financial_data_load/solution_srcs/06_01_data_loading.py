"""
Data Loading Fundamentals

Builds a two-layer knowledge graph in Neo4j from scratch: structured entity
nodes (Company, Product, RiskFactor) and unstructured document chunks with
cross-link relationships.

Run with: uv run python main.py solutions <N>
"""

import os
import sys

from config import get_neo4j_driver

# Add financial_data_load to sys.path so local lib imports work
FINANCIAL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, FINANCIAL_DATA_DIR)

from lib.data_utils import split_text  # noqa: E402

# Structured filing data matching Lab_6_GraphRAG_Pipeline/financial_data.json
FILING_DATA = {
    "company": {
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "cik": "320193",
    },
    "document": {
        "name": "Apple Inc 10-K 2024",
        "source": "SEC EDGAR",
    },
    "products": [
        {"name": "iPhone", "description": "Line of smartphones based on iOS operating system"},
        {"name": "Mac", "description": "Line of personal computers based on macOS operating system"},
        {"name": "iPad", "description": "Line of multi-purpose tablets based on iPadOS operating system"},
        {"name": "Apple Watch", "description": "Wearable smartwatch device"},
        {"name": "AirPods", "description": "Wireless earbuds and headphones"},
        {"name": "Apple TV", "description": "Digital media player and streaming device"},
        {"name": "HomePod", "description": "Smart speaker"},
        {"name": "App Store", "description": "Digital distribution platform for apps"},
        {"name": "Apple Music", "description": "Music streaming subscription service"},
        {"name": "Apple TV+", "description": "Video streaming subscription service"},
        {"name": "AppleCare", "description": "Fee-based service and support products"},
        {"name": "Apple Pay", "description": "Mobile and digital payment service"},
    ],
    "risk_factors": [
        {"name": "Macroeconomic and Industry Risks", "description": "Risks from global market conditions including inflation, interest rate changes and currency fluctuations that could materially affect revenue and profitability"},
        {"name": "Supply Chain Risk", "description": "Supply chain disruptions from geopolitical tensions, natural disasters or public health emergencies that could impact manufacturing and delivery of products"},
        {"name": "Competitive Market", "description": "Intensely competitive markets with pricing pressure from competitors across all product categories"},
        {"name": "Customer Demand and Spending", "description": "Changes in consumer demand, economic conditions or buying patterns that could reduce sales volumes"},
        {"name": "Intellectual Property Risks", "description": "Unauthorized use or infringement of the Company's intellectual property that could harm competitive position"},
    ],
    "filing_text": (
        'Apple Inc. (\u201cApple\u201d or the \u201cCompany\u201d) designs, manufactures and markets smartphones, '
        "personal computers, tablets, wearables and accessories, and sells a variety of related "
        "services. The Company\u2019s fiscal year is the 52- or 53-week period that ends on the last "
        "Saturday of September. The Company is a California corporation established in 1977.\n"
        "\n"
        "Products\n"
        "\n"
        "iPhone is the Company\u2019s line of smartphones based on its iOS operating system. The iPhone "
        "product line includes iPhone 16 Pro, iPhone 16, iPhone 15 and iPhone SE. Mac is the "
        "Company\u2019s line of personal computers based on its macOS operating system, including "
        "MacBook Air, MacBook Pro, iMac, Mac mini, Mac Studio and Mac Pro. iPad is the Company\u2019s "
        "line of multi-purpose tablets based on its iPadOS operating system, including iPad Pro, "
        "iPad Air, iPad and iPad mini. Wearables, Home and Accessories includes Apple Watch, "
        "AirPods, Apple TV, HomePod and Beats products, as well as Apple-branded and third-party "
        "accessories.\n"
        "\n"
        "Services\n"
        "\n"
        "The Company\u2019s services segment includes advertising, AppleCare, cloud services, digital "
        "content and payment services. Advertising includes third-party licensing arrangements and "
        "the Company\u2019s own advertising platforms. AppleCare offers a portfolio of fee-based service "
        "and support products. Cloud Services store and keep customers\u2019 content up-to-date and "
        "available across multiple Apple devices. Digital Content operates various platforms, "
        "including the App Store, Apple Arcade, Apple Fitness+, Apple Music, Apple News+, Apple TV+ "
        "and Apple Books. Payment Services include Apple Card, Apple Cash and Apple Pay.\n"
        "\n"
        "Risk Factors\n"
        "\n"
        "The Company faces significant risks from global market conditions including inflation, "
        "interest rate changes and currency fluctuations that could materially affect revenue and "
        "profitability. Supply chain disruptions from geopolitical tensions, natural disasters or "
        "public health emergencies could impact the Company\u2019s ability to manufacture and deliver "
        "products. The Company operates in intensely competitive markets and faces pricing pressure "
        "from competitors across all product categories. Changes in consumer demand, economic "
        "conditions or buying patterns could reduce sales volumes. The Company\u2019s intellectual "
        "property is critical to its business and unauthorized use or infringement could harm "
        "competitive position.\n"
        "\n"
        "Financial Performance\n"
        "\n"
        "Total net revenue for fiscal year 2024 was $391.0 billion, compared to $383.3 billion in "
        "fiscal year 2023, an increase of 2%. iPhone revenue was $201.2 billion, representing 51% "
        "of total revenue. Services revenue reached $96.2 billion, growing 13% year-over-year and "
        "representing the fastest-growing segment. The Company\u2019s gross margin was 46.2%, up from "
        "44.1% in the prior year. Net income was $93.7 billion with diluted earnings per share of "
        "$6.08. The Company returned over $110 billion to shareholders through dividends and share "
        "repurchases during fiscal year 2024. Cash and cash equivalents totaled $29.9 billion at "
        "year end."
    ),
}


def clear_graph(driver) -> int:
    """Remove all nodes and relationships."""
    with driver.session() as session:
        result = session.run("""
            MATCH (n)
            DETACH DELETE n
            RETURN count(n) as deleted
        """)
        return result.single()["deleted"]


def create_company(driver, company: dict) -> str:
    """Create a Company node and return its element ID."""
    with driver.session() as session:
        result = session.run("""
            MERGE (c:Company {name: $name})
            SET c.ticker = $ticker, c.cik = $cik
            RETURN elementId(c) AS company_id
        """, name=company["name"], ticker=company["ticker"], cik=company["cik"])
        return result.single()["company_id"]


def create_products(driver, company_id: str, products: list[dict]) -> None:
    """Create Product nodes and OFFERS relationships from Company."""
    with driver.session() as session:
        session.run("""
            MATCH (c:Company) WHERE elementId(c) = $company_id
            UNWIND $products AS prod
            MERGE (p:Product {name: prod.name})
            SET p.description = prod.description
            MERGE (c)-[:OFFERS]->(p)
        """, company_id=company_id, products=products)


def create_risk_factors(driver, company_id: str, risk_factors: list[dict]) -> None:
    """Create RiskFactor nodes and FACES_RISK relationships from Company."""
    with driver.session() as session:
        session.run("""
            MATCH (c:Company) WHERE elementId(c) = $company_id
            UNWIND $risks AS risk
            MERGE (r:RiskFactor {name: risk.name})
            SET r.description = risk.description
            MERGE (c)-[:FACES_RISK]->(r)
        """, company_id=company_id, risks=risk_factors)


def create_document(driver, company_id: str, document: dict) -> str:
    """Create a Document node and FILED relationship from Company."""
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Company) WHERE elementId(c) = $company_id
            MERGE (d:Document {name: $name})
            SET d.source = $source
            MERGE (c)-[:FILED]->(d)
            RETURN elementId(d) AS doc_id
        """, company_id=company_id, name=document["name"], source=document["source"])
        return result.single()["doc_id"]


def create_chunks(driver, doc_id: str, chunks: list[str]) -> None:
    """Create Chunk nodes linked to a Document via FROM_DOCUMENT."""
    chunk_data = [{"index": i, "text": t} for i, t in enumerate(chunks)]
    with driver.session() as session:
        session.run("""
            MATCH (d:Document) WHERE elementId(d) = $doc_id
            UNWIND $chunks AS chunk
            MERGE (c:Chunk {index: chunk.index})
            SET c.text = chunk.text
            MERGE (c)-[:FROM_DOCUMENT]->(d)
        """, doc_id=doc_id, chunks=chunk_data)
        print(f"Created {len(chunks)} Chunk nodes with FROM_DOCUMENT relationships")


def link_chunks(driver, num_chunks: int) -> None:
    """Create NEXT_CHUNK relationships between consecutive chunks."""
    pairs = [{"idx1": i, "idx2": i + 1} for i in range(num_chunks - 1)]
    with driver.session() as session:
        session.run("""
            UNWIND $pairs AS pair
            MATCH (c1:Chunk {index: pair.idx1})
            MATCH (c2:Chunk {index: pair.idx2})
            MERGE (c1)-[:NEXT_CHUNK]->(c2)
        """, pairs=pairs)
        print(f"Created {num_chunks - 1} NEXT_CHUNK relationships")


def link_products_to_chunks(driver, products: list[dict]) -> int:
    """Create FROM_CHUNK relationships from Products to Chunks that mention them."""
    total = 0
    with driver.session() as session:
        for product in products:
            result = session.run("""
                MATCH (p:Product {name: $name})
                MATCH (c:Chunk)
                WHERE c.text CONTAINS $name
                MERGE (p)-[:FROM_CHUNK]->(c)
                RETURN count(*) AS linked
            """, name=product["name"])
            count = result.single()["linked"]
            if count > 0:
                print(f"  {product['name']} -> {count} chunk(s)")
                total += count
    print(f"\nCreated {total} FROM_CHUNK relationships")
    return total


def show_graph_structure(driver) -> None:
    """Display the full graph structure."""
    with driver.session() as session:
        # Node counts
        result = session.run("""
            MATCH (n)
            WITH labels(n)[0] AS label, n
            WHERE label IS NOT NULL
            RETURN label, count(n) AS count
            ORDER BY label
        """)
        print("\n=== Node Counts ===")
        for record in result:
            print(f"  {record['label']}: {record['count']}")

        # Relationship counts
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(r) AS count
            ORDER BY type
        """)
        print("\n=== Relationship Counts ===")
        for record in result:
            print(f"  {record['type']}: {record['count']}")

        # Structured layer
        result = session.run("""
            MATCH (c:Company)
            OPTIONAL MATCH (c)-[:OFFERS]->(p:Product)
            OPTIONAL MATCH (c)-[:FACES_RISK]->(r:RiskFactor)
            OPTIONAL MATCH (c)-[:FILED]->(d:Document)
            RETURN c.name AS company, c.ticker AS ticker,
                   count(DISTINCT p) AS products,
                   count(DISTINCT r) AS risks,
                   count(DISTINCT d) AS documents
        """)
        print("\n=== Structured Layer ===")
        for record in result:
            print(f"  {record['company']} ({record['ticker']})")
            print(f"    Products: {record['products']}, Risk Factors: {record['risks']}, Documents: {record['documents']}")

        # Chunk chain
        result = session.run("""
            MATCH (c:Chunk)
            OPTIONAL MATCH (c)-[:NEXT_CHUNK]->(next:Chunk)
            OPTIONAL MATCH (p:Product)-[:FROM_CHUNK]->(c)
            RETURN c.index AS idx, next.index AS next_idx,
                   left(c.text, 60) AS preview,
                   collect(DISTINCT p.name) AS products
            ORDER BY c.index
        """)
        print("\n=== Chunk Chain ===")
        for record in result:
            next_str = f" -> Chunk {record['next_idx']}" if record["next_idx"] is not None else " (end)"
            products_str = f" [Products: {', '.join(record['products'])}]" if record["products"] else ""
            print(f"  Chunk {record['idx']}: \"{record['preview']}...\"{next_str}{products_str}")


def main():
    """Run data loading demo."""
    with get_neo4j_driver() as driver:
        driver.verify_connectivity()
        print("Connected to Neo4j successfully!")

        # Clear existing data
        deleted = clear_graph(driver)
        print(f"Deleted {deleted} existing nodes")

        # Load filing data
        filing_text = FILING_DATA["filing_text"]
        print(f"\nCompany: {FILING_DATA['company']['name']} ({FILING_DATA['company']['ticker']})")
        print(f"Products: {len(FILING_DATA['products'])}")
        print(f"Risk Factors: {len(FILING_DATA['risk_factors'])}")
        print(f"Filing text: {len(filing_text)} characters")

        # Create structured layer
        company_id = create_company(driver, FILING_DATA["company"])
        print(f"\nCreated Company: {FILING_DATA['company']['name']} ({FILING_DATA['company']['ticker']})")

        create_products(driver, company_id, FILING_DATA["products"])
        print(f"Created {len(FILING_DATA['products'])} Product nodes with OFFERS relationships")

        create_risk_factors(driver, company_id, FILING_DATA["risk_factors"])
        print(f"Created {len(FILING_DATA['risk_factors'])} RiskFactor nodes with FACES_RISK relationships")

        # Create document and FILED relationship
        doc_id = create_document(driver, company_id, FILING_DATA["document"])
        print(f"Created Document: {FILING_DATA['document']['name']}")
        print(f"Created FILED relationship: {FILING_DATA['company']['name']} -> {FILING_DATA['document']['name']}")

        # Split text into chunks
        chunks = split_text(filing_text)
        print(f"\nSplit into {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i}: {len(chunk)} chars")
            print(f"  {chunk[:80]}...\n")

        # Create chunks and link to document
        create_chunks(driver, doc_id, chunks)

        # Link chunks sequentially
        link_chunks(driver, len(chunks))

        # Link products to chunks
        print("\nLinking products to chunks...")
        link_products_to_chunks(driver, FILING_DATA["products"])

        # Show structure
        show_graph_structure(driver)

    print("\nConnection closed.")


if __name__ == "__main__":
    main()
