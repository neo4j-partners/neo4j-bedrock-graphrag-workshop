"""Description normalization phase: clean up raw text dumps.

Called by apply_cleanse() after removals and merges are applied.
Operates directly on Neo4j — rewrites descriptions in place.
Logs all rewrites to logs/cleanse_normalize_*.json.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from neo4j import Driver

from .config import get_llm_deterministic

logger = logging.getLogger(__name__)

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

BATCH_SIZE = 20  # entities per LLM call

# ---------------------------------------------------------------------------
# Normalization targets per entity type
# ---------------------------------------------------------------------------

NORMALIZATION_TARGETS: dict[str, dict] = {
    "RiskFactor": {
        "fields": ["description"],
        "instruction": (
            "Rewrite the description as 1-2 clean prose sentences summarizing "
            "the risk. Convert Python list literals to prose. Remove raw PDF "
            "extraction artifacts."
        ),
    },
    "Executive": {
        "fields": ["title"],
        "instruction": (
            "Pick the most complete, formal job title. If the title is a Python "
            "list literal, extract the best single title. Remove artifacts."
        ),
    },
    "FinancialMetric": {
        "fields": ["value", "period"],
        "instruction": (
            "Standardize value to a clean numeric format with explicit unit "
            "(e.g. '$1.2B', '15.3%'). Standardize period to 'FY2023' format. "
            "If the period is empty, leave it empty."
        ),
    },
    "Product": {
        "fields": ["description"],
        "instruction": (
            "If there is a description, rewrite it as a single clean sentence. "
            "Convert Python list literals to prose. Remove raw PDF artifacts."
        ),
    },
}

# ---------------------------------------------------------------------------
# System prompt for the normalization LLM
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a data normalization expert for a knowledge graph built from SEC 10-K \
financial filings.

You will receive a batch of entities with their current field values. Your job \
is to normalize the fields according to the specific instructions provided.

Rules:
- Only change fields that actually need cleaning. If a field is already clean, \
return it unchanged and set "changed" to false.
- Convert Python list literals (e.g. ['item1', 'item2']) to clean prose.
- Remove raw PDF extraction artifacts (extra whitespace, garbled characters, \
line-break artifacts).
- For financial values: do NOT invent numbers. Only reformat existing values \
into a standardized form (e.g. '$1.2B', '15.3%'). If you cannot determine \
the correct format, leave the value unchanged.
- For executive titles: if you see a Python list like ['CEO', 'Chairman'], \
pick the single most senior or complete title. If you see duplicates, pick \
the best one.
- For periods: standardize to 'FY2023' format. If the period says \
'fiscal year 2023' or 'Fiscal Year 2023', convert to 'FY2023'. If the \
period is empty or cannot be determined, leave it empty.
- Keep normalized text concise and factual. Do not add information that is \
not present in the original.

Return ONLY valid JSON in this exact format:
{"normalized": [{"index": 1, "fields": {"field_name": "normalized value"}, \
"changed": true}, ...]}

Every entity in the batch must appear in the response. The "index" field \
corresponds to the entity number in the batch (1-based). The "fields" object \
must contain all fields listed for that entity. Set "changed" to true if ANY \
field was modified, false if all fields are unchanged."""


# ---------------------------------------------------------------------------
# Neo4j queries
# ---------------------------------------------------------------------------


def _query_entities(
    driver: Driver, label: str, fields: list[str]
) -> list[dict[str, Any]]:
    """Query Neo4j for entities with non-empty values in the target fields.

    Returns a list of dicts with element_id, name, and field values.
    """
    # Build WHERE clause: at least one target field must be non-null and non-empty
    where_clauses = []
    for field in fields:
        where_clauses.append(f"(e.{field} IS NOT NULL AND e.{field} <> '')")
    where_str = " OR ".join(where_clauses)

    # Build RETURN clause
    return_parts = ["elementId(e) AS element_id", "e.name AS name"]
    for field in fields:
        return_parts.append(f"e.{field} AS {field}")
    return_str = ", ".join(return_parts)

    query = (
        f"MATCH (e:{label}) "
        f"WHERE {where_str} "
        f"RETURN {return_str}"
    )

    rows, _, _ = driver.execute_query(query)

    entities = []
    for row in rows:
        entity: dict[str, Any] = {
            "element_id": row["element_id"],
            "name": row["name"] or "",
        }
        for field in fields:
            entity[field] = row[field] if row[field] is not None else ""
        entities.append(entity)

    return entities


def _update_entity(driver: Driver, element_id: str, field: str, new_value: str) -> None:
    """Update a single field on an entity in Neo4j."""
    driver.execute_query(
        f"MATCH (e) WHERE elementId(e) = $element_id SET e.{field} = $new_value",
        element_id=element_id,
        new_value=new_value,
    )


