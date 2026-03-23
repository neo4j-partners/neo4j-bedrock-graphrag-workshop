from __future__ import annotations

"""
Shared configuration and utilities for workshop solutions.

This module provides common functionality for Neo4j connections,
LLM/embedder initialization, and configuration management.
Supports OpenAI, Azure AI Foundry, and AWS Bedrock embedding providers.

Embedding logic is delegated to ``src.embeddings`` to avoid duplication.
"""

import sys
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from financial_data_load directory
_root_env = Path(__file__).parent.parent / ".env"
load_dotenv(_root_env)

# Ensure src package is importable from solution_srcs context.
_src_parent = Path(__file__).resolve().parent.parent
if str(_src_parent) not in sys.path:
    sys.path.insert(0, str(_src_parent))


class Neo4jConfig(BaseSettings):
    """Neo4j configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    uri: str = Field(validation_alias="NEO4J_URI")
    username: str = Field(validation_alias="NEO4J_USERNAME")
    password: str = Field(validation_alias="NEO4J_PASSWORD")


# Re-export AgentConfig from the canonical location so solution files
# that do ``from config import AgentConfig`` keep working.
from src.config import AgentConfig  # noqa: E402


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


def get_agent_config() -> AgentConfig:
    """Get agent configuration from environment."""
    return AgentConfig()


def _get_azure_token() -> str:
    """Get Azure token for cognitive services.

    Delegates to src.embeddings.azure for the actual implementation.
    Kept here for backward compatibility with solution files that import it.
    """
    from src.embeddings.azure import get_azure_token
    return get_azure_token()


def get_embedder():
    """Get embedder for the configured EMBEDDING_PROVIDER.

    Delegates to src.embeddings which picks the right backend.
    """
    from src.embeddings import get_embedder as _get_embedder
    return _get_embedder()


def get_llm():
    """Get LLM configured from environment (OpenAI or Azure AI Foundry)."""
    from neo4j_graphrag.llm import OpenAILLM

    config = get_agent_config()

    if config.use_openai:
        return OpenAILLM(
            model_name=config.model_name,
            api_key=config.openai_api_key,
        )

    token = _get_azure_token()
    return OpenAILLM(
        model_name=config.model_name,
        base_url=config.inference_endpoint,
        api_key=token,
    )
