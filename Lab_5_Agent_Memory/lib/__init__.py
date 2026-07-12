"""Shared utilities for Lab 5 (Agent Memory).

Kept as a lightweight package on purpose: nothing is imported eagerly here so
that ``import lib`` does not pull in ``neo4j_agent_memory`` before the notebook's
``%pip install`` cell has run. Import the submodules directly instead:

    from lib.data_utils import get_llm
    from lib.memory_utils import build_memory_client
"""
