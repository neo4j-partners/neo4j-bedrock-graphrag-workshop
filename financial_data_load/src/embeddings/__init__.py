"""Bedrock embedding provider.

Usage:
    from src.embeddings import get_embedder, get_embedding_dimensions
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo4j_graphrag.embeddings import Embedder


def get_embedder() -> Embedder:
    """Get a BedrockEmbeddings instance."""
    from .bedrock import create_embedder

    return create_embedder()


def get_embedding_dimensions() -> int:
    """Get the embedding vector dimensions.

    Returns the explicit EMBEDDING_DIMENSIONS if set, otherwise infers
    from the model: 1024 for Titan, 1024 for Nova (Nova default is 3072
    but we use 1024 to match existing vector indexes).
    """
    from ..config import AgentConfig

    config = AgentConfig()
    if config.embedding_dimensions:
        return config.embedding_dimensions
    return 1024
