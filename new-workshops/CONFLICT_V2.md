# Entity Conflict Issue: Root Cause Analysis and Proposed Solutions

> **STATUS: RESOLVED** - The library fix has been implemented. See the "Resolution" section at the end.

This document provides an in-depth analysis of the entity conflict error encountered when running the full data load pipeline, identifies the root causes in both the neo4j-graphrag-python library and this project, and proposes solutions.

---

## Executive Summary

The error "Node already exists with label Company and property name = 'Apple Inc.'" occurs because:

1. The LLM extracts the same entity (e.g., "Apple Inc.") from multiple chunks of a single PDF
2. The neo4j-graphrag-python library's KGWriter uses CREATE (not MERGE) to write nodes
3. A uniqueness constraint on Company.name causes the second creation attempt to fail
4. Entity resolution runs AFTER node creation, so it cannot prevent the conflict

This is a **library design limitation** compounded by **project-specific constraints**.

---

## Part 1: Neo4j-GraphRAG-Python Library Analysis

### How the Pipeline Works

The SimpleKGPipeline processes documents through these stages:

```
PDF Loader → Splitter → Chunk Embedder → Schema → Extractor → Pruner → Writer → Resolver
```

Each stage passes data to the next. The critical stages for this issue are:

| Stage | What It Does |
|-------|-------------|
| Splitter | Breaks document into chunks (e.g., 2000 chars each) |
| Extractor | LLM extracts entities from EACH chunk independently |
| Writer | Creates nodes in Neo4j using CREATE statements |
| Resolver | Merges duplicate entities (runs AFTER writer) |

### The Core Problem: CREATE vs MERGE

**File:** `neo4j_graphrag/experimental/components/kg_writer.py`

The KGWriter uses this Cypher pattern:

```cypher
UNWIND $rows AS row
CREATE (n:__KGBuilder__ {__tmp_internal_id: row.id})
SET n += row.properties
WITH n, row
CALL apoc.create.addLabels(n, row.labels) YIELD node
...
```

Key observations:

1. **Uses CREATE, not MERGE** - Every extracted entity becomes a new node
2. **Labels added after creation** - apoc.create.addLabels adds Company label to an already-created node
3. **No batch deduplication** - If "Apple Inc." appears in 5 chunks, 5 CREATE statements run

### Why apoc.create.addLabels Fails

The failure sequence:

1. Node created with only `__KGBuilder__` label and `name: "Apple Inc."`
2. Second node created with `__KGBuilder__` label and `name: "Apple Inc."`
3. `apoc.create.addLabels` adds `Company` label to first node - succeeds
4. `apoc.create.addLabels` adds `Company` label to second node - **FAILS**

The uniqueness constraint `(:Company {name})` is checked when the `Company` label is added, not when the node is created. By this point, a Company node with that name already exists.

### Entity Resolution: Too Late to Help

**File:** `neo4j_graphrag/experimental/components/resolver.py`

The SinglePropertyExactMatchResolver runs AFTER the writer:

```python
# Pipeline connections (simplified)
connections = [
    ("pruner", "writer"),      # Pruner feeds writer
    ("writer", "resolver"),    # Writer feeds resolver (if enabled)
]
```

Entity resolution uses `apoc.refactor.mergeNodes` to consolidate duplicates:

```cypher
WITH prop, lab, collect(entity) AS entities
CALL apoc.refactor.mergeNodes(entities, {properties:'discard', mergeRels:true})
```

**The problem:** If the writer fails with a constraint violation, the resolver never runs. The library assumes either:
- No database constraints exist, OR
- Duplicates are successfully created and resolution cleans them up

### Schema Constraints: Not Enforced by Library

The library's GraphSchema supports defining constraints:

```python
class ConstraintType(BaseModel):
    type: Literal["UNIQUENESS"]
    node_type: str
    property_name: str
```

However, these are **metadata only** - the library does NOT:
- Create actual Neo4j constraints from the schema
- Check for existing database constraints before writing
- Warn about potential constraint conflicts

If you manually create constraints in Neo4j, the library is unaware and will fail unexpectedly.

---

## Part 2: Project-Specific Issues

### Issue 1: Manual Constraint Creation

