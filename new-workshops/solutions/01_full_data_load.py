"""
Full Data Loading with SimpleKGPipeline and AWS Bedrock

This solution loads all SEC 10-K filings from the form10k-sample directory,
extracts entities and relationships using Claude via Bedrock, generates
embeddings with Titan V2, and stores everything in Neo4j.

Pipeline Flow:
1. Load CSV metadata (company names, tickers, CIK numbers)
2. Create Company nodes from CSV with normalized names
3. Run SimpleKGPipeline on each PDF to extract entities
4. Library uses MERGE (not CREATE) so extracted entities merge with existing nodes
5. Create AssetManager nodes and OWNS relationships

The neo4j-graphrag-python library now uses MERGE by default for node creation,
which prevents duplicate entities when the same company is mentioned in multiple
chunks of a document. See CREATE_MERGE.md in the library for details.

Run with: uv run python -m solutions.01_full_data_load
Options:
  --limit N        Process only N PDFs (for testing)
  --skip-metadata  Skip loading CSV metadata
  --clear          Clear database before loading

Prerequisites:
- AWS credentials configured (for Bedrock access)
- Neo4j connection configured in .env
- PDFs in DATA_DIR (defaults to ~/projects/workshops/workshop-financial-data)
"""

import asyncio
import csv
import logging
from pathlib import Path
from typing import Optional

import neo4j
from neo4j import GraphDatabase

from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.components.schema import GraphSchema
from neo4j_graphrag.llm import BedrockLLM
from neo4j_graphrag.embeddings import BedrockEmbeddings

from .config import Neo4jConfig
from .name_utils import normalize_company_name

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data directory - adjust this path as needed
DATA_DIR = Path.home() / "projects" / "workshops" / "workshop-financial-data"
PDF_DIR = DATA_DIR / "form10k-sample"
COMPANY_CSV = DATA_DIR / "Company_Filings.csv"
ASSET_MANAGER_CSV = DATA_DIR / "Asset_Manager_Holdings.csv"

# Schema for SEC 10-K financial documents
# Note: Properties require a 'type' field (STRING, INTEGER, FLOAT, etc.)
SEC_SCHEMA = GraphSchema.model_validate({
    "node_types": [
        {
            "label": "Company",
            "description": "A publicly traded company",
            "properties": [
                {"name": "name", "type": "STRING", "description": "Company name"},
                {"name": "ticker", "type": "STRING", "description": "Stock ticker symbol"},
            ],
        },
        {
            "label": "RiskFactor",
            "description": "A risk factor disclosed in the 10-K filing",
            "properties": [
                {"name": "name", "type": "STRING", "description": "Short name of the risk"},
                {"name": "description", "type": "STRING", "description": "Detailed description"},
            ],
        },
        {
            "label": "Product",
            "description": "A product or service offered by the company",
            "properties": [
                {"name": "name", "type": "STRING", "description": "Product name"},
            ],
        },
        {
            "label": "Executive",
            "description": "A company executive or board member",
            "properties": [
                {"name": "name", "type": "STRING", "description": "Person's name"},
                {"name": "title", "type": "STRING", "description": "Job title"},
            ],
        },
        {
            "label": "FinancialMetric",
            "description": "A financial metric or KPI",
            "properties": [
                {"name": "name", "type": "STRING", "description": "Metric name"},
                {"name": "value", "type": "STRING", "description": "Metric value"},
                {"name": "period", "type": "STRING", "description": "Reporting period"},
            ],
        },
    ],
    "relationship_types": [
        {
            "label": "FACES_RISK",
            "description": "Company faces this risk factor",
        },
        {
            "label": "OFFERS",
            "description": "Company offers this product/service",
        },
        {
            "label": "HAS_EXECUTIVE",
            "description": "Company has this executive",
        },
        {
            "label": "REPORTS",
            "description": "Company reports this financial metric",
        },
        {
            "label": "COMPETES_WITH",
            "description": "Company competes with another company",
        },
        {
            "label": "PARTNERS_WITH",
            "description": "Company partners with another company",
        },
    ],
    "patterns": [
        ("Company", "FACES_RISK", "RiskFactor"),
        ("Company", "OFFERS", "Product"),
        ("Company", "HAS_EXECUTIVE", "Executive"),
        ("Company", "REPORTS", "FinancialMetric"),
        ("Company", "COMPETES_WITH", "Company"),
        ("Company", "PARTNERS_WITH", "Company"),
    ],
})


