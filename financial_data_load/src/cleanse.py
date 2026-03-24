"""Cleanse pipeline: validate, deduplicate, and normalize extracted entities.

Two commands:
    cleanse       — Generate a cleanse plan (does not modify Neo4j)
    apply-cleanse — Execute the plan (removals, merges, normalize)

The plan file is the review artifact. Nothing touches Neo4j until apply-cleanse.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from neo4j import Driver

from .models import (
    CleansePlan,
    DedupSection,
    GroundTruthScore,
    RemovalDecision,
    SnapshotEntity,
)

logger = logging.getLogger(__name__)

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

# Entity types to cleanse, in processing order.
# Company last so validation removes noise in relationship targets first.
ENTITY_LABELS = ["Executive", "Product", "RiskFactor", "FinancialMetric", "Company"]


# ---------------------------------------------------------------------------
# Snapshot helper (inline, no file I/O)
# ---------------------------------------------------------------------------


def _snapshot_entities(driver: Driver, label: str) -> list[SnapshotEntity]:
    """Query Neo4j for all entities of a given label. Returns objects, no file."""
    rows, _, _ = driver.execute_query(
        "MATCH (e:" + label + ") "
        "OPTIONAL MATCH (e)-[:FROM_CHUNK]->(c:Chunk) "
        "WITH e, collect(DISTINCT c.text)[0..3] AS source_chunks "
        "OPTIONAL MATCH (e)-[r]-() "
        "WITH e, source_chunks, count(r) AS rel_count "
        "RETURN elementId(e) AS element_id, "
        "       e.name AS name, "
        "       labels(e) AS all_labels, "
        "       properties(e) AS props, "
        "       source_chunks, "
        "       rel_count "
        "ORDER BY coalesce(e.name, '')"
    )

    entities = []
    for row in rows:
        labels = [la for la in row["all_labels"] if not la.startswith("__")]
        props = {
            k: v
            for k, v in row["props"].items()
            if not k.startswith("__") and not isinstance(v, list)
        }
        entities.append(
            SnapshotEntity(
                element_id=row["element_id"],
                name=row["name"] or "",
                labels=labels,
                properties=props,
                source_chunks=[c for c in row["source_chunks"] if c],
                relationship_count=row["rel_count"],
            )
        )
    return entities


# ---------------------------------------------------------------------------
# Plan generation
# ---------------------------------------------------------------------------


def cleanse(
    driver: Driver,
    phase: str | None = None,
    base_plan: Path | None = None,
    skip_labels: list[str] | None = None,
    only_labels: list[str] | None = None,
) -> Path:
    """Generate a cleanse plan. Does not modify Neo4j.

    Args:
        driver: Neo4j driver.
        phase: Run only this phase ("validate" or "dedup"). Default: both.
        base_plan: Path to an existing plan to build on. Carries forward
            removals and dedup_sections from that plan so you can run
            phases incrementally.
        skip_labels: Entity labels to skip during dedup (e.g. ["RiskFactor"]).
        only_labels: If set, only dedup these labels (e.g. ["RiskFactor"]).

    Returns:
        Path to the cleanse plan JSON file.
    """
    from .entity_resolution import resolve_entities
    from .validate import validate_entities

    LOG_DIR.mkdir(exist_ok=True)

    plan_path = (
        LOG_DIR / f"cleanse_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    # Load base plan if provided
    base: CleansePlan | None = None
    if base_plan:
        print(f"Loading base plan: {base_plan}")
        base = CleansePlan.model_validate_json(base_plan.read_text())

    # Snapshot all entity types
    print("Snapshotting entities...")
    snapshots: dict[str, list[SnapshotEntity]] = {}
    entity_counts: dict[str, int] = {}
    for label in ENTITY_LABELS:
        entities = _snapshot_entities(driver, label)
        snapshots[label] = entities
        entity_counts[label] = len(entities)
        print(f"  {label}: {len(entities)} entities")

    # Mutable state that gets saved incrementally — seed from base plan
    removals: list[RemovalDecision] = list(base.removals) if base else []
    dedup_sections: dict[str, DedupSection] = dict(base.dedup_sections) if base else {}
    ground_truth = base.ground_truth if base else None

    if base and removals:
        print(f"  Carried forward {len(removals)} removals from base plan")
    if base and dedup_sections:
        print(f"  Carried forward dedup for: {', '.join(dedup_sections.keys())}")

    def _save_plan() -> None:
        """Write current plan state to disk."""
        plan = CleansePlan(
            created_at=datetime.now().isoformat(),
            entity_counts=entity_counts,
            removals=removals,
            dedup_sections=dedup_sections,
            ground_truth=ground_truth,
        )
        plan_path.write_text(plan.model_dump_json(indent=2))

    # Phase 1: Validation
    if phase is None or phase == "validate":
        print("\n--- Phase 1: Validation ---")
        removals = validate_entities(snapshots)
        print(f"  Total: {len(removals)} entities marked for removal")
        _save_plan()
        print(f"  (checkpoint saved: {plan_path.name})")

    # Filter out removed entities before dedup
    removed_ids = {r.element_id for r in removals}
    for label in ENTITY_LABELS:
        before = len(snapshots[label])
        snapshots[label] = [
            e for e in snapshots[label] if e.element_id not in removed_ids
        ]
        after = len(snapshots[label])
        if before != after:
            print(f"  {label}: {before} -> {after} after validation")

    # Determine which labels to dedup
    dedup_labels = list(ENTITY_LABELS)
    if only_labels:
        dedup_labels = [l for l in dedup_labels if l in only_labels]
    elif skip_labels:
        dedup_labels = [l for l in dedup_labels if l not in skip_labels]

    # Phase 2: Deduplication
    if phase is None or phase == "dedup":
        print("\n--- Phase 2: Deduplication ---")
        skipped = set(ENTITY_LABELS) - set(dedup_labels)
        if skipped:
            print(f"  Skipping: {', '.join(sorted(skipped))}")
        for label in dedup_labels:
            entities = snapshots[label]
            if not entities:
                continue
            print(f"\n  Deduplicating {label} ({len(entities)} entities)...")
            result = resolve_entities(entities, label)
            dedup_sections[label] = DedupSection(
                label=label,
                config=result.config,
                total_entities=len(entities),
                candidate_pairs=result.candidate_pairs,
                decisions=result.decisions,
                merge_groups=result.merge_groups,
            )
            ready = [g for g in result.merge_groups if g["status"] == "ready"]
            print(f"    {len(ready)} merge groups ready")
            _save_plan()
            print(f"    (checkpoint saved: {plan_path.name})")

    # Ground truth scoring (Company only)
    if "Company" in dedup_sections:
        ground_truth = _score_company_ground_truth(dedup_sections["Company"])

    # Final write
    _save_plan()
    print(f"\nCleanse plan written: {plan_path}")

    if ground_truth:
        print(f"Company ground truth: {ground_truth.overall_score}")

    return plan_path


def _score_company_ground_truth(section: DedupSection) -> GroundTruthScore:
    """Run Company ground truth checks against dedup merge groups."""
    from .compare import (
        _extract_all_merge_groups,
        _score_expected_merges,
        _score_forbidden_merges,
    )

    # Build a plan-like dict for the existing scoring functions
    plan_dict = {"merge_groups": section.merge_groups}
    groups = _extract_all_merge_groups(plan_dict)
    expected = _score_expected_merges(groups)
    forbidden = _score_forbidden_merges(groups)

    expected_pass = sum(1 for r in expected if r.passed)
    forbidden_pass = sum(1 for r in forbidden if r.passed)

    return GroundTruthScore(
        overall_score=f"{expected_pass + forbidden_pass}/{len(expected) + len(forbidden)}",
        expected_merges=expected,
        forbidden_merges=forbidden,
    )


# ---------------------------------------------------------------------------
# Plan execution
# ---------------------------------------------------------------------------


def apply_cleanse(
    driver: Driver,
    plan_path: Path,
    skip_normalize: bool = False,
) -> None:
    """Execute a cleanse plan: removals -> merges -> normalize.

    Args:
        driver: Neo4j driver.
        plan_path: Path to cleanse plan JSON.
        skip_normalize: If True, skip the normalization phase.
    """
    plan = CleansePlan.model_validate_json(plan_path.read_text())

    # Phase 1: Execute removals
    if plan.removals:
        print(f"\n--- Executing {len(plan.removals)} removals ---")
        _execute_removals(driver, plan.removals)

    # Phase 2: Execute merges
    total_groups = 0
    for section in plan.dedup_sections.values():
        total_groups += sum(
            1 for g in section.merge_groups if g["status"] == "ready"
        )

    if total_groups:
        print(f"\n--- Executing merges ({total_groups} groups) ---")
        for label, section in plan.dedup_sections.items():
            _execute_merges(driver, label, section)

    # Phase 3: Normalize
    if not skip_normalize:
        print("\n--- Phase 3: Normalization ---")
        from .normalize import normalize_entities

        normalize_entities(driver)
    else:
        print("\nSkipping normalization (--skip-normalize)")

    print("\nCleanse applied. Run 'uv run python main.py finalize' next.")


def _execute_removals(driver: Driver, removals: list[RemovalDecision]) -> None:
    """Delete entities marked for removal."""
    ok = 0
    fail = 0
    for r in removals:
        try:
            driver.execute_query(
                "MATCH (n) WHERE elementId(n) = $eid DETACH DELETE n",
                eid=r.element_id,
            )
            ok += 1
        except Exception as e:
            fail += 1
            logger.error(f"Failed to remove {r.name} ({r.entity_type}): {e}")

    print(f"  Removals: {ok} OK, {fail} failed")


def _execute_merges(driver: Driver, label: str, section: DedupSection) -> None:
    """Execute merge groups for one entity type."""
    ready = [g for g in section.merge_groups if g["status"] == "ready"]
    if not ready:
        return

    consumed_total = sum(len(g["consumed"]) for g in ready)
    print(f"  {label}: {len(ready)} groups ({consumed_total} merges)")

    ok = 0
    fail = 0
    for group in ready:
        survivor_id = group["survivor"]["element_id"]
        survivor_name = group["survivor"]["name"]
        for consumed in group["consumed"]:
            consumed_id = consumed["element_id"]
            try:
                # Compute fill properties: consumed's non-null props that survivor lacks
                props_result, _, _ = driver.execute_query(
                    "MATCH (s) WHERE elementId(s) = $sid "
                    "MATCH (c) WHERE elementId(c) = $cid "
                    "RETURN properties(s) AS sp, properties(c) AS cp",
                    sid=survivor_id,
                    cid=consumed_id,
                )
                fill_props = {}
                if props_result:
                    sp = props_result[0]["sp"]
                    cp = props_result[0]["cp"]
                    for k, v in cp.items():
                        if k.startswith("__"):
                            continue
                        if v and not sp.get(k):
                            fill_props[k] = v

                driver.execute_query(
                    """
                    MATCH (survivor) WHERE elementId(survivor) = $survivor_id
                    MATCH (consumed) WHERE elementId(consumed) = $consumed_id
                    CALL apoc.refactor.mergeNodes([survivor, consumed],
                         {properties: 'discard', mergeRels: true})
                    YIELD node
                    SET node += $fill_props
                    RETURN node.name AS name
                    """,
                    survivor_id=survivor_id,
                    consumed_id=consumed_id,
                    fill_props=fill_props,
                )
                ok += 1
            except Exception as e:
                fail += 1
                logger.error(
                    f"Failed merging {consumed['name']} into {survivor_name}: {e}"
                )

    if fail:
        print(f"    {ok} OK, {fail} failed")


def latest_cleanse_plan() -> Path | None:
    """Find the most recent cleanse plan file."""
    if not LOG_DIR.exists():
        return None
    files = sorted(LOG_DIR.glob("cleanse_plan_*.json"), reverse=True)
    return files[0] if files else None
