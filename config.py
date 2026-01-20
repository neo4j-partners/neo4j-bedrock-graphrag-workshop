"""
Configuration module for Neo4j and AWS Bedrock integration.

This module provides:
- Environment configuration loading using pydantic-settings
- Neo4j driver initialization
- Bedrock LLM and Embedder access via neo4j-graphrag native classes

The neo4j-graphrag library now includes native Bedrock support through:
- neo4j_graphrag.embeddings.BedrockEmbeddings
- neo4j_graphrag.llm.BedrockLLM

These use boto3's default credential chain and support inference profiles
for cross-region access to newer Claude models.
"""

from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import BedrockEmbeddings
from neo4j_graphrag.llm import BedrockLLM
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from project root
_root_env = Path(__file__).parent / ".env"
load_dotenv(_root_env)


class Neo4jConfig(BaseSettings):
    """Neo4j configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    uri: str = Field(validation_alias="NEO4J_URI")
    username: str = Field(default="neo4j", validation_alias="NEO4J_USERNAME")
    password: str = Field(validation_alias="NEO4J_PASSWORD")
    vector_index_name: str = Field(
        default="chunkEmbeddings", validation_alias="NEO4J_VECTOR_INDEX_NAME"
    )


class AWSConfig(BaseSettings):
    """AWS Bedrock configuration loaded from environment variables.

    Model IDs and Inference Profiles:
    - Claude Sonnet 4.5: us.anthropic.claude-sonnet-4-5-20250929-v1:0 (inference profile)
    - Claude 3.5 Sonnet v2: anthropic.claude-3-5-sonnet-20241022-v2:0 (direct model ID)
    - Titan Embeddings V2: amazon.titan-embed-text-v2:0 (1024 dimensions default)

    Note: Newer Claude models require inference profiles for cross-region access.
    See: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html
    """

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    region: str = Field(default="us-east-1", validation_alias="AWS_REGION")
    # Claude Sonnet 4.5 US cross-region inference profile
    bedrock_inference_profile_id: str = Field(
        default="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        validation_alias="AWS_BEDROCK_INFERENCE_PROFILE_ID",
    )
    bedrock_embedding_model_id: str = Field(
        default="amazon.titan-embed-text-v2:0",
        validation_alias="AWS_BEDROCK_EMBEDDING_MODEL_ID",
    )
    embedding_dimensions: int = Field(
        default=1024, validation_alias="EMBEDDING_DIMENSIONS"
    )


# Global configuration instances
neo4j_config = Neo4jConfig()
aws_config = AWSConfig()


def get_neo4j_driver():
    """Get a Neo4j driver instance."""
    if not neo4j_config.uri or not neo4j_config.password:
        raise ValueError(
            "NEO4J_URI and NEO4J_PASSWORD must be set in environment variables or .env file"
        )
    return GraphDatabase.driver(
        neo4j_config.uri,
        auth=(neo4j_config.username, neo4j_config.password),
    )


def get_embedder() -> BedrockEmbeddings:
    """
    Get a BedrockEmbeddings instance using neo4j-graphrag native support.

    Uses boto3's default credential chain (env vars, ~/.aws/credentials, IAM role).
    Returns BedrockEmbeddings configured for Amazon Titan Text Embeddings V2.

    Returns:
        Configured BedrockEmbeddings instance with 1024 dimensions.
    """
    return BedrockEmbeddings(
        model_id=aws_config.bedrock_embedding_model_id,
        region_name=aws_config.region,
    )


def get_llm() -> BedrockLLM:
    """
    Get a BedrockLLM instance using neo4j-graphrag native support.

    Uses boto3's default credential chain (env vars, ~/.aws/credentials, IAM role).
    Returns BedrockLLM configured for Claude Sonnet 4.5 via the Converse API
    with US cross-region inference profile.

    Returns:
        Configured BedrockLLM instance.
    """
    return BedrockLLM(
        inference_profile_id=aws_config.bedrock_inference_profile_id,
        region_name=aws_config.region,
    )


def get_schema(driver) -> str:
    """
    Get the schema of the Neo4j database.

    Args:
        driver: Neo4j driver instance.

    Returns:
        String representation of the database schema.
    """
    with driver.session() as session:
        # Get node labels and their properties
        node_result = session.run(
            """
            CALL db.schema.nodeTypeProperties()
            YIELD nodeType, propertyName, propertyTypes
            RETURN nodeType, collect({property: propertyName, types: propertyTypes}) as properties
            """
        )
        nodes = {record["nodeType"]: record["properties"] for record in node_result}

        # Get relationship types and their properties
        rel_result = session.run(
            """
            CALL db.schema.relTypeProperties()
            YIELD relType, propertyName, propertyTypes
            RETURN relType, collect({property: propertyName, types: propertyTypes}) as properties
            """
        )
        relationships = {record["relType"]: record["properties"] for record in rel_result}

    schema_parts = ["Node Labels and Properties:"]
    for node_type, props in nodes.items():
        prop_str = ", ".join([f"{p['property']}: {p['types']}" for p in props if p["property"]])
        schema_parts.append(f"  {node_type}: {prop_str if prop_str else 'no properties'}")

    schema_parts.append("\nRelationship Types and Properties:")
    for rel_type, props in relationships.items():
        prop_str = ", ".join([f"{p['property']}: {p['types']}" for p in props if p["property"]])
        schema_parts.append(f"  {rel_type}: {prop_str if prop_str else 'no properties'}")

    return "\n".join(schema_parts)
