"""OpenAI embedding provider (direct API key auth)."""

from __future__ import annotations


def create_embedder():
    """Create an OpenAI embedder using OPENAI_API_KEY."""
    from neo4j_graphrag.embeddings import OpenAIEmbeddings

    from ..config import AgentConfig

    config = AgentConfig()

    if not config.openai_api_key:
        raise ValueError(
            "OpenAI provider requires OPENAI_API_KEY to be set."
        )

    return OpenAIEmbeddings(
        model=config.embedding_name,
        api_key=config.openai_api_key,
    )