def load_company_metadata(csv_path: Path) -> dict[str, dict]:
    """Load company metadata from CSV, keyed by PDF filename."""
    companies = {}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract filename from path
            path = row.get("path_Mac_ix", "")
            filename = Path(path).name if path else None
            if filename:
                companies[filename] = {
                    "name": row.get("name", ""),
                    "ticker": row.get("ticker", ""),
                    "cik": row.get("cik", ""),
                    "cusip": row.get("cusip", ""),
                }
    return companies


def load_asset_managers(csv_path: Path) -> list[dict]:
    """Load asset manager holdings from CSV."""
    holdings = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            holdings.append({
                "manager_name": row.get("managerName", ""),
                "company_name": row.get("companyName", ""),
                "shares": int(row.get("shares", 0)),
            })
    return holdings


async def clear_database(driver: neo4j.Driver) -> None:
    """Clear all nodes and relationships from the database."""
    logger.info("Clearing database...")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    logger.info("Database cleared")


async def create_company_nodes(driver: neo4j.Driver, companies: dict[str, dict]) -> None:
    """Create Company nodes from CSV metadata before LLM extraction.

    The library now uses MERGE by default (see CREATE_MERGE.md in neo4j-graphrag-python),
    so these nodes will be merged with any Company nodes the LLM extracts.
    Name normalization ensures CSV names match LLM-extracted names.
    """
    logger.info(f"Creating {len(companies)} Company nodes from metadata...")

    with driver.session() as session:
        # Create uniqueness constraint - works now because library uses MERGE
        session.run("""
            CREATE CONSTRAINT company_name IF NOT EXISTS
            FOR (c:Company) REQUIRE c.name IS UNIQUE
        """)

        # Create companies with normalized names
        for filename, meta in companies.items():
            normalized_name = normalize_company_name(meta["name"])
            session.run("""
                MERGE (c:Company {name: $name})
                SET c.ticker = $ticker,
                    c.cik = $cik,
                    c.cusip = $cusip
            """, name=normalized_name, ticker=meta["ticker"],
                cik=meta["cik"], cusip=meta["cusip"])

    logger.info("Company nodes created")


async def create_asset_manager_relationships(
    driver: neo4j.Driver,
    holdings: list[dict]
) -> None:
    """Create AssetManager nodes and OWNS relationships."""
    logger.info("Creating asset manager relationships...")

    with driver.session() as session:
        # Create constraint
        session.run("""
            CREATE CONSTRAINT asset_manager_name IF NOT EXISTS
            FOR (a:AssetManager) REQUIRE a.managerName IS UNIQUE
        """)

        # Create asset managers and relationships
        # Normalize company names to match the Company nodes we created
        for holding in holdings:
            normalized_company = normalize_company_name(holding["company_name"])
            session.run("""
                MERGE (a:AssetManager {managerName: $manager_name})
                WITH a
                MATCH (c:Company {name: $company_name})
                MERGE (a)-[r:OWNS]->(c)
                SET r.shares = $shares
            """, manager_name=holding["manager_name"],
                company_name=normalized_company,
                shares=holding["shares"])

    logger.info("Asset manager relationships created")


async def process_pdf(
    pipeline: SimpleKGPipeline,
    pdf_path: Path,
    company_meta: Optional[dict] = None,
) -> None:
    """Process a single PDF through the KG pipeline."""
    logger.info(f"Processing: {pdf_path.name}")

    metadata = {"source": str(pdf_path)}
    if company_meta:
        metadata.update(company_meta)

    try:
        result = await pipeline.run_async(
            file_path=str(pdf_path),
            document_metadata=metadata,
        )
        logger.info(f"  Completed: {pdf_path.name} - {result}")
    except Exception as e:
        logger.error(f"  Failed: {pdf_path.name} - {e}")


