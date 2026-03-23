"""Configuration, authentication, and Neo4j connection management."""

from __future__ import annotations

import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from pydantic import Field, SecretStr, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolved once at import time -- stable regardless of cwd.
_PKG_DIR = Path(__file__).resolve().parent
_ENV_FILE = _PKG_DIR.parent / ".env"

load_dotenv(_ENV_FILE)


class Neo4jConfig(BaseSettings):
    """Neo4j connection settings loaded from .env."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    uri: str = Field(validation_alias="NEO4J_URI")
    username: str = Field(validation_alias="NEO4J_USERNAME")
    password: SecretStr = Field(validation_alias="NEO4J_PASSWORD")

    @model_validator(mode="after")
    def _check_uri_scheme(self) -> Neo4jConfig:
        valid = ("neo4j://", "neo4j+s://", "neo4j+ssc://",
                 "bolt://", "bolt+s://", "bolt+ssc://")
        if not self.uri.startswith(valid):
            raise ValueError(
                f"NEO4J_URI must start with a valid scheme "
                f"(neo4j+s://, bolt+s://, etc.), got: {self.uri}"
            )
        return self


class AgentConfig(BaseSettings):
    """LLM and embedding configuration loaded from .env.

    Requires EMBEDDING_PROVIDER to select the embedding backend:
    - openai: uses OPENAI_API_KEY
    - azure: uses AZURE_AI_PROJECT_ENDPOINT (+ az login)
    - bedrock: uses AWS credential chain
    """

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    openai_api_key: str | None = Field(
        default=None, validation_alias="OPENAI_API_KEY"
    )
    project_endpoint: str | None = Field(
        default=None, validation_alias="AZURE_AI_PROJECT_ENDPOINT"
    )
    model_name: str = Field(
        default="gpt-4o",
        validation_alias="AZURE_AI_MODEL_NAME",
    )
    embedding_name: str = Field(
        default="text-embedding-3-small",
        validation_alias="AZURE_AI_EMBEDDING_NAME",
    )

    # --- Embedding provider settings (required) ---
    embedding_provider: str = Field(
        validation_alias="EMBEDDING_PROVIDER",
    )
    embedding_dimensions: int | None = Field(
        default=None, validation_alias="EMBEDDING_DIMENSIONS",
    )

    @computed_field
    @property
    def inference_endpoint(self) -> str | None:
        """Get the model inference endpoint from project endpoint."""
        if not self.project_endpoint:
            return None
        if "/api/projects/" in self.project_endpoint:
            base = self.project_endpoint.split("/api/projects/")[0]
            return f"{base}/models"
        return self.project_endpoint

    @property
    def use_openai(self) -> bool:
        """True when using OpenAI directly instead of Azure."""
        return self.openai_api_key is not None


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def get_azure_token() -> str:
    """Get Azure token for cognitive services.

    Delegates to the Azure embedding provider module.
    Kept here for backward compatibility with code that imports it directly.
    """
    from .embeddings.azure import get_azure_token as _get_azure_token

    return _get_azure_token()


# ---------------------------------------------------------------------------
# LLM and embedder factories
# ---------------------------------------------------------------------------


def get_llm():
    """Get LLM configured from environment (OpenAI or Azure AI Foundry)."""
    from neo4j_graphrag.llm import OpenAILLM

    config = AgentConfig()

    if config.use_openai:
        return OpenAILLM(
            model_name=config.model_name,
            api_key=config.openai_api_key,
        )

    token = get_azure_token()
    return OpenAILLM(
        model_name=config.model_name,
        base_url=config.inference_endpoint,
        api_key=token,
    )


def get_embedder():
    """Get embedder for the configured EMBEDDING_PROVIDER.

    Delegates to src.embeddings which picks the right backend.
    """
    from .embeddings import get_embedder as _get_embedder

    return _get_embedder()


# ---------------------------------------------------------------------------
# Neo4j connection
# ---------------------------------------------------------------------------


@contextmanager
def connect() -> Generator[Driver, None, None]:
    """Create a Neo4j driver, verify connectivity, and close on exit."""
    config = Neo4jConfig()
    driver = GraphDatabase.driver(
        config.uri,
        auth=(config.username, config.password.get_secret_value()),
    )
    try:
        driver.verify_connectivity()
    except (ServiceUnavailable, OSError) as exc:
        driver.close()
        print(f"[FAIL] Cannot connect to {config.uri}")
        print(f"       {exc}")
        print("\nCheck that the Neo4j instance is running and reachable.")
        sys.exit(1)
    try:
        print(f"[OK] Connected to {config.uri}\n")
        yield driver
    finally:
        driver.close()
