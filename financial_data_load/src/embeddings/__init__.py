"""Modular embedding provider system.

Picks the right embedding backend based on the EMBEDDING_PROVIDER env var.

Usage:
    from src.embeddings import get_embedder, get_embedding_dimensions
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo4j_graphrag.embeddings import Embedder

_SUPPORTED_PROVIDERS = ("openai", "azure", "bedrock")


def _resolve_provider() -> str:
    """Return the configured EMBEDDING_PROVIDER, or raise."""
    from ..config import AgentConfig

    config = AgentConfig()

    if not config.embedding_provider:
        raise ValueError(
            "EMBEDDING_PROVIDER is required in .env. "
            f"Supported values: {', '.join(_SUPPORTED_PROVIDERS)}"
        )

    provider = config.embedding_provider.lower()
    if provider not in _SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unknown EMBEDDING_PROVIDER: {provider!r}. "
            f"Supported: {', '.join(_SUPPORTED_PROVIDERS)}"
        )

    return provider


def get_embedder() -> Embedder:
    """Get an embedder instance for the configured EMBEDDING_PROVIDER."""
    provider = _resolve_provider()

    if provider == "openai":
        from .openai import create_embedder
        return create_embedder()

    if provider == "azure":
        from .azure import create_embedder
        return create_embedder()

    if provider == "bedrock":
        from .bedrock import create_embedder
        return create_embedder()

    # _resolve_provider already validates, so this is unreachable
    raise AssertionError(f"unhandled provider: {provider!r}")


def get_embedding_dimensions() -> int:
    """Get the embedding vector dimensions from config.

    Returns the explicit EMBEDDING_DIMENSIONS if set, otherwise a
    sensible default based on the provider.
    """
    from ..config import AgentConfig

    config = AgentConfig()

    if config.embedding_dimensions:
        return config.embedding_dimensions

    # Provider-specific defaults
    provider = _resolve_provider()
    defaults = {
        "openai": 1536,
        "azure": 1536,
        "bedrock": 1024,
    }
    return defaults.get(provider, 1536)
