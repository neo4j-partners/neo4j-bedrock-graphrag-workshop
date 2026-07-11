"""Bedrock Titan embedding provider.

Usage:
    from src.embeddings import get_embedder, get_embedding_dimensions
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo4j_graphrag.embeddings import Embedder


def get_embedder() -> Embedder:
    """Get a BedrockEmbeddings (Titan Text Embeddings V2) instance."""
    from .bedrock import create_embedder

    return create_embedder()


def get_embedding_dimensions() -> int:
    """Get the embedding vector dimensions.

    Returns the explicit EMBEDDING_DIMENSIONS if set, otherwise defaults
    to 1024. Titan Text Embeddings V2 supports 256, 512, or 1024; 1024
    matches the existing vector indexes.
    """
    from ..config import AgentConfig

    config = AgentConfig()
    if config.embedding_dimensions:
        return config.embedding_dimensions
    return 1024
