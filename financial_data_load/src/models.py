"""Shared Pydantic models for the financial data pipeline.

Centralizes types used across multiple modules to avoid circular imports
and provide strong type enforcement on plan files and data exchange.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Entity snapshot models (used by snapshot, entity_resolution, cleanse, validate)
# ---------------------------------------------------------------------------


class SnapshotEntity(BaseModel):
    """A single entity exported from Neo4j."""

    element_id: str
    name: str
    labels: list[str]
    properties: dict[str, Any]
    source_chunks: list[str]
    relationship_count: int


class EntitySnapshot(BaseModel):
    """Complete entity snapshot for a label group."""

    exported_at: str
    label: str
    entity_count: int
    entities: list[SnapshotEntity]


# ---------------------------------------------------------------------------
# Entity resolution models (used by entity_resolution, cleanse)
# ---------------------------------------------------------------------------


class MergeDecision(BaseModel):
    """LLM decision on whether two entities should be merged."""

    entity_a_name: str
    entity_a_element_id: str
    entity_b_name: str
    entity_b_element_id: str
    decision: str  # "merge" or "no_merge"
    confidence: float | None = None
    reasoning: str


class ResolutionResult(BaseModel):
    """Result of entity resolution for one label."""

    decisions: list[MergeDecision]
    merge_groups: list[dict[str, Any]]
    config: dict[str, Any]
    candidate_pairs: int


# ---------------------------------------------------------------------------
# Ground truth models (used by compare, cleanse)
# ---------------------------------------------------------------------------


class GroundTruthResult(BaseModel):
    """Single ground truth check result."""

    label: str
    passed: bool
    detail: str


# ---------------------------------------------------------------------------
# Cleanse plan models (used by cleanse, validate)
# ---------------------------------------------------------------------------


class RemovalDecision(BaseModel):
    """An entity marked for removal by the validation phase."""

    entity_type: str  # e.g. "Executive", "Product"
    element_id: str
    name: str
    company: str  # associated company for context
    reasoning: str


class DedupSection(BaseModel):
    """Deduplication results for one entity type."""

    label: str
    config: dict[str, Any]
    total_entities: int  # count after validation removals
    candidate_pairs: int
    decisions: list[MergeDecision]
    merge_groups: list[dict[str, Any]]


class GroundTruthScore(BaseModel):
    """Company ground truth regression check."""

    overall_score: str
    expected_merges: list[GroundTruthResult]
    forbidden_merges: list[GroundTruthResult]


class CleansePlan(BaseModel):
    """Complete cleanse plan — the review artifact."""

    created_at: str
    entity_counts: dict[str, int]  # label -> count before cleansing

    # Phase 1: Validation
    removals: list[RemovalDecision]

    # Phase 2: Deduplication (keyed by entity label)
    dedup_sections: dict[str, DedupSection]

    # Ground truth (Company only)
    ground_truth: GroundTruthScore | None = None
