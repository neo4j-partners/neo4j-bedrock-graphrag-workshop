"""
Test script for validating MERGE behavior and graph structure in Neo4jWriter.

This script tests that:
1. The neo4j-graphrag-python library correctly uses MERGE for node creation
2. The knowledge graph is properly structured after pipeline execution
3. Relationships follow the defined schema
4. Embeddings and properties are correctly stored

Run with: uv run python -m solutions.01_test_full_data_load

Options:
  --graph-only    Only run graph structure validation (skip MERGE unit tests)
  --full          Run full pipeline test (clears DB, runs pipeline, validates)

This is a plain Python test file (no pytest required).
"""

import sys
import argparse
from neo4j import GraphDatabase

from .config import Neo4jConfig


def test_merge_query_generation():
    """Test that the merge query is generated correctly."""
    print("\n=== Test: Merge Query Generation ===")

    from neo4j_graphrag.neo4j_queries import upsert_node_query_merge

    # Test with Neo4j 5.23+ syntax
    query = upsert_node_query_merge(support_variable_scope_clause=True)

    # Verify key components
    checks = [
        ("Uses apoc.merge.node", "apoc.merge.node" in query),
        ("Merges on first label only", "[row.labels[0]]" in query),
        ("Uses identity props", "{`name`: row.properties.`name`}" in query),
        ("Adds labels after merge", "apoc.create.addLabels" in query),
        ("Sets __tmp_internal_id", "__tmp_internal_id" in query),
    ]

    passed = 0
    for name, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")
        if result:
            passed += 1

    print(f"\n  Result: {passed}/{len(checks)} checks passed")
    return passed == len(checks)


