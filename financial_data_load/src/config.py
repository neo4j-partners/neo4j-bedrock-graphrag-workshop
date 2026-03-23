"""Configuration, authentication, and Neo4j connection management."""

from __future__ import annotations

import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from pydantic import Field, SecretStr, model_validator
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

    Uses AWS Bedrock for both LLM and embeddings.
    """

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # --- AWS Bedrock settings ---
    aws_region: str | None = Field(
        default=None, validation_alias="AWS_REGION",
    )
    llm_model_id: str | None = Field(
        default=None, validation_alias="MODEL_ID",
    )
    embedding_model_id: str | None = Field(
        default=None, validation_alias="EMBEDDING_MODEL_ID",
    )
    embedding_dimensions: int | None = Field(
        default=None, validation_alias="EMBEDDING_DIMENSIONS",
    )


# ---------------------------------------------------------------------------
# LLM and embedder factories
# ---------------------------------------------------------------------------


def get_llm():
    """Get a BedrockLLM instance. Requires MODEL_ID in .env."""
    from neo4j_graphrag.llm import BedrockLLM

    config = AgentConfig()
    if not config.llm_model_id:
        raise ValueError("MODEL_ID must be set in .env.")
    kwargs: dict = {"model_id": config.llm_model_id}
    if config.aws_region:
        kwargs["region_name"] = config.aws_region
    return BedrockLLM(**kwargs)


def get_llm_deterministic():
    """Get a BedrockLLM with temperature=0 for deterministic output.

    Used by entity resolution, validation, and normalization phases
    where reproducible results are important.
    """
    from neo4j_graphrag.llm import BedrockLLM

    config = AgentConfig()
    if not config.llm_model_id:
        raise ValueError("MODEL_ID must be set in .env.")
    kwargs: dict = {
        "model_id": config.llm_model_id,
        "model_params": {"temperature": 0},
    }
    if config.aws_region:
        kwargs["region_name"] = config.aws_region
    return BedrockLLM(**kwargs)


def get_embedder():
    """Get a BedrockEmbeddings instance."""
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
