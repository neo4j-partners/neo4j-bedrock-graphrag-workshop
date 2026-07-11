"""AWS Bedrock Titan embedding provider using neo4j-graphrag."""

from __future__ import annotations


def create_embedder():
    """Create a BedrockEmbeddings instance via neo4j-graphrag.

    Uses Amazon Titan Text Embeddings V2, which outputs 1024-dimensional
    vectors by default. Reads AWS_REGION from .env via AgentConfig; AWS
    credentials are resolved by the default boto3 credential chain.
    """
    from neo4j_graphrag.embeddings import BedrockEmbeddings

    from ..config import AgentConfig

    config = AgentConfig()

    kwargs: dict = {"model_id": "amazon.titan-embed-text-v2:0"}
    if config.aws_region:
        kwargs["region_name"] = config.aws_region
    return BedrockEmbeddings(**kwargs)