# ---------------------------------------------------------------------------
# LLM batch processing
# ---------------------------------------------------------------------------


def _build_batch_prompt(
    entities: list[dict[str, Any]],
    fields: list[str],
    instruction: str,
) -> str:
    """Build the user prompt for a batch of entities."""
    lines = [f"Normalization instruction: {instruction}", ""]
    lines.append(f"Fields to normalize: {', '.join(fields)}")
    lines.append("")

    for i, entity in enumerate(entities, 1):
        lines.append(f"Entity {i}: {entity['name']}")
        for field in fields:
            value = entity.get(field, "")
            lines.append(f"  {field}: {value}")
        lines.append("")

    return "\n".join(lines)


def _parse_llm_response(content: str) -> dict[str, Any] | None:
    """Parse the LLM response JSON, handling markdown fences."""
    # Strip markdown fences if present
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        return None


def _call_llm_batch(
    entities: list[dict[str, Any]],
    fields: list[str],
    instruction: str,
    client,
) -> list[dict[str, Any]] | None:
    """Send a batch to the LLM and parse normalized results.

    Returns a list of dicts with index, fields, and changed flag,
    or None if the call or parsing failed.
    """
    prompt = _build_batch_prompt(entities, fields, instruction)

    try:
        response = client.invoke(prompt, system_instruction=SYSTEM_PROMPT)
        content = response.content
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return None

    result = _parse_llm_response(content)
    if result is None:
        return None

    normalized = result.get("normalized")
    if not isinstance(normalized, list):
        logger.error("LLM response missing 'normalized' array")
        return None

    return normalized


# ---------------------------------------------------------------------------
# Public interface (called by apply_cleanse in cleanse.py)
# ---------------------------------------------------------------------------


def normalize_entities(driver: Driver) -> None:
    """Normalize descriptions and fields for all entity types.

    Queries Neo4j for entities with non-empty target fields, sends batches
    to the LLM for normalization, and updates entities in place.
    """
    LOG_DIR.mkdir(exist_ok=True)

    client = get_llm_deterministic()
    all_rewrites: list[dict[str, Any]] = []

    for entity_type, target in NORMALIZATION_TARGETS.items():
        fields: list[str] = target["fields"]
        instruction: str = target["instruction"]

        print(f"  Normalizing {entity_type} ({', '.join(fields)})...")

        # Query entities with non-empty target fields
        entities = _query_entities(driver, entity_type, fields)
        if not entities:
            print(f"    No {entity_type} entities to normalize.")
            continue

        print(f"    Found {len(entities)} entities")

        # Process in batches
        batches = [
            entities[i : i + BATCH_SIZE]
            for i in range(0, len(entities), BATCH_SIZE)
        ]

        type_rewrite_count = 0

        for batch_num, batch in enumerate(batches, 1):
            print(
                f"    Batch {batch_num}/{len(batches)} "
                f"({len(batch)} entities)..."
            )

            normalized = _call_llm_batch(batch, fields, instruction, client)
            if normalized is None:
                logger.error(
                    f"    Skipping batch {batch_num} for {entity_type} "
                    f"due to LLM error"
                )
                continue

            # Process each normalized entity in the response
            for item in normalized:
                index = item.get("index")
                if not isinstance(index, int) or index < 1 or index > len(batch):
                    logger.warning(
                        f"    Invalid index {index} in LLM response, skipping"
                    )
                    continue

                entity = batch[index - 1]
                changed = item.get("changed", False)
                new_fields = item.get("fields", {})

                if not changed:
                    continue

                # Update each changed field
                for field in fields:
                    new_value = new_fields.get(field)
                    if new_value is None:
                        continue

                    old_value = entity.get(field, "")

                    # Only update if the value actually differs
                    if str(new_value).strip() == str(old_value).strip():
                        continue

                    # Write to Neo4j
                    try:
                        _update_entity(
                            driver, entity["element_id"], field, new_value
                        )
                    except Exception as e:
                        logger.error(
                            f"    Failed to update {entity_type} "
                            f"'{entity['name']}' field '{field}': {e}"
                        )
                        continue

                    # Record the rewrite
                    all_rewrites.append(
                        {
                            "entity_type": entity_type,
                            "element_id": entity["element_id"],
                            "name": entity["name"],
                            "field": field,
                            "before": old_value,
                            "after": new_value,
                        }
                    )
                    type_rewrite_count += 1

        print(f"    {type_rewrite_count} fields rewritten for {entity_type}")

    # Write log file
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "rewrites": all_rewrites,
    }
    log_path = (
        LOG_DIR
        / f"cleanse_normalize_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    log_path.write_text(json.dumps(log_entry, indent=2))

    print(f"\n  Normalization complete: {len(all_rewrites)} total rewrites")
    print(f"  Log: {log_path}")
