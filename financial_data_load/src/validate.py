"""Entity validation phase: remove entities that don't belong.

Called by cleanse.py during plan generation. Returns a list of
RemovalDecision objects without modifying Neo4j.

Each entity type has a validation prompt that asks the LLM a binary
question: does this entity belong to this label? Entities that fail
are marked for removal in the cleanse plan.
"""

from __future__ import annotations

import json
import logging
import re

from .config import get_llm_deterministic
from .models import RemovalDecision, SnapshotEntity

logger = logging.getLogger(__name__)

BATCH_SIZE = 30  # entities per LLM call


# ---------------------------------------------------------------------------
# Validation prompts per entity type
# ---------------------------------------------------------------------------

VALIDATION_PROMPTS: dict[str, str] = {
    "Executive": (
        "Is this a named individual person who holds a corporate officer, "
        "executive, or board member position? Reject titles without names, "
        "committees, generic roles, and non-person entries."
    ),
    "Product": (
        "Is this a specific, named commercial product or service that a company "
        "offers to customers? Reject generic technology terms (e.g. 'AI', 'API', "
        "'IoT'), internal programs, corporate initiatives, and regulatory references."
    ),
    "RiskFactor": (
        "Is this a distinct risk category or risk event that a company discloses "
        "in an SEC filing? Reject entries that are regulatory bodies, legislation "
        "names without risk framing, or general business concepts that are not risks."
    ),
    "FinancialMetric": (
        "Is this a quantifiable financial measure with a numeric value? "
        "Reject entries where the value field is empty or non-numeric."
    ),
    "Company": (
        "Is this the name of an actual company or organization (appearing as a "
        "competitor or partner)? Reject generic terms like 'Competitors', "
        "'Local companies', categories like 'Utility', and regulatory bodies."
    ),
}


# ---------------------------------------------------------------------------
# Public interface (called by cleanse.py)
# ---------------------------------------------------------------------------


def validate_entities(
    snapshots: dict[str, list[SnapshotEntity]],
) -> list[RemovalDecision]:
    """Validate all entity types. Returns list of RemovalDecision.

    Args:
        snapshots: Dict mapping label -> list of SnapshotEntity.

    Returns:
        List of RemovalDecision for entities that should be removed.
    """
    removals: list[RemovalDecision] = []

    for label, prompt in VALIDATION_PROMPTS.items():
        entities = snapshots.get(label, [])
        if not entities:
            continue

        print(f"  Validating {label} ({len(entities)} entities)...")
        label_removals = _validate_entity_type(entities, label, prompt)
        removals.extend(label_removals)
        print(f"    {len(label_removals)} marked for removal")

    return removals


# ---------------------------------------------------------------------------
# Internal implementation
# ---------------------------------------------------------------------------


SYSTEM_PROMPT_TEMPLATE = """\
You are an entity validation expert for a knowledge graph built from SEC 10-K \
financial filings.

You will be given a numbered list of entities extracted from SEC filings, each \
labeled as "{label}". For each entity, decide whether it truly belongs under \
this label.

Validation question: {validation_prompt}

Rules:
- Be conservative: when in doubt, KEEP the entity. It is better to have a few \
extra nodes than to accidentally remove valid ones.
- Only mark an entity for removal if you are confident it does not belong.
- Consider the entity name, its properties, and the associated company context.

Return your answer as JSON with this exact structure:
{{"decisions": [{{"index": 1, "keep": true, "reasoning": "..."}}, \
{{"index": 2, "keep": false, "reasoning": "..."}}]}}

Return a decision for EVERY entity in the list. The "index" field must match \
the number shown next to each entity. The "reasoning" field should be a brief \
explanation (one sentence)."""


