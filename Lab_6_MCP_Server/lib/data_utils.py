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

# Load configuration. Local runs use the project-root .env; the workshop uses
# CONFIG.txt; the test harness falls back to financial_data_load/.env. Exactly
# one source is authoritative per run.
_root = Path(__file__).resolve().parents[2]
_env_file = _root / ".env"
_config_file = _root / "CONFIG.txt"
_fallback_env = _root / "financial_data_load" / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
elif _config_file.exists():
    load_dotenv(_config_file)
elif _fallback_env.exists():
    load_dotenv(_fallback_env)
else:
    raise FileNotFoundError(
        f"No config found. Expected {_env_file} (local), {_config_file} "
        f"(workshop), or {_fallback_env} (test harness)."
    )


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