def test_merge_with_preexisting_nodes(driver):
    """Test that MERGE finds pre-existing nodes created outside the pipeline."""
    print("\n=== Test: Merge with Pre-existing Nodes ===")

    with driver.session() as session:
        # Clean up test data
        session.run("MATCH (n:TestCompany) DETACH DELETE n")

        # Create a pre-existing node (like CSV import would do)
        session.run("""
            CREATE (c:TestCompany {name: 'Acme Corp'})
        """)

        # Verify it exists
        result = session.run("""
            MATCH (c:TestCompany {name: 'Acme Corp'})
            RETURN count(c) AS count, elementId(c) AS id
        """)
        record = result.single()
        original_id = record["id"]
        print(f"  Created pre-existing node with ID: {original_id}")

        # Now simulate what the library does: merge on primary label
        session.run("""
            CALL apoc.merge.node(
                ['TestCompany'],
                {name: 'Acme Corp'},
                {name: 'Acme Corp', extracted: true},
                {extracted: true}
            ) YIELD node
            WITH node
            CALL apoc.create.addLabels(node, ['__Entity__', '__KGBuilder__']) YIELD node AS n
            RETURN n
        """)

        # Verify only one node exists
        result = session.run("""
            MATCH (c:TestCompany {name: 'Acme Corp'})
            RETURN count(c) AS count, elementId(c) AS id, c.extracted AS extracted, labels(c) AS labels
        """)
        record = result.single()

        checks = [
            ("Only one node exists", record["count"] == 1),
            ("Same node ID (merged, not new)", record["id"] == original_id),
            ("Property was updated", record["extracted"] == True),
            ("Has __Entity__ label", "__Entity__" in record["labels"]),
            ("Has __KGBuilder__ label", "__KGBuilder__" in record["labels"]),
        ]

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        # Cleanup
        session.run("MATCH (n:TestCompany) DETACH DELETE n")

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_merge_deduplication(driver):
    """Test that MERGE deduplicates entities extracted from multiple chunks."""
    print("\n=== Test: Merge Deduplication ===")

    with driver.session() as session:
        # Clean up test data
        session.run("MATCH (n:TestEntity) DETACH DELETE n")

        # Simulate extracting same entity from 3 different chunks
        # Each extraction has a different internal ID but same name
        rows = [
            {"labels": ["TestEntity"], "id": "chunk1-entity1", "properties": {"name": "Apple Inc.", "chunk": 1}},
            {"labels": ["TestEntity"], "id": "chunk2-entity1", "properties": {"name": "Apple Inc.", "chunk": 2}},
            {"labels": ["TestEntity"], "id": "chunk3-entity1", "properties": {"name": "Apple Inc.", "chunk": 3}},
        ]

        print(f"  Simulating {len(rows)} extractions of 'Apple Inc.' from different chunks...")

        # Use the same query pattern as the library
        for row in rows:
            session.run("""
                CALL apoc.merge.node(
                    [$label],
                    {name: $name},
                    $props,
                    $props
                ) YIELD node AS n
                WITH n
                CALL apoc.create.addLabels(n, $all_labels) YIELD node
                SET n.__tmp_internal_id = $id
                RETURN node
            """,
                label=row["labels"][0],
                name=row["properties"]["name"],
                props=row["properties"],
                all_labels=row["labels"] + ["__KGBuilder__"],
                id=row["id"]
            )

        # Verify only one node exists
        result = session.run("""
            MATCH (e:TestEntity {name: 'Apple Inc.'})
            RETURN count(e) AS count, e.chunk AS lastChunk
        """)
        record = result.single()

        checks = [
            ("Only one node created", record["count"] == 1),
            ("Last chunk property preserved", record["lastChunk"] == 3),
        ]

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        # Cleanup
        session.run("MATCH (n:TestEntity) DETACH DELETE n")

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_merge_with_uniqueness_constraint(driver):
    """Test that MERGE works with uniqueness constraints (the original problem)."""
    print("\n=== Test: Merge with Uniqueness Constraint ===")

    with driver.session() as session:
        # Clean up
        try:
            session.run("DROP CONSTRAINT test_company_name IF EXISTS")
        except:
            pass
        session.run("MATCH (n:ConstrainedCompany) DETACH DELETE n")

        # Create uniqueness constraint
        session.run("""
            CREATE CONSTRAINT test_company_name IF NOT EXISTS
            FOR (c:ConstrainedCompany) REQUIRE c.name IS UNIQUE
        """)
        print("  Created uniqueness constraint on ConstrainedCompany.name")

        # Create initial node (like CSV import)
        session.run("""
            CREATE (c:ConstrainedCompany {name: 'Test Corp', source: 'csv'})
        """)
        print("  Created initial node from 'CSV'")

        # Try to merge (simulating LLM extraction) - this should NOT throw error
        error_occurred = False
        try:
            session.run("""
                CALL apoc.merge.node(
                    ['ConstrainedCompany'],
                    {name: 'Test Corp'},
                    {name: 'Test Corp', source: 'llm'},
                    {source: 'llm'}
                ) YIELD node
                WITH node
                CALL apoc.create.addLabels(node, ['__Entity__', '__KGBuilder__']) YIELD node AS n
                RETURN n
            """)
            print("  MERGE succeeded (no constraint violation)")
        except Exception as e:
            error_occurred = True
            print(f"  MERGE failed with error: {e}")

        # Verify state
        result = session.run("""
            MATCH (c:ConstrainedCompany {name: 'Test Corp'})
            RETURN count(c) AS count, c.source AS source
        """)
        record = result.single()

        checks = [
            ("No constraint violation", not error_occurred),
            ("Only one node exists", record["count"] == 1),
            ("Source updated to 'llm'", record["source"] == "llm"),
        ]

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        # Cleanup
        session.run("DROP CONSTRAINT test_company_name IF EXISTS")
        session.run("MATCH (n:ConstrainedCompany) DETACH DELETE n")

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_kg_writer_parameters():
    """Test that Neo4jWriter has the new merge parameters."""
    print("\n=== Test: KGWriter Parameters ===")

    from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter
    import inspect

    # Check __init__ signature
    sig = inspect.signature(Neo4jWriter.__init__)
    params = sig.parameters

    checks = [
        ("Has 'use_merge' parameter", "use_merge" in params),
        ("Has 'merge_property' parameter", "merge_property" in params),
        ("use_merge defaults to True", params.get("use_merge") and params["use_merge"].default == True),
        ("merge_property defaults to 'name'", params.get("merge_property") and params["merge_property"].default == "name"),
    ]

    passed = 0
    for name, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")
        if result:
            passed += 1

    print(f"\n  Result: {passed}/{len(checks)} checks passed")
    return passed == len(checks)


