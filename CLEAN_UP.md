# Proposal: Post-Extraction Cleansing for the Financial Data Pipeline

## Design Decisions

1. **`cleanse` absorbs Company resolution.** The existing `snapshot → resolve → apply-merges` flow is replaced entirely. `cleanse` generalizes entity_resolution.py to all entity types including Companies (using the proven prefix-0.3/binary config for Companies). The old `snapshot`, `resolve`, `apply-merges`, and `compare` commands will be removed — no backward compatibility needed. Pipeline becomes `restore → cleanse → apply-cleanse → finalize`.

2. **Offline plan with review.** `cleanse` produces a plan file (validation removals + dedup merges for all entity types). `apply-cleanse` executes the plan. Nothing touches Neo4j until you review and approve.

3. **Company ground truth regression checks.** `apply-cleanse` automatically scores the plan's Company merge section against the existing 6-expected/5-forbidden ground truth before applying. Warns on regressions.

4. **Normalize defaults to on.** `apply-cleanse` runs normalize after merges. Skip with `--skip-normalize`.

5. **No comparison framework for non-Company entities.** One-shot review via the plan file is sufficient. No ground truth exists for those types.

## The Mess

The `financial_data_load/` pipeline extracts entities from SEC 10-K PDFs using `SimpleKGPipeline` and an LLM. The extraction produces a graph with real structure, but the entities themselves are noisy. After exporting the gold database to CSVs, the problems are visible at a glance.

**Products (274 rows):** The LLM extracts every noun phrase that looks like a product or service. Microsoft alone generates entries for "Azure," "Azure AI," "Azure AI platform," "Azure IoT Edge," "Azure Orbital," and "Azure Space & Missions Engineering." Apple produces separate entries for "MacBook Air 15\"," "MacBook Pro 14\"," and "MacBook Pro 16\"" rather than a single "MacBook" product family. Generic terms like "AI," "API," and "IoT" appear as products. Non-products like "Benefits for Employees," "Justice Reform Initiative," and "AI Skills Initiative" are labeled as products because they appeared in contexts the LLM interpreted as offerings.

**Risk Factors (203 rows):** Near-duplicates proliferate. "COVID-19," "COVID-19 Pandemic," "COVID-19 pandemic," "COVID-19 pandemic impact" are four separate risk factor nodes. "Competition," "Competition Risk," "Competition in our current and target markets," "Intense Competition," and "Competition Investigation" each have their own node. Some risk factors are company-specific events rather than risk categories ("2020 Zogg fire," "Catastrophic Event Memorandum Account Application"). Many descriptions are raw list dumps from the PDF text, stored as Python list literals rather than clean prose.

**Executives (33 rows):** The LLM extracts both formal names and honorifics as separate entities. "Amy E. Hood" and "Ms. Hood" both exist. "Bradford L. Smith" and "Mr. Smith" both exist. "Compensation Committee" and "Board of Directors" appear as executives. "Employees" is listed as an executive with the title "Full-time and part-time." One entry is literally "Unnamed executive." PG&E has "Executive Vice President" as a name with the title as a separate field, and a second entry that concatenates both into the name.

**Competitors (37 rows):** The LLM creates COMPETES_WITH relationships to entities that are not companies. Amazon "competes with" "Competitors" (the word itself) and "Local companies" (a generic phrase). PG&E "competes with" "FERC" (a regulator) and "Utility" (a category). "Arm" and "Arm Limited" appear as separate competitors of NVIDIA.

**Financial Metrics (111 rows):** Values are stored as strings, sometimes with currency symbols or units embedded. Period fields are inconsistent: some say "fiscal year 2023," others "FY2023," others are empty.

The existing entity resolution module (`entity_resolution.py`) addresses one piece of this: it merges Company nodes with similar names using fuzzy matching and LLM pairwise comparison. But it only runs on Company entities and only handles the deduplication problem. The noise problems in other entity types remain untouched.

