# ---------------------------------------------------------------------------
# COPIED from root lib/data_utils.py to simplify env loading.
# financial_data_load uses .env (not CONFIG.txt), so this local copy loads
# from the financial_data_load/.env instead of the project-root CONFIG.txt.
#
# If you change this file, update the root lib/data_utils.py as well.
# If you change the root lib/data_utils.py, update this file as well.
# ---------------------------------------------------------------------------

"""Utilities for data loading, Neo4j operations, and AWS Bedrock AI services."""

import asyncio
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import BedrockNovaEmbeddings
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.llm import BedrockLLM
from neo4j_graphrag.schema import get_schema as _lib_get_schema
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load configuration from financial_data_load/.env
_env_file = Path(__file__).parent.parent / ".env"
load_dotenv(_env_file)


# =============================================================================
# Configuration Classes
# =============================================================================

class Neo4jConfig(BaseSettings):
    """Neo4j configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    uri: str = Field(validation_alias="NEO4J_URI")
    username: str = Field(default="neo4j", validation_alias="NEO4J_USERNAME")
    password: str = Field(validation_alias="NEO4J_PASSWORD")


class BedrockConfig(BaseSettings):
    """AWS Bedrock configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        validation_alias="MODEL_ID"
    )
    region: str = Field(default="us-east-1", validation_alias="REGION")
    embedding_dimensions: int = Field(default=1024, validation_alias="EMBEDDING_DIMENSIONS")


# =============================================================================
# AI Services
# =============================================================================

def get_embedder() -> BedrockNovaEmbeddings:
    """Get embedder using AWS Bedrock Nova Multimodal Embeddings.

    Returns a BedrockNovaEmbeddings object for use with neo4j-graphrag retrievers.
    """
    config = BedrockConfig()

    return BedrockNovaEmbeddings(
        region_name=config.region,
        embedding_dimension=config.embedding_dimensions,
    )


def get_llm() -> BedrockLLM:
    """Get LLM using AWS Bedrock."""
    config = BedrockConfig()

    return BedrockLLM(
        model_id=config.model_id,
        region_name=config.region,
    )


_embedder = None


def get_embedding(text: str) -> list[float]:
    """Generate an embedding vector for text using Bedrock Nova.

    Returns the raw float array for use in Cypher vector search queries.
    """
    global _embedder
    if _embedder is None:
        _embedder = get_embedder()
    return _embedder.embed_query(text)


def get_schema(driver) -> str:
    """Get the schema of the Neo4j database.

    Args:
        driver: Neo4j driver instance.

    Returns:
        String representation of the database schema.
    """
    return _lib_get_schema(driver, sanitize=True)


# =============================================================================
# Neo4j Connection
# =============================================================================

class Neo4jConnection:
    """Manages Neo4j database connection."""

    def __init__(self):
        """Initialize and connect to Neo4j using environment configuration."""
        self.config = Neo4jConfig()
        self.driver = GraphDatabase.driver(
            self.config.uri,
            auth=(self.config.username, self.config.password)
        )

    def verify(self):
        """Verify the connection is working."""
        self.driver.verify_connectivity()
        print("Connected to Neo4j successfully!")
        return self

    def clear_graph(self):
        """Remove all nodes and relationships in batches."""
        total_deleted = 0
        with self.driver.session() as session:
            while True:
                result = session.run("""
                    MATCH (n)
                    WITH n LIMIT 500
                    DETACH DELETE n
                    RETURN count(*) as deleted
                """)
                count = result.single()["deleted"]
                if count == 0:
                    break
                total_deleted += count
            print(f"Deleted {total_deleted} nodes")
        return self

    def close(self):
        """Close the database connection."""
        self.driver.close()
        print("Connection closed.")


# =============================================================================
# Data Loading
# =============================================================================

class DataLoader:
    """Handles loading text data from files."""

    def __init__(self, file_path: str):
        """Initialize with path to data file."""
        self.file_path = Path(file_path)
        self._text = None

    @property
    def text(self) -> str:
        """Load and return the text content from the file."""
        if self._text is None:
            self._text = self.file_path.read_text().strip()
        return self._text

    def get_metadata(self) -> dict:
        """Return metadata about the loaded file."""
        return {
            "path": str(self.file_path),
            "name": self.file_path.name,
            "size": len(self.text)
        }



# =============================================================================
# Text Splitting
# =============================================================================

def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Split text into chunks using FixedSizeSplitter.

    Args:
        text: Text to split
        chunk_size: Maximum characters per chunk
        chunk_overlap: Characters to overlap between chunks

    Returns:
        List of chunk text strings
    """
    splitter = FixedSizeSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        approximate=True
    )

    # Handle both Jupyter (running event loop) and regular Python
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        import nest_asyncio
        nest_asyncio.apply()
        result = asyncio.run(splitter.run(text))
    else:
        result = asyncio.run(splitter.run(text))

    return [chunk.text for chunk in result.chunks]