def test_validation_skips_nodes_without_merge_property():
    """Test that entity nodes without merge_property are skipped, but lexical nodes use CREATE."""
    print("\n=== Test: Validation Separates Merge and Create Nodes ===")

    from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter
    from neo4j_graphrag.experimental.components.types import Neo4jNode, LexicalGraphConfig

    config = Neo4jConfig()
    driver = GraphDatabase.driver(config.uri, auth=(config.username, config.password))

    try:
        writer = Neo4jWriter(driver=driver, use_merge=True, merge_property="name")
        lexical_config = LexicalGraphConfig()  # Default: Chunk, Document are lexical

        # Create test nodes:
        # - 2 entity nodes with 'name' -> should MERGE
        # - 2 Chunk nodes without 'name' -> should CREATE (lexical graph)
        # - 1 entity node without 'name' -> should be SKIPPED
        nodes = [
            Neo4jNode(id="1", label="Company", properties={"name": "Good Corp"}),
            Neo4jNode(id="2", label="Chunk", properties={"text": "Some text", "index": 0}),
            Neo4jNode(id="3", label="Company", properties={"name": "Another Corp"}),
            Neo4jNode(id="4", label="Chunk", properties={"text": "More text", "index": 1}),
            Neo4jNode(id="5", label="Product", properties={"description": "No name"}),  # Missing 'name'
        ]

        # Call validation with lexical config
        merge_nodes, create_nodes, skipped_count = writer._validate_merge_property(nodes, lexical_config)

        checks = [
            ("Returns 2 merge nodes (entities with name)", len(merge_nodes) == 2),
            ("Returns 2 create nodes (Chunks)", len(create_nodes) == 2),
            ("Skipped 1 entity node (missing name)", skipped_count == 1),
            ("Merge nodes have 'name' property", all("name" in n.properties for n in merge_nodes)),
            ("Create nodes are Chunks", all(n.label == "Chunk" for n in create_nodes)),
        ]

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)
    finally:
        driver.close()


# =============================================================================
# GRAPH STRUCTURE VALIDATION TESTS
# =============================================================================