def _validate_entity_type(
    entities: list[SnapshotEntity],
    label: str,
    validation_prompt: str,
) -> list[RemovalDecision]:
    """Validate entities of one type via LLM. Returns RemovalDecision list.

    1. Build batches of BATCH_SIZE entities
    2. For each batch, format entity names + properties + associated company
    3. Send to LLM with system prompt containing the validation_prompt
    4. Parse JSON response: {"decisions": [{"index": N, "keep": bool, "reasoning": "..."}]}
    5. Return RemovalDecision for each entity where keep=false
    """
    client = get_llm_deterministic()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        label=label,
        validation_prompt=validation_prompt,
    )

    removals: list[RemovalDecision] = []

    # Build batches
    batches: list[list[SnapshotEntity]] = [
        entities[i : i + BATCH_SIZE]
        for i in range(0, len(entities), BATCH_SIZE)
    ]

    for batch_num, batch in enumerate(batches, 1):
        print(f"    Batch {batch_num}/{len(batches)} ({len(batch)} entities)...")

        # Format the user prompt with entity details
        user_prompt = _format_batch_prompt(batch, label)

        try:
            response = client.invoke(user_prompt, system_instruction=system_prompt)
            content = response.content

            # Strip markdown fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]

            result = json.loads(content)
            decisions_raw = result.get("decisions", [])
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(
                f"Failed to parse LLM response for {label} batch {batch_num}: {e}"
            )
            # Skip this batch — conservative approach, keep all entities
            continue
        except Exception as e:
            logger.error(
                f"LLM call failed for {label} batch {batch_num}: {e}"
            )
            continue

        # Process decisions
        for d in decisions_raw:
            idx = d.get("index", 0) - 1  # convert 1-based to 0-based
            if idx < 0 or idx >= len(batch):
                logger.warning(
                    f"LLM returned invalid index {d.get('index')} "
                    f"for {label} batch {batch_num}"
                )
                continue

            keep = d.get("keep", True)  # default to keep (conservative)
            if not keep:
                entity = batch[idx]
                company = _get_associated_company(entity)
                removals.append(
                    RemovalDecision(
                        entity_type=label,
                        element_id=entity.element_id,
                        name=entity.name,
                        company=company,
                        reasoning=d.get("reasoning", "No reasoning provided"),
                    )
                )

    return removals


def _format_batch_prompt(
    batch: list[SnapshotEntity],
    label: str,
) -> str:
    """Build the user prompt for a batch of entities to validate."""
    lines = []
    for i, entity in enumerate(batch, 1):
        company = _get_associated_company(entity)

        # Format properties (exclude name to avoid redundancy)
        props = {
            k: v
            for k, v in entity.properties.items()
            if k != "name" and v is not None and v != ""
        }
        props_str = (
            ", ".join(f"{k}={v}" for k, v in props.items())
            if props
            else "(none)"
        )

        lines.append(f"{i}. \"{entity.name}\"")
        lines.append(f"   Company: {company}")
        lines.append(f"   Properties: {props_str}")

        # Include a snippet of source text for additional context
        if entity.source_chunks:
            chunk_preview = entity.source_chunks[0][:300]
            lines.append(f"   Source text: {chunk_preview}")

        lines.append("")

    return "\n".join(lines)


def _get_associated_company(entity: SnapshotEntity) -> str:
    """Extract the associated company name from an entity's properties or source chunks.

    Strategy:
    1. Check properties for a 'company' field (some entities store it directly).
    2. Search source_chunks for common SEC filing company name patterns.
    3. Fall back to 'unknown' if no company can be determined.
    """
    # 1. Check properties for explicit company field
    company = entity.properties.get("company")
    if company and isinstance(company, str) and company.strip():
        return company.strip()

    # Also check for 'companyName' or similar variants
    for key in ("companyName", "company_name", "filing_company"):
        val = entity.properties.get(key)
        if val and isinstance(val, str) and val.strip():
            return val.strip()

    # 2. Try to extract company name from source chunk text
    if entity.source_chunks:
        company_from_chunk = _extract_company_from_text(entity.source_chunks[0])
        if company_from_chunk:
            return company_from_chunk

    return "unknown"


def _extract_company_from_text(text: str) -> str | None:
    """Try to identify a company name from SEC filing source text.

    Looks for common patterns in 10-K filings like:
    - "COMPANY_NAME (the "Company")"
    - "filed by COMPANY_NAME"
    - Company names followed by common suffixes (Inc., Corp., LLC, etc.)
    """
    if not text:
        return None

    # Pattern: "COMPANY_NAME, Inc." or "COMPANY_NAME Corporation" etc.
    # Look for known SEC filing patterns
    patterns = [
        # "X (the "Company")" or "X (the 'Company')"
        r'([A-Z][A-Za-z\s&.,]+(?:Inc\.|Corp(?:oration)?|LLC|Ltd\.?|Co\.|L\.P\.))\s*\((?:the\s+)?["\'](?:Company|Registrant)',
        # "X, Inc." at start of text (common in filing headers)
        r'^([A-Z][A-Za-z\s&.,]+(?:Inc\.|Corp(?:oration)?|LLC|Ltd\.?|Co\.|L\.P\.))',
    ]

    for pattern in patterns:
        match = re.search(pattern, text[:500])
        if match:
            name = match.group(1).strip().rstrip(",")
            if len(name) > 2 and len(name) < 100:
                return name

    return None
