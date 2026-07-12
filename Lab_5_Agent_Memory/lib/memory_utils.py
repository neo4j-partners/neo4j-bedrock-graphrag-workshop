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

import logging

from neo4j_agent_memory import EmbeddingConfig, EmbeddingProvider, MemoryClient, MemorySettings
from neo4j_agent_memory import Neo4jConfig as MemoryNeo4jConfig
from neo4j_agent_memory.config.settings import ExtractionConfig, ExtractorType
from neo4j_agent_memory.embeddings.bedrock import BedrockEmbedder
from pydantic import SecretStr

from lib.data_utils import BedrockConfig, Neo4jConfig

TITAN_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"

# Silence Neo4j server-notification logging. neo4j-agent-memory issues vector
# recall via db.index.vector.queryNodes, which Aura now flags as deprecated; the
# driver logs one WARNING-level notification per call to the "neo4j.notifications"
# logger (neo4j/_async/work/result.py). The Cypher lives inside the memory SDK and
# MemoryClient builds its own driver, so we cannot rewrite the query or pass
# driver-level notification filters from here. Raising just this logger's level to
# ERROR drops the deprecation noise from the notebook output while leaving genuine
# errors intact.
logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)


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

    The ``EmbeddingConfig`` in ``build_memory_settings`` only sizes the vector
    index; in neo4j-agent-memory 0.5.0 the client builds a concrete embedder
    from that config for OpenAI and sentence-transformers only, and returns
    ``None`` for every other provider, including Bedrock. Left that way, the
    client has no embedder, ``generate_embedding=True`` silently writes vectors
    of length zero, and semantic recall (``search_entities`` /
    ``long_term.get_context``) finds nothing. So the Bedrock embedder is
    constructed explicitly here and passed via ``embedder=``, which the client
    adopts directly.

    Returns:
        A ``MemoryClient`` bound to the shared ``MemorySettings`` with a working
        Bedrock embedder.
    """
    bedrock_cfg = BedrockConfig()
    embedder = BedrockEmbedder(
        model=TITAN_EMBEDDING_MODEL,
        region_name=bedrock_cfg.region,
    )
    return MemoryClient(build_memory_settings(), embedder=embedder)