The `01_full_data_load.py` script creates a uniqueness constraint:

```python
session.run("""
    CREATE CONSTRAINT company_name IF NOT EXISTS
    FOR (c:Company) REQUIRE c.name IS UNIQUE
""")
```

This constraint is created BEFORE the pipeline runs, causing conflicts when the KGWriter tries to create duplicate Company nodes.

### Issue 2: CSV Metadata Pre-Loading (Original Issue)

The original CONFLICT.md described a different issue:
- CSV creates "APPLE INC" (uppercase)
- LLM extracts "Apple Inc." (title case)
- These are treated as different entities

This is a **secondary issue** - the name normalization utility addresses it, but the primary issue is the library's CREATE vs MERGE behavior.

### Issue 3: Incorrect CSV Data

The CSV contains data quality issues:

```csv
name,ticker
APPLE INC,INTC  # Wrong! Apple's ticker is AAPL, not INTC
```

This causes incorrect metadata to be associated with companies.

---

## Part 3: Proposed Solutions

### Solution A: Remove the Uniqueness Constraint (Quick Fix)

**Effort:** Low
**Risk:** Medium (allows temporary duplicates)

Remove the constraint and rely on entity resolution:

```python
# In 01_full_data_load.py
# Remove or comment out:
# session.run("""
#     CREATE CONSTRAINT company_name IF NOT EXISTS
#     FOR (c:Company) REQUIRE c.name IS UNIQUE
# """)
```

**Pros:**
- Works immediately
- Entity resolution will merge duplicates

**Cons:**
- Duplicates exist until resolution runs
- If resolution fails, duplicates remain
- Query performance may degrade without constraint/index

### Solution B: Pre-Deduplicate Entities Before Writing (Project Fix)

**Effort:** Medium
**Risk:** Low

Create a custom component that deduplicates entities before they reach the writer. This could be a custom Pruner or a post-processor.

```python
from collections import defaultdict

def deduplicate_entities(graph):
    """Merge entities with the same label and name."""
    seen = {}  # (label, name) -> entity
    for entity in graph.entities:
        key = (entity.label, entity.properties.get("name"))
        if key in seen:
            # Merge properties into existing entity
            seen[key].properties.update(entity.properties)
        else:
            seen[key] = entity
    graph.entities = list(seen.values())
    return graph
```

**Pros:**
- Works with existing constraints
- No library modifications needed

**Cons:**
- Requires custom pipeline code
- Must handle relationship references to merged entities

### Solution C: Modify KGWriter to Use MERGE (Library Fix)

**Effort:** High
**Risk:** Low (but requires library changes)

Change the Cypher query in `neo4j_queries.py` to use MERGE:

```cypher
UNWIND $rows AS row
MERGE (n:Company {name: row.properties.name})
ON CREATE SET n += row.properties, n:__KGBuilder__, n.__tmp_internal_id = row.id
ON MATCH SET n += row.properties
...
```

**Challenges:**
- Different node types have different identifying properties
- MERGE requires knowing which property is the "key"
- Would need schema to specify merge keys per node type

**Pros:**
- Solves the problem at the source
- Works with any constraints

**Cons:**
- Requires library modification
- More complex query logic
- Performance implications of MERGE vs CREATE

### Solution D: Move Entity Resolution Before Writing (Library Fix)

**Effort:** High
**Risk:** Medium

Restructure the pipeline to deduplicate in-memory before writing:

```
Extractor → In-Memory Resolution → Writer → (optional DB Resolution)
```

This would require:
1. Collecting all extracted entities across chunks
2. Deduplicating in Python before any database writes
3. Writing only unique entities

**Pros:**
- Most architecturally sound solution
- Works with any constraints
- Reduces database operations

**Cons:**
- Significant library restructure
- Memory usage for large documents
- Changes pipeline semantics

### Solution E: Use Constraint-Aware Writing (Library Enhancement)

**Effort:** High
**Risk:** Low

Enhance KGWriter to:
1. Query existing database constraints on startup
2. For constrained properties, check existence before creating
3. Use MERGE for constrained node types, CREATE for others