def test_graph_node_counts(driver):
    """Validate node counts by label."""
    print("\n=== Test: Graph Node Counts ===")

    with driver.session() as session:
        # Get all node labels and counts
        result = session.run("""
            MATCH (n)
            WITH labels(n) AS lbls, count(n) AS cnt
            UNWIND lbls AS label
            RETURN label, sum(cnt) AS count
            ORDER BY count DESC
        """)

        counts = {record["label"]: record["count"] for record in result}
        print("  Node counts by label:")
        for label, count in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"    {label}: {count}")

        # Define expected labels based on schema
        expected_labels = ["Company", "RiskFactor", "Product", "Executive", "FinancialMetric"]
        infrastructure_labels = ["__KGBuilder__", "__Entity__", "Chunk", "Document"]

        checks = [
            ("Has Company nodes", counts.get("Company", 0) > 0),
            ("Has __KGBuilder__ nodes", counts.get("__KGBuilder__", 0) > 0),
            ("Total nodes > 0", sum(counts.values()) > 0),
        ]

        # Check for entity nodes (at least one type should exist)
        entity_exists = any(counts.get(label, 0) > 0 for label in expected_labels)
        checks.append(("Has at least one entity type", entity_exists))

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_graph_relationship_counts(driver):
    """Validate relationship counts by type."""
    print("\n=== Test: Graph Relationship Counts ===")

    with driver.session() as session:
        # Get all relationship types and counts
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS type, count(r) AS count
            ORDER BY count DESC
        """)

        counts = {record["type"]: record["count"] for record in result}
        print("  Relationship counts by type:")
        for rel_type, count in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"    {rel_type}: {count}")

        # Expected relationship types from schema
        schema_relationships = ["FACES_RISK", "OFFERS", "HAS_EXECUTIVE", "REPORTS", "COMPETES_WITH", "PARTNERS_WITH"]
        lexical_relationships = ["FROM_CHUNK", "FROM_DOCUMENT", "PART_OF"]

        checks = [
            ("Has relationships", sum(counts.values()) > 0),
            ("Has FROM_CHUNK relationships (provenance)", counts.get("FROM_CHUNK", 0) > 0),
        ]

        # Check if at least one schema relationship exists
        schema_rel_exists = any(counts.get(rel, 0) > 0 for rel in schema_relationships)
        checks.append(("Has at least one schema relationship type", schema_rel_exists))

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_graph_schema_compliance(driver):
    """Validate that relationships connect correct node types per schema."""
    print("\n=== Test: Graph Schema Compliance ===")

    with driver.session() as session:
        # Define expected patterns: (start_label, rel_type, end_label)
        expected_patterns = [
            ("Company", "FACES_RISK", "RiskFactor"),
            ("Company", "OFFERS", "Product"),
            ("Company", "HAS_EXECUTIVE", "Executive"),
            ("Company", "REPORTS", "FinancialMetric"),
            ("Company", "COMPETES_WITH", "Company"),
            ("Company", "PARTNERS_WITH", "Company"),
        ]

        # Check each relationship type for schema violations
        violations = []
        valid_patterns = []

        for start_label, rel_type, end_label in expected_patterns:
            # Check if any relationships of this type exist with wrong node types
            result = session.run(f"""
                MATCH (a)-[r:{rel_type}]->(b)
                WHERE NOT (a:{start_label} AND b:{end_label})
                RETURN count(r) AS violations,
                       collect(DISTINCT [labels(a)[0], labels(b)[0]])[0..3] AS examples
            """)
            record = result.single()

            if record["violations"] > 0:
                violations.append(f"{rel_type}: {record['violations']} violations (e.g., {record['examples']})")
            else:
                # Check if valid relationships exist
                result = session.run(f"""
                    MATCH (a:{start_label})-[r:{rel_type}]->(b:{end_label})
                    RETURN count(r) AS count
                """)
                count = result.single()["count"]
                if count > 0:
                    valid_patterns.append(f"{start_label}-[{rel_type}]->{end_label}: {count}")

        print("  Valid relationship patterns found:")
        for pattern in valid_patterns[:10]:  # Show first 10
            print(f"    {pattern}")

        if violations:
            print("  Schema violations found:")
            for v in violations:
                print(f"    {v}")

        checks = [
            ("No schema violations", len(violations) == 0),
            ("At least one valid pattern exists", len(valid_patterns) > 0),
        ]

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_graph_lexical_structure(driver):
    """Validate the lexical graph structure (Document -> Chunk -> Entity)."""
    print("\n=== Test: Lexical Graph Structure ===")

    with driver.session() as session:
        # Check Document nodes
        doc_result = session.run("""
            MATCH (d:Document)
            RETURN count(d) AS count
        """)
        doc_count = doc_result.single()["count"]

        # Check Chunk nodes
        chunk_result = session.run("""
            MATCH (c:Chunk)
            RETURN count(c) AS count,
                   count(CASE WHEN c.text IS NOT NULL THEN 1 END) AS with_text,
                   count(CASE WHEN c.index IS NOT NULL THEN 1 END) AS with_index
        """)
        chunk_record = chunk_result.single()

        # Check Document-Chunk relationships
        doc_chunk_result = session.run("""
            MATCH (d:Document)<-[:PART_OF]-(c:Chunk)
            RETURN count(DISTINCT d) AS docs_with_chunks,
                   count(c) AS chunks_linked
        """)
        doc_chunk_record = doc_chunk_result.single()

        # Check Entity-Chunk relationships (provenance)
        entity_chunk_result = session.run("""
            MATCH (e:__Entity__)-[:FROM_CHUNK]->(c:Chunk)
            RETURN count(DISTINCT e) AS entities_with_provenance,
                   count(*) AS provenance_links
        """)
        entity_chunk_record = entity_chunk_result.single()

        print(f"  Documents: {doc_count}")
        print(f"  Chunks: {chunk_record['count']} (with text: {chunk_record['with_text']}, with index: {chunk_record['with_index']})")
        print(f"  Documents with chunks: {doc_chunk_record['docs_with_chunks']}")
        print(f"  Entities with provenance: {entity_chunk_record['entities_with_provenance']}")
        print(f"  Provenance links: {entity_chunk_record['provenance_links']}")

        checks = [
            ("Chunks have 'text' property", chunk_record["with_text"] == chunk_record["count"] or chunk_record["count"] == 0),
            ("Chunks have 'index' property", chunk_record["with_index"] == chunk_record["count"] or chunk_record["count"] == 0),
            ("Entities have provenance (FROM_CHUNK)", entity_chunk_record["provenance_links"] > 0 or chunk_record["count"] == 0),
        ]

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_graph_embeddings(driver):
    """Validate that embeddings exist on appropriate nodes."""
    print("\n=== Test: Graph Embeddings ===")

    with driver.session() as session:
        # Check for embedding properties on Chunk nodes
        chunk_emb_result = session.run("""
            MATCH (c:Chunk)
            WHERE c.embedding IS NOT NULL
            RETURN count(c) AS with_embedding
        """)
        chunks_with_emb = chunk_emb_result.single()["with_embedding"]

        # Check for embedding properties on Entity nodes
        entity_emb_result = session.run("""
            MATCH (e:__Entity__)
            WHERE e.embedding IS NOT NULL
            RETURN count(e) AS with_embedding
        """)
        entities_with_emb = entity_emb_result.single()["with_embedding"]

        # Get total counts
        total_result = session.run("""
            MATCH (c:Chunk) WITH count(c) AS chunks
            MATCH (e:__Entity__) WITH chunks, count(e) AS entities
            RETURN chunks, entities
        """)
        totals = total_result.single()

        print(f"  Chunks with embeddings: {chunks_with_emb}/{totals['chunks']}")
        print(f"  Entities with embeddings: {entities_with_emb}/{totals['entities']}")

        # Check embedding dimensions
        dim_result = session.run("""
            MATCH (n)
            WHERE n.embedding IS NOT NULL
            RETURN labels(n)[0] AS label, size(n.embedding) AS dimension
            LIMIT 1
        """)
        dim_record = dim_result.single()
        if dim_record:
            print(f"  Embedding dimension: {dim_record['dimension']}")

        checks = [
            ("Chunks have embeddings", chunks_with_emb > 0 or totals["chunks"] == 0),
        ]

        # Only check entity embeddings if entities exist
        if totals["entities"] > 0:
            # Not all pipelines generate entity embeddings, so this is informational
            if entities_with_emb > 0:
                print(f"  INFO: {entities_with_emb} entities have embeddings")

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_graph_entity_properties(driver):
    """Validate that entities have required properties."""
    print("\n=== Test: Entity Properties ===")

    with driver.session() as session:
        # Check Company nodes for required properties
        company_result = session.run("""
            MATCH (c:Company)
            RETURN count(c) AS total,
                   count(CASE WHEN c.name IS NOT NULL THEN 1 END) AS with_name,
                   count(CASE WHEN c.ticker IS NOT NULL THEN 1 END) AS with_ticker
        """)
        company = company_result.single()

        # Check __Entity__ nodes for name property (the merge key)
        entity_result = session.run("""
            MATCH (e:__Entity__)
            RETURN count(e) AS total,
                   count(CASE WHEN e.name IS NOT NULL THEN 1 END) AS with_name
        """)
        entity = entity_result.single()

        print(f"  Company nodes: {company['total']}")
        print(f"    with name: {company['with_name']}")
        print(f"    with ticker: {company['with_ticker']}")
        print(f"  Entity nodes: {entity['total']}")
        print(f"    with name (merge key): {entity['with_name']}")

        checks = [
            ("All Company nodes have 'name'", company["with_name"] == company["total"] or company["total"] == 0),
            ("All Entity nodes have 'name' (merge key)", entity["with_name"] == entity["total"] or entity["total"] == 0),
        ]

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_graph_no_orphan_entities(driver):
    """Check for orphan entities (entities with no relationships)."""
    print("\n=== Test: No Orphan Entities ===")

    with driver.session() as session:
        # Find entities with no relationships at all
        orphan_result = session.run("""
            MATCH (e:__Entity__)
            WHERE NOT (e)--()
            RETURN count(e) AS orphan_count,
                   collect(e.name)[0..5] AS examples
        """)
        orphan = orphan_result.single()

        # Find entities with no schema relationships (only FROM_CHUNK)
        no_schema_rel_result = session.run("""
            MATCH (e:__Entity__)
            WHERE NOT (e)-[:FACES_RISK|OFFERS|HAS_EXECUTIVE|REPORTS|COMPETES_WITH|PARTNERS_WITH]-()
              AND NOT (e)<-[:FACES_RISK|OFFERS|HAS_EXECUTIVE|REPORTS|COMPETES_WITH|PARTNERS_WITH]-()
            RETURN count(e) AS count
        """)
        no_schema_rel = no_schema_rel_result.single()["count"]

        # Get total entity count
        total_result = session.run("MATCH (e:__Entity__) RETURN count(e) AS total")
        total = total_result.single()["total"]

        print(f"  Total entities: {total}")
        print(f"  Orphan entities (no relationships): {orphan['orphan_count']}")
        if orphan["examples"]:
            print(f"    Examples: {orphan['examples']}")
        print(f"  Entities without schema relationships: {no_schema_rel}")

        # Some orphan entities may be acceptable (e.g., companies mentioned but not the main subject)
        orphan_ratio = orphan["orphan_count"] / total if total > 0 else 0

        checks = [
            ("Less than 10% orphan entities", orphan_ratio < 0.1 or total == 0),
        ]

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "WARN"  # Warning, not failure
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_graph_no_duplicates(driver):
    """Check for duplicate entities that should have been merged."""
    print("\n=== Test: No Duplicate Entities ===")

    with driver.session() as session:
        # Find potential duplicates (same label and name)
        dup_result = session.run("""
            MATCH (e:__Entity__)
            WITH labels(e) AS lbls, e.name AS name, count(e) AS cnt
            WHERE cnt > 1
            RETURN lbls[0] AS label, name, cnt
            ORDER BY cnt DESC
            LIMIT 10
        """)

        duplicates = list(dup_result)

        if duplicates:
            print("  Potential duplicates found:")
            for record in duplicates:
                print(f"    {record['label']}:{record['name']} appears {record['cnt']} times")
        else:
            print("  No duplicate entities found")

        # Check specifically for Company duplicates (most critical)
        company_dup_result = session.run("""
            MATCH (c:Company)
            WITH c.name AS name, count(c) AS cnt
            WHERE cnt > 1
            RETURN name, cnt
        """)
        company_dups = list(company_dup_result)

        checks = [
            ("No duplicate Company nodes", len(company_dups) == 0),
            ("No duplicate entities overall", len(duplicates) == 0),
        ]

        passed = 0
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print(f"\n  Result: {passed}/{len(checks)} checks passed")
        return passed == len(checks)


def test_graph_summary(driver):
    """Print a comprehensive graph summary."""
    print("\n=== Graph Summary ===")

    with driver.session() as session:
        # Get stats with OPTIONAL MATCH to handle missing labels
        total_nodes = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
        total_rels = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
        entities = session.run("OPTIONAL MATCH (e:__Entity__) RETURN count(e) AS count").single()["count"]
        companies = session.run("OPTIONAL MATCH (c:Company) RETURN count(c) AS count").single()["count"]
        chunks = session.run("OPTIONAL MATCH (ch:Chunk) RETURN count(ch) AS count").single()["count"]

        print(f"  Total nodes: {total_nodes}")
        print(f"  Total relationships: {total_rels}")
        print(f"  Entity nodes: {entities}")
        print(f"  Company nodes: {companies}")
        print(f"  Chunk nodes: {chunks}")

        # Calculate ratios
        if chunks > 0:
            entities_per_chunk = entities / chunks
            print(f"  Entities per chunk: {entities_per_chunk:.2f}")

        if entities > 0:
            rels_per_entity = total_rels / entities
            print(f"  Relationships per entity: {rels_per_entity:.2f}")

    return True  # Summary always passes


def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(description="Test MERGE behavior and graph structure")
    parser.add_argument("--graph-only", action="store_true", help="Only run graph structure validation")
    parser.add_argument("--full", action="store_true", help="Run full pipeline test")
    args = parser.parse_args()

    print("=" * 60)
    print("Knowledge Graph Test Suite")
    print("=" * 60)
    print("\nTesting MERGE behavior and graph structure validation.")

    # Initialize Neo4j
    config = Neo4jConfig()
    driver = GraphDatabase.driver(config.uri, auth=(config.username, config.password))

    try:
        driver.verify_connectivity()
        print(f"\nConnected to Neo4j: {config.uri}")
    except Exception as e:
        print(f"\nFailed to connect to Neo4j: {e}")
        sys.exit(1)

    # Run tests
    results = []

    try:
        if not args.graph_only:
            # MERGE behavior tests
            print("\n" + "-" * 60)
            print("PART 1: MERGE Behavior Tests")
            print("-" * 60)
            results.append(("Query Generation", test_merge_query_generation()))
            results.append(("KGWriter Parameters", test_kg_writer_parameters()))
            results.append(("Validation", test_validation_skips_nodes_without_merge_property()))
            results.append(("Merge with Pre-existing Nodes", test_merge_with_preexisting_nodes(driver)))
            results.append(("Merge Deduplication", test_merge_deduplication(driver)))
            results.append(("Merge with Uniqueness Constraint", test_merge_with_uniqueness_constraint(driver)))

        # Graph structure validation tests
        print("\n" + "-" * 60)
        print("PART 2: Graph Structure Validation")
        print("-" * 60)
        results.append(("Node Counts", test_graph_node_counts(driver)))
        results.append(("Relationship Counts", test_graph_relationship_counts(driver)))
        results.append(("Schema Compliance", test_graph_schema_compliance(driver)))
        results.append(("Lexical Structure", test_graph_lexical_structure(driver)))
        results.append(("Embeddings", test_graph_embeddings(driver)))
        results.append(("Entity Properties", test_graph_entity_properties(driver)))
        results.append(("No Orphan Entities", test_graph_no_orphan_entities(driver)))
        results.append(("No Duplicate Entities", test_graph_no_duplicates(driver)))

        # Summary (always runs)
        test_graph_summary(driver)

    finally:
        driver.close()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\nMERGE Behavior Tests:" if not args.graph_only else "")
    for name, result in results[:6] if not args.graph_only else []:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")

    print("\nGraph Structure Tests:")
    start_idx = 0 if args.graph_only else 6
    for name, result in results[start_idx:]:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll tests passed! Knowledge graph is properly structured.")
        sys.exit(0)
    else:
        print("\nSome tests failed. Check output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
