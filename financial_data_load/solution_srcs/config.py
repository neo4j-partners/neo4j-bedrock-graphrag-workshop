from __future__ import annotations

"""
Shared configuration and utilities for workshop solutions.

This module provides common functionality for Neo4j connections,
LLM/embedder initialization, and configuration management.
Uses AWS Bedrock for LLM and embedding services.
"""

import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import BedrockEmbeddings
from neo4j_graphrag.llm import BedrockLLM
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from financial_data_load directory.
# Override with ENV_FILE env var (e.g., ENV_FILE=.env.gold).
_env_name = os.environ.get("ENV_FILE", ".env")
_root_env = Path(__file__).parent.parent / _env_name
load_dotenv(_root_env, override=True)


class Neo4jConfig(BaseSettings):
    """Neo4j configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    uri: str = Field(validation_alias="NEO4J_URI")
    username: str = Field(validation_alias="NEO4J_USERNAME")
    password: str = Field(validation_alias="NEO4J_PASSWORD")


class BedrockConfig(BaseSettings):
    """AWS Bedrock configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-6",
        validation_alias="MODEL_ID",
    )
    region: str = Field(default="us-east-1", validation_alias="AWS_REGION")
    embedding_dimensions: int = Field(
        default=1024, validation_alias="EMBEDDING_DIMENSIONS"
    )


@contextmanager
def get_neo4j_driver():
    """Context manager for Neo4j driver connection."""
    config = Neo4jConfig()
    driver = GraphDatabase.driver(
        config.uri,
        auth=(config.username, config.password),
    )
    try:
        yield driver
    finally:
        driver.close()


def get_embedder() -> BedrockEmbeddings:
    """Get embedder using AWS Bedrock Titan Text Embeddings V2.

    Returns a BedrockEmbeddings object for use with neo4j-graphrag retrievers.
    Titan Text Embeddings V2 outputs 1024-dimensional vectors by default,
    matching the chunkEmbeddings vector index.
    """
    config = BedrockConfig()

    return BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v2:0",
        region_name=config.region,
    )


def get_llm() -> BedrockLLM:
    """Get LLM using AWS Bedrock."""
    config = BedrockConfig()

    return BedrockLLM(
        model_name=config.model_id,
        region_name=config.region,
    )


