# ---------------------------------------------------------------------------
# Neo4j Agent Memory setup helpers for Lab 5.
#
# Builds a MemoryClient over the SAME Aura instance and Titan Text Embeddings V2
# the earlier labs use, so memory nodes land beside the SEC 10-K graph.
#
# Kept separate from data_utils.py on purpose: that file is a verbatim copy of
# the shared helper (see its header) and must stay in sync with the root copy,
# so the neo4j-agent-memory dependency lives here instead. The memory SDK also
# ships its own ``Neo4jConfig``; it is aliased ``MemoryNeo4jConfig`` below to
# avoid clashing with ``data_utils.Neo4jConfig``.
# ---------------------------------------------------------------------------

"""MemorySettings / MemoryClient construction for the Lab 5 notebooks."""

from __future__ import annotations

from neo4j_agent_memory import EmbeddingConfig, EmbeddingProvider, MemoryClient, MemorySettings
from neo4j_agent_memory import Neo4jConfig as MemoryNeo4jConfig
from neo4j_agent_memory.config.settings import ExtractionConfig, ExtractorType
from pydantic import SecretStr

from lib.data_utils import BedrockConfig, Neo4jConfig

TITAN_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"


def build_memory_settings() -> MemorySettings:
    """Assemble ``MemorySettings`` for the bolt (direct-driver) path against Aura.

    Embedding-only configuration: Titan V2 supplies the vectors, no LLM is
    constructed, and entity extraction is turned off. The Lab 5 notebooks write
    memory explicitly (``add_message`` / ``add_entity`` / ``add_fact`` /
    ``add_preference``), so ``ExtractorType.NONE`` keeps the LLM surface off
    entirely. Nothing in the core path needs to call a model to extract
    entities from text.

    Returns:
        A ``MemorySettings`` ready to hand to ``MemoryClient``.
    """
    neo4j_cfg = Neo4jConfig()
    bedrock_cfg = BedrockConfig()

    # Configure the embedder via EmbeddingConfig with an explicit aws_region so
    # the region comes from CONFIG.txt's REGION key, the same key every other
    # lab uses. The "bedrock/<model>" provider-string shorthand would instead
    # read AWS_REGION, which the workshop CONFIG.txt does not set. dimensions is
    # pinned to Titan V2's 1024 (EmbeddingConfig defaults to OpenAI's 1536) so
    # the memory vector index matches the vectors Titan actually produces.
    embedding = EmbeddingConfig(
        provider=EmbeddingProvider.BEDROCK,
        model=TITAN_EMBEDDING_MODEL,
        dimensions=bedrock_cfg.embedding_dimensions,
        aws_region=bedrock_cfg.region,
    )

    return MemorySettings(
        neo4j=MemoryNeo4jConfig(
            uri=neo4j_cfg.uri,
            username=neo4j_cfg.username,
            password=SecretStr(neo4j_cfg.password),
        ),
        embedding=embedding,
        extraction=ExtractionConfig(extractor_type=ExtractorType.NONE),
    )


def build_memory_client() -> MemoryClient:
    """Construct an unconnected ``MemoryClient`` for the shared memory settings.

    Returned unconnected because ``connect()`` is a coroutine. Open it in a
    notebook with::

        memory = build_memory_client()
        await memory.connect()

    and release it with ``await memory.close()``.

    Returns:
        A ``MemoryClient`` bound to the shared ``MemorySettings``.
    """
    return MemoryClient(build_memory_settings())
