"""AWS Bedrock embedding provider using neo4j-graphrag."""

from __future__ import annotations


def _is_nova_model(model_id: str) -> bool:
    """Return True if the model ID refers to a Nova embeddings model."""
    return "nova" in model_id.lower() and "embed" in model_id.lower()


def create_embedder():
    """Create a Bedrock embedder via neo4j-graphrag.

    Automatically selects BedrockNovaEmbeddings or BedrockEmbeddings (Titan)
    based on the EMBEDDING_MODEL_ID in .env.

    Reads AWS_REGION, EMBEDDING_MODEL_ID, and EMBEDDING_DIMENSIONS from .env
    via AgentConfig. AWS credentials are resolved by the default boto3
    credential chain.
    """
    from ..config import AgentConfig

    config = AgentConfig()
    model_id = config.embedding_model_id or ""

    if _is_nova_model(model_id):
        from neo4j_graphrag.embeddings import BedrockNovaEmbeddings

        kwargs: dict = {}
        if config.aws_region:
            kwargs["region_name"] = config.aws_region
        if model_id:
            kwargs["model_id"] = model_id
        if config.embedding_dimensions:
            kwargs["embedding_dimension"] = config.embedding_dimensions
        return BedrockNovaEmbeddings(**kwargs)
    else:
        from neo4j_graphrag.embeddings import BedrockEmbeddings

        kwargs = {}
        if config.aws_region:
            kwargs["region_name"] = config.aws_region
        if model_id:
            kwargs["model_id"] = model_id
        return BedrockEmbeddings(**kwargs)
