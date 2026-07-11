"""Lightweight data utilities for Lab 6 notebooks.

Provides only the Bedrock embedding function needed by the Lab 6 MCP-based
search notebooks.  No neo4j or neo4j-graphrag dependencies.
"""

import json
from pathlib import Path

import boto3
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load configuration from project root (lib/ -> Lab_6_MCP_Server/ -> project root)
_config_file = Path(__file__).parent.parent.parent / "CONFIG.txt"
load_dotenv(_config_file)

# Also load .env if it exists (for backward compatibility)
_env_file = Path(__file__).parent.parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=True)


class BedrockConfig(BaseSettings):
    """AWS Bedrock configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        validation_alias="MODEL_ID",
    )
    region: str = Field(default="us-east-1", validation_alias="REGION")
    embedding_dimensions: int = Field(default=1024, validation_alias="EMBEDDING_DIMENSIONS")


_bedrock_client = None


def get_embedding(text: str) -> list[float]:
    """Generate an embedding vector for text using Bedrock Titan Text Embeddings V2.

    Returns the raw float array for use in Cypher vector search queries.
    """
    global _bedrock_client
    config = BedrockConfig()
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-runtime", region_name=config.region)
    request_body = {
        "inputText": text,
        "dimensions": config.embedding_dimensions,
        "normalize": True,
    }
    response = _bedrock_client.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps(request_body),
    )
    result = json.loads(response["body"].read())
    return result["embedding"]