```python
class KGWriter:
    def __init__(self, driver, ...):
        self.constraints = self._discover_constraints()

    def _discover_constraints(self):
        result = driver.execute_query(
            "SHOW CONSTRAINTS YIELD labelsOrTypes, properties, type"
        )
        return {(label, prop) for label, prop, type in result if type == 'UNIQUENESS'}

    def _upsert_nodes(self, nodes, ...):
        for node in nodes:
            if self._has_constraint(node.label, 'name'):
                self._merge_node(node)
            else:
                self._create_node(node)
```

**Pros:**
- Automatic constraint discovery
- Works with any database setup
- Backward compatible

**Cons:**
- Complex implementation
- Performance overhead for constraint checking

---

## Recommended Approach

### For This Demo Project (Immediate)

1. **Remove the uniqueness constraint** from `01_full_data_load.py`
2. **Keep entity resolution enabled** (`perform_entity_resolution=True`)
3. **Add a post-processing step** to verify no duplicates remain

```python
# After pipeline.run_async()
with driver.session() as session:
    # Check for any remaining duplicates
    result = session.run("""
        MATCH (c:Company)
        WITH c.name AS name, collect(c) AS nodes, count(*) AS cnt
        WHERE cnt > 1
        RETURN name, cnt
    """)
    for record in result:
        logger.warning(f"Duplicate Company found: {record['name']} ({record['cnt']} nodes)")
```

### For Production Use (Long-term)

1. **Contribute to neo4j-graphrag-python:**
   - Add in-memory entity deduplication before writing
   - Make KGWriter constraint-aware
   - Document the constraint interaction clearly

2. **Create a custom pipeline component** for entity deduplication that runs before the writer

3. **Use CIK (SEC identifier) as the unique key** instead of company name - this avoids the name variation problem entirely

---

## Summary Table

| Solution | Effort | Where | Solves Root Cause? |
|----------|--------|-------|-------------------|
| A: Remove constraint | Low | Project | No (workaround) |
| B: Pre-deduplicate | Medium | Project | Partially |
| C: Use MERGE | High | Library | Yes |
| D: In-memory resolution | High | Library | Yes |
| E: Constraint-aware writing | High | Library | Yes |

---

## Appendix: Error Trace Explained

```
ERROR: IndexEntryConflictException{propertyValues=( String("Apple Inc.") ), addedEntityId=-1, existingEntityId=52}
```

- `propertyValues: "Apple Inc."` - The conflicting property value
- `addedEntityId=-1` - The new node being created (not yet assigned an ID)
- `existingEntityId=52` - The node that already exists with this value

The error occurs in `apoc.create.addLabels` because:
1. Node 52 already has label `Company` and `name="Apple Inc."`
2. The new node also wants `Company` label with `name="Apple Inc."`
3. The uniqueness constraint prevents this

---

## Resolution: Library Fix Implemented

**Solution C was implemented** in the neo4j-graphrag-python library. The changes include:

### Library Changes

1. **New function `upsert_node_query_merge()`** in `neo4j_queries.py`:
   - Uses `apoc.merge.node` instead of `CREATE` + `apoc.create.addLabels`
   - Merges nodes based on labels + identifying property (default: `name`)

2. **New parameters in `Neo4jWriter`**:
   - `use_merge: bool = True` - Use MERGE by default
   - `merge_property: str = "name"` - Property to merge on

3. **Documentation**: See `CREATE_MERGE.md` in the library root.

### Project Changes

The `01_full_data_load.py` script was simplified:

1. **Restored original flow**: CSV metadata loaded BEFORE extraction
2. **Kept uniqueness constraint**: Now works because library uses MERGE
3. **Removed workarounds**: No more constraint dropping or post-extraction metadata merge
4. **Kept name normalization**: Still useful for CSV → LLM name consistency

### How It Works Now

```
1. Clear database (optional)
2. Create Company nodes from CSV with normalized names + uniqueness constraint
3. Run SimpleKGPipeline on PDFs
   - Library uses MERGE by default
   - Extracted "Apple Inc." merges with existing node (no conflict!)
4. Create AssetManager relationships
```

### Verification

Run the pipeline:
```bash
uv run python -m solutions.01_full_data_load --limit 1 --clear
```

Expected: No `IndexEntryConflictException` errors.