## The Approach

A single `cleanse` command that runs three internal phases in sequence — validate, deduplicate, normalize — after `SimpleKGPipeline` finishes and before the `finalize` step creates constraints and indexes. The phases have an internal ordering dependency (validation reduces dedup candidates, dedup reduces normalization work) but from the user's perspective it's one step. Each phase uses LLM calls to make judgment calls that rule-based logic cannot, but constrains those calls with structured prompts and validation.

### Phase 1: Entity Validation

The first source of noise is entities that should not exist at all. "Employees" is not an executive. "AI" is not a product. "Competitors" is not a company. A validation pass reviews each entity against its label and removes or re-labels the ones that don't belong.

The approach: for each entity type, send batches of entity names (with their descriptions and connected company) to the LLM with a type-specific validation prompt. The prompt asks a binary question: does this entity belong to this label? For executives, the question is "Is this a named individual person who holds a corporate officer or board position?" For products, "Is this a specific, named product or service that a customer can purchase or use?" The LLM returns a keep/remove decision for each entity in the batch.

Entities marked for removal are detached from the graph (relationships deleted, node deleted). Entities that belong under a different label can be re-labeled if a clear mapping exists (a "Board of Directors" executive becoming a governance entity, for example), but in the first iteration, removal is simpler and safer than re-labeling.

**Entity types and their validation questions:**

- **Executive:** Is this a named individual person who holds a corporate officer, executive, or board member position? Reject titles without names, committees, generic roles, and non-person entries.
- **Product:** Is this a specific, named commercial product or service that a company offers to customers? Reject generic technology terms, internal programs, corporate initiatives, and regulatory references.
- **RiskFactor:** Is this a distinct risk category or risk event that a company discloses in an SEC filing? Reject entries that are regulatory bodies, legislation names without risk framing, or duplicates of other risk factor entries in the same batch.
- **FinancialMetric:** Is this a quantifiable financial measure with a numeric value? Reject entries where the value field is empty or non-numeric.
- **Company (in COMPETES_WITH / PARTNERS_WITH):** Is this the name of an actual company or organization? Reject generic terms, categories, and regulatory bodies.

### Phase 2: Entity Deduplication

After validation removes the entries that don't belong, the remaining entities still contain duplicates. "Amy E. Hood" and "Ms. Hood" refer to the same person. "A100" and "A100 integrated circuits" refer to the same product. "COVID-19 pandemic" and "COVID-19 Pandemic" and "COVID-19 pandemic impact" describe the same risk.

The existing `entity_resolution.py` module provides the right architecture for this: fuzzy pre-filtering to generate candidate pairs, LLM pairwise comparison to confirm merges, and `apoc.refactor.mergeNodes` to execute them. The module currently only runs against Company nodes. Extending it to all entity types (Company, Product, RiskFactor, Executive, FinancialMetric) requires:

- Running the dedup cycle for each entity label, with Company using the proven prefix-0.3/binary config.
- Tuning the pre-filter threshold per entity type. Product names tend to have high string similarity when they're variants ("Azure" vs "Azure AI"), so a lower threshold catches more candidates. Executive names with honorific variants ("Mr. Smith" vs "Bradford L. Smith") need a different matching strategy, perhaps combining fuzzy matching with a title-based heuristic.
- Adjusting the LLM system prompt per entity type. The current prompt has Company-specific rules (ticker and CIK are definitive signals). Executive resolution needs rules about honorifics and name variants. Product resolution needs rules about product families versus distinct SKUs.

### Phase 3: Description Normalization

Many entity descriptions are raw text dumps from the PDF extraction. Risk factor descriptions contain Python list literals (`['First sentence.', 'Second sentence.']`). Executive titles contain list literals. Some descriptions are multi-paragraph extracts that should be a single summary sentence.

