"""
Configuration module for Neo4j and AWS Bedrock integration.

This module provides:
- Environment configuration loading
- Bedrock client initialization
- BedrockEmbedder class for neo4j-graphrag compatibility
- BedrockLLM class for neo4j-graphrag compatibility
- Neo4j driver initialization
"""

import json
import os
from typing import Any

import boto3
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import Embedder
from neo4j_graphrag.llm import LLMInterface, LLMResponse
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()


class AWSConfig(BaseModel):
    """AWS configuration settings.

    Model IDs:
    - Claude 3.5 Sonnet v2: anthropic.claude-3-5-sonnet-20241022-v2:0 (default, widely available)
    - Claude Sonnet 4: anthropic.claude-sonnet-4-20250514-v1:0 (latest, may require access)
    - Titan Embeddings V2: amazon.titan-embed-text-v2:0 (1024 dimensions)
    """

    region: str = os.getenv("AWS_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv(
        "AWS_BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"
    )
    bedrock_embedding_model_id: str = os.getenv(
        "AWS_BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"
    )
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))


class Neo4jConfig(BaseModel):
    """Neo4j configuration settings."""

    uri: str = os.getenv("NEO4J_URI", "")
    username: str = os.getenv("NEO4J_USERNAME", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "")
    vector_index_name: str = os.getenv("NEO4J_VECTOR_INDEX_NAME", "chunkEmbeddings")


# Global configuration instances
aws_config = AWSConfig()
neo4j_config = Neo4jConfig()


def get_bedrock_client():
    """Get a Bedrock Runtime client for model invocation."""
    return boto3.client("bedrock-runtime", region_name=aws_config.region)


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


class BedrockEmbedder(Embedder):
    """
    Embedder implementation using Amazon Titan Text Embeddings V2.

    This class implements the neo4j-graphrag Embedder interface,
    allowing it to be used with VectorRetriever and other GraphRAG components.
    """

    def __init__(
        self,
        model_id: str | None = None,
        dimensions: int | None = None,
        normalize: bool = True,
    ):
        """
        Initialize the Bedrock embedder.

        Args:
            model_id: Bedrock embedding model ID. Defaults to Titan Embeddings V2.
            dimensions: Output embedding dimensions (256, 512, or 1024 for Titan V2).
            normalize: Whether to normalize embeddings. Defaults to True.
        """
        self.client = get_bedrock_client()
        self.model_id = model_id or aws_config.bedrock_embedding_model_id
        self.dimensions = dimensions or aws_config.embedding_dimensions
        self.normalize = normalize

    def embed_query(self, text: str) -> list[float]:
        """
        Generate embeddings for a single query text.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        request_body = {
            "inputText": text,
            "dimensions": self.dimensions,
            "normalize": self.normalize,
        }

        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body),
        )

        response_body = json.loads(response["body"].read())
        return response_body["embedding"]


class BedrockLLM(LLMInterface):
    """
    LLM implementation using Amazon Bedrock Converse API.

    This class implements the neo4j-graphrag LLMInterface,
    allowing it to be used with Text2CypherRetriever and other GraphRAG components.
    The Converse API provides a unified interface for all Bedrock models.
    """

    def __init__(
        self,
        model_id: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ):
        """
        Initialize the Bedrock LLM.

        Args:
            model_id: Bedrock model ID. Defaults to Claude 3.5 Sonnet.
            temperature: Sampling temperature (0.0 = deterministic).
            max_tokens: Maximum tokens in response.
        """
        self.client = get_bedrock_client()
        self.model_id = model_id or aws_config.bedrock_model_id
        self.temperature = temperature
        self.max_tokens = max_tokens

    def invoke(self, input: str) -> LLMResponse:
        """
        Invoke the LLM with a text prompt.

        Args:
            input: The prompt text.

        Returns:
            LLMResponse containing the model's response.
        """
        messages = [{"role": "user", "content": [{"text": input}]}]

        response = self.client.converse(
            modelId=self.model_id,
            messages=messages,
            inferenceConfig={
                "temperature": self.temperature,
                "maxTokens": self.max_tokens,
            },
        )

        # Extract text from response
        output_message = response["output"]["message"]
        response_text = ""
        for content_block in output_message["content"]:
            if "text" in content_block:
                response_text += content_block["text"]

        return LLMResponse(content=response_text)

    async def ainvoke(self, input: str) -> LLMResponse:
        """
        Async version of invoke. Currently wraps the sync version.

        Args:
            input: The prompt text.

        Returns:
            LLMResponse containing the model's response.
        """
        return self.invoke(input)


def get_embedder(
    model_id: str | None = None,
    dimensions: int | None = None,
    normalize: bool = True,
) -> BedrockEmbedder:
    """
    Get a BedrockEmbedder instance.

    Args:
        model_id: Optional model ID override.
        dimensions: Optional dimensions override.
        normalize: Whether to normalize embeddings.

    Returns:
        Configured BedrockEmbedder instance.
    """
    return BedrockEmbedder(
        model_id=model_id,
        dimensions=dimensions,
        normalize=normalize,
    )


def get_llm(
    model_id: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> BedrockLLM:
    """
    Get a BedrockLLM instance.

    Args:
        model_id: Optional model ID override.
        temperature: Sampling temperature.
        max_tokens: Maximum response tokens.

    Returns:
        Configured BedrockLLM instance.
    """
    return BedrockLLM(
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
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