async def main(
    pdf_limit: Optional[int] = None,
    skip_metadata: bool = False,
    clear_db: bool = False,
) -> None:
    """
    Run the full data loading pipeline.

    Args:
        pdf_limit: Limit number of PDFs to process (for testing). None = all.
        skip_metadata: Skip loading CSV metadata (Company, AssetManager nodes).
        clear_db: Clear all nodes/relationships before loading.
    """
    # Check data directory exists
    if not DATA_DIR.exists():
        logger.error(f"Data directory not found: {DATA_DIR}")
        logger.error("Please update DATA_DIR in this file or symlink the data.")
        return

    if not PDF_DIR.exists():
        logger.error(f"PDF directory not found: {PDF_DIR}")
        return

    # Get list of PDFs
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        logger.error(f"No PDF files found in: {PDF_DIR}")
        return

    if pdf_limit:
        pdf_files = pdf_files[:pdf_limit]

    logger.info(f"Found {len(pdf_files)} PDF files to process")

    # Load metadata
    company_meta = {}
    if COMPANY_CSV.exists():
        company_meta = load_company_metadata(COMPANY_CSV)
        logger.info(f"Loaded metadata for {len(company_meta)} companies")

    asset_holdings = []
    if ASSET_MANAGER_CSV.exists():
        asset_holdings = load_asset_managers(ASSET_MANAGER_CSV)
        logger.info(f"Loaded {len(asset_holdings)} asset manager holdings")

    # Initialize Neo4j
    config = Neo4jConfig()
    driver = GraphDatabase.driver(
        config.uri,
        auth=(config.username, config.password),
    )

    try:
        driver.verify_connectivity()
        logger.info(f"Connected to Neo4j: {config.uri}")

        # Clear database if requested
        if clear_db:
            await clear_database(driver)

        # Create metadata nodes BEFORE extraction
        # The library now uses MERGE by default, so LLM-extracted entities
        # will merge with these pre-created nodes instead of conflicting.
        if not skip_metadata and company_meta:
            await create_company_nodes(driver, company_meta)

        # Initialize Bedrock LLM and Embedder
        logger.info("Initializing Bedrock LLM and Embedder...")
        # Use Claude 4.5 Sonnet via US inference profile
        # Direct model access requires inference profiles for newer models
        # See: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html
        llm = BedrockLLM(
            model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
            inference_profile_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            region_name="us-east-1",
            model_params={
                "maxTokens": 4096,
                "temperature": 0,
            },
        )

        embedder = BedrockEmbeddings(
            region_name="us-east-1",
            # Titan V2 defaults to 1024 dimensions
        )

        # Create pipeline
        logger.info("Creating SimpleKGPipeline...")
        pipeline = SimpleKGPipeline(
            llm=llm,
            driver=driver,
            embedder=embedder,
            schema=SEC_SCHEMA,
            from_pdf=True,
            on_error="IGNORE",  # Continue on extraction errors
            perform_entity_resolution=True,
        )

        # Process each PDF
        for pdf_path in pdf_files:
            meta = company_meta.get(pdf_path.name)
            await process_pdf(pipeline, pdf_path, meta)

        logger.info("=" * 50)
        logger.info(f"Processed {len(pdf_files)} PDFs")

        # Create asset manager relationships (after Companies exist)
        if not skip_metadata and asset_holdings:
            await create_asset_manager_relationships(driver, asset_holdings)

        logger.info("Data loading complete!")

        # Show summary
        with driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(n) AS count
                ORDER BY count DESC
            """)
            logger.info("Node counts:")
            for record in result:
                logger.info(f"  {record['label']}: {record['count']}")

    finally:
        driver.close()
        logger.info("Connection closed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load SEC 10-K data into Neo4j")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of PDFs to process (for testing)",
    )
    parser.add_argument(
        "--skip-metadata",
        action="store_true",
        help="Skip loading CSV metadata",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear database before loading",
    )
    args = parser.parse_args()

    asyncio.run(main(pdf_limit=args.limit, skip_metadata=args.skip_metadata, clear_db=args.clear))