An LLM normalization pass reads each entity's description and rewrites it as clean, concise prose. For risk factors, this means collapsing a list of extracted sentences into a one-to-two sentence summary of the risk. For executives, it means picking the most complete title variant. For financial metrics, it means standardizing the value format (numeric, with unit) and the period format (consistent "FY2023" style).

This phase is lower priority than validation and deduplication, but it directly improves the quality of fulltext search results and the readability of agent responses in Labs 1 and 2.

## Where This Fits in the Pipeline

The current pipeline flow:

```
load (PDFs) -> backup -> restore -> snapshot -> resolve (Companies) -> apply-merges -> finalize
```

The proposed flow replaces `snapshot → resolve → apply-merges` with `cleanse → apply-cleanse`:

```
load (PDFs) -> backup -> restore -> cleanse -> [review plan] -> apply-cleanse -> finalize
```

`cleanse` reads the graph, runs validate → deduplicate (all entity types including Companies) internally, and writes a plan file to `logs/cleanse_plan_*.json`. It never modifies Neo4j. `apply-cleanse` executes the plan (removals, merges) and then runs normalize on the surviving entities.

In README section 6, this replaces the current snapshot/resolve/apply-merges steps:

```bash
uv run python main.py restore

# Generate cleanse plan (validate + dedup all entity types — does not modify Neo4j)
uv run python main.py cleanse

# Review the plan
cat logs/cleanse_plan_*.json

# Apply the plan (removals, merges, normalize)
uv run python main.py apply-cleanse
# Or skip normalize: uv run python main.py apply-cleanse --skip-normalize

uv run python main.py finalize
uv run python main.py verify
```

`cleanse` flags: `--phase validate|dedup` (run a single phase).

## Tradeoffs

**LLM cost:** Each phase makes LLM calls. Validation sends batches of 20-50 entities per call across 5 entity types, so roughly 30-50 LLM calls for a 9-company dataset. Deduplication depends on the number of candidate pairs (the fuzzy pre-filter reduces this significantly). Normalization is one call per entity with a non-empty description. For the current dataset size this is modest, but cost scales linearly with the number of filings processed.

**False positives in validation:** An aggressive validation prompt might remove entities that legitimately belong. "AI" as a product is debatable for a company like Microsoft whose AI division is a revenue-generating business. The validation prompt needs to be specific enough to catch "Benefits for Employees" but permissive enough to keep "AI Enterprise." Tuning this requires reviewing the first batch of decisions and adjusting the prompt.

**Dedup merge direction:** When merging "Amy E. Hood" and "Ms. Hood," the survivor should be "Amy E. Hood" (the more complete name). The existing merge logic uses `apoc.refactor.mergeNodes` with `properties: 'combine'`, which keeps all properties. The survivor selection logic may need refinement to prefer the more informative name.

**Ordering dependency:** Validation should run before deduplication. Removing invalid entities first reduces the number of candidate pairs the dedup phase needs to evaluate and prevents false merge candidates (merging "Board of Directors" with "Board of Directors of PG&E Corporation" is a waste of an LLM call when both should be removed).

## Implementation Plan

### Step 1: Shared Contract (skeleton — done before parallel work)

Define the plan file schema, function signatures, and orchestrator.

| File | Purpose |
|------|---------|
| `src/cleanse.py` | Orchestrator, plan data models (`CleansePlan`, `RemovalDecision`, `DedupSection`), `cleanse()` and `apply_cleanse()`, snapshot helper, ground truth scoring |
| `src/validate.py` | Function signature: `validate_entities(snapshots) -> list[RemovalDecision]` |
| `src/normalize.py` | Function signature: `normalize_entities(driver) -> None` |
| `src/entity_resolution.py` | New: `ResolutionResult` model, `resolve_entities(entities, label) -> ResolutionResult` |
| `main.py` | `cleanse` and `apply-cleanse` commands |

### Step 2: Parallel Implementation (3 agents, no file conflicts)

