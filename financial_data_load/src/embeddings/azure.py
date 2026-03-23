"""Azure AI Foundry embedding provider (uses az login token auth)."""

from __future__ import annotations


def get_azure_token() -> str:
    """Get Azure token for cognitive services.

    Tries AzureCliCredential first (for Dev Containers after ``az login``),
    then falls back to DefaultAzureCredential for other environments.
    """
    from azure.identity import AzureCliCredential, DefaultAzureCredential

    scope = "https://cognitiveservices.azure.com/.default"

    try:
        credential = AzureCliCredential()
        return credential.get_token(scope).token
    except Exception:
        pass

    try:
        credential = DefaultAzureCredential()
        return credential.get_token(scope).token
    except Exception as e:
        raise RuntimeError(
            "Azure authentication failed. Please run:\n"
            "  az login --use-device-code\n"
            f"Original error: {e}"
        ) from e


def create_embedder():
    """Create an Azure AI Foundry embedder using az login credentials."""
    from neo4j_graphrag.embeddings import OpenAIEmbeddings

    from ..config import AgentConfig

    config = AgentConfig()

    if not config.project_endpoint:
        raise ValueError(
            "Azure provider requires AZURE_AI_PROJECT_ENDPOINT to be set."
        )

    token = get_azure_token()
    return OpenAIEmbeddings(
        model=config.embedding_name,
        base_url=config.inference_endpoint,
        api_key=token,
    )
