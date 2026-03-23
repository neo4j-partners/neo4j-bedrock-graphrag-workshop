"""
Configuration for the graphrag-validator CLI (Lab 6 validation).

Loads settings from environment variables with fallback to CONFIG.txt
at the repository root.
"""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve CONFIG.txt at repo root (setup/solutions_bedrock/../../CONFIG.txt)
_config_file = Path(__file__).resolve().parents[4] / "CONFIG.txt"
load_dotenv(_config_file)

_env_file = Path(__file__).resolve().parents[4] / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=True)


class Settings(BaseSettings):
    """Settings for GraphRAG validation."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    neo4j_uri: str = Field(validation_alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", validation_alias="NEO4J_USERNAME")
    neo4j_password: str = Field(validation_alias="NEO4J_PASSWORD")
    model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        validation_alias="MODEL_ID",
    )
    embedding_model_id: str = Field(
        default="amazon.titan-embed-text-v2:0",
        validation_alias="EMBEDDING_MODEL_ID",
    )
    region: str = Field(default="us-east-1", validation_alias="REGION")
    data_dir: str = Field(default="TransformedData/", validation_alias="DATA_DIR")

    @property
    def resolved_data_dir(self) -> Path:
        """Return data_dir as an absolute path, resolved relative to the repo root."""
        p = Path(self.data_dir)
        if p.is_absolute():
            return p
        return Path(__file__).resolve().parents[4] / p
