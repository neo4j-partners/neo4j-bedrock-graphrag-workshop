# ---------------------------------------------------------------------------
# COPIED from root lib/data_utils.py to simplify imports from Lab_4 notebooks.
# Loads CONFIG.txt from the project root (two levels up from this file).
#
# If you change this file, update the root lib/data_utils.py as well.
# If you change the root lib/data_utils.py, update this file as well.
# ---------------------------------------------------------------------------

"""Utilities for data loading, Neo4j operations, and AWS Bedrock AI services."""

import asyncio
import json
from pathlib import Path

import boto3
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import BedrockNovaEmbeddings
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.llm import BedrockLLM
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load configuration from project root (lib/ -> Lab_4_Graph_Enriched_Search/ -> project root)
_config_file = Path(__file__).parent.parent.parent / "CONFIG.txt"
load_dotenv(_config_file)

# Also load .env if it exists (for backward compatibility)
_env_file = Path(__file__).parent.parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=True)


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
    For raw float arrays (e.g., for Cypher queries), use get_embedding() instead.
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


class _NovaEmbedding(BaseModel):
    embedding: list[float]


class _NovaEmbeddingResponse(BaseModel):
    embeddings: list[_NovaEmbedding]


_bedrock_client = None


def get_embedding(text: str) -> list[float]:
    """Generate an embedding vector for text using Bedrock Nova.

    Returns the raw float array for use in Cypher vector search queries.
    Unlike get_embedder(), this returns floats directly rather than a
    BedrockNovaEmbeddings object.
    """
    global _bedrock_client
    config = BedrockConfig()
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-runtime", region_name=config.region)
    request_body = {
        "taskType": "SINGLE_EMBEDDING",
        "singleEmbeddingParams": {
            "embeddingPurpose": "GENERIC_INDEX",
            "embeddingDimension": config.embedding_dimensions,
            "text": {
                "truncationMode": "END",
                "value": text,
            },
        },
    }
    response = _bedrock_client.invoke_model(
        modelId="amazon.nova-2-multimodal-embeddings-v1:0",
        body=json.dumps(request_body),
    )
    result = json.loads(response["body"].read())
    parsed = _NovaEmbeddingResponse.model_validate(result)
    return parsed.embeddings[0].embedding


def get_schema(driver) -> str:
    """Get the schema of the Neo4j database.

    Args:
        driver: Neo4j driver instance.

    Returns:
        String representation of the database schema.
    """
    with driver.session() as session:
        node_result = session.run(
            """
            CALL db.schema.nodeTypeProperties()
            YIELD nodeType, propertyName, propertyTypes
            WITH nodeType, collect({property: propertyName, types: propertyTypes}) as properties
            RETURN nodeType, properties
            """
        )
        nodes = {record["nodeType"]: record["properties"] for record in node_result}

        rel_result = session.run(
            """
            CALL db.schema.relTypeProperties()
            YIELD relType, propertyName, propertyTypes
            WITH relType, collect({property: propertyName, types: propertyTypes}) as properties
            RETURN relType, properties
            """
        )
        relationships = {record["relType"]: record["properties"] for record in rel_result}

    schema_parts = ["Node Labels and Properties:"]
    for node_type, props in nodes.items():
        prop_str = ", ".join([f"{p['property']}: {p['types']}" for p in props if p["property"]])
        schema_parts.append(f"  {node_type}: {prop_str if prop_str else 'no properties'}")

    schema_parts.append("\nRelationship Types and Properties:")
    for rel_type, props in relationships.items():
        prop_str = ", ".join([f"{p['property']}: {p['types']}" for p in props if p["property"]])
        schema_parts.append(f"  {rel_type}: {prop_str if prop_str else 'no properties'}")

    return "\n".join(schema_parts)


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