| Agent | File it writes to | Scope |
|-------|-------------------|-------|
| **Validation** | `src/validate.py` | LLM validation prompts per entity type, batch processing (20-50 entities per call), RemovalDecision generation |
| **Dedup** | `src/entity_resolution.py` | Implement `resolve_entities()` by extracting core logic from existing `resolve()`, add per-label system prompts and default configs, add honorific/product-family pre-filters |
| **Normalize** | `src/normalize.py` | LLM normalization prompts, batch rewriting, period/value standardization, logging to `logs/cleanse_normalize_*.json` |

No merge conflicts: each agent only modifies its own file. The orchestrator (`cleanse.py`) imports from all three and is already complete.

### Step 3: Integration

- Remove old commands (`snapshot`, `resolve`, `apply-merges`, `compare`) from `main.py`
- Remove `src/snapshot.py` and `src/compare.py` (after extracting ground truth into `cleanse.py`)
- Update README section 6
- Re-export CSVs and verify

## TODO

### `cleanse` command — plan generation (`src/cleanse.py`)

- [ ] Add `cleanse` command to `main.py` with flags: `--phase validate|dedup` (run a single phase)
- [ ] Implement two-phase plan generator: validate → dedup, writing combined plan to `logs/cleanse_plan_*.json`
- [ ] Plan file format: JSON with `removals` (entity name, type, reasoning) and `merges` (per entity type, groups with survivor + absorbed entities)

### `apply-cleanse` command

- [ ] Add `apply-cleanse` command to `main.py` with flags: `--plan PATH`, `--skip-normalize`
- [ ] Execute removals from the plan (detach delete)
- [ ] Execute merges from the plan (apoc.refactor.mergeNodes)
- [ ] Run normalize phase on surviving entities (default on, skippable)
- [ ] Run Company ground truth checks against the plan's Company merge section to catch regressions

### Phase 1: Entity Validation (inside `cleanse`)

- [ ] Design validation prompts for each entity type (Executive, Product, RiskFactor, FinancialMetric, Company-in-relationships)
- [ ] Build a batch validation function that sends entity names + context to the LLM and parses keep/remove decisions
- [ ] Run against the gold database and review decisions; adjust prompts based on false positives/negatives

### Phase 2: Entity Deduplication (inside `cleanse`)

- [ ] Generalize `entity_resolution.py` to accept any entity label, not just Company
- [ ] Company uses proven prefix-0.3/binary config; other types get independent configs
- [ ] Add per-entity-type configuration (pre-filter threshold, LLM system prompt, merge strategy)
- [ ] Add an honorific-aware pre-filter for Executive entities ("Mr./Ms./Mrs." prefix detection)
- [ ] Add a product-family pre-filter for Product entities (common prefix with different suffixes)
- [ ] Define survivor selection logic (prefer longer names, prefer names with first and last, prefer names without list-literal formatting)

### Phase 3: Description Normalization (inside `apply-cleanse`)

- [ ] Design a normalization prompt that converts list literals and multi-sentence extracts to clean prose
- [ ] Build a batch normalization function that rewrites descriptions in place
- [ ] Standardize financial metric values to numeric format with explicit unit and period fields
- [ ] Standardize executive titles to a single string (resolve list literals, pick most complete variant)
- [ ] Log all rewrites to `logs/cleanse_normalize_*.json` with before/after pairs

### Integration

- [ ] Remove old commands from `main.py`: `snapshot`, `resolve`, `apply-merges`, `compare`
- [ ] Remove `src/snapshot.py` and `src/compare.py` (dedup logic in `entity_resolution.py` is reused, not removed)
- [ ] Update README section 6: replace `snapshot → resolve → apply-merges` with `cleanse → apply-cleanse`
- [ ] Update `main.py` docstring to reflect new pipeline flow
- [ ] Re-export CSVs to `TransformedData/` after cleansing and verify improved counts
- [ ] Update the extraction schema prompts in `schema.py` to reduce noise at the source (more specific entity descriptions, negative examples in the schema)
