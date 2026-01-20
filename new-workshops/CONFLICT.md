# Entity Conflict Issue in Full Data Load

This document describes a conflict that occurs when running the full data load pipeline and proposes solutions.

---

## The Problem

When running the full data load with metadata enabled, a unique constraint violation occurs:

```
Node(52) already exists with label `Company` and property `name` = 'Apple Inc.'
```

The pipeline fails partway through processing because it cannot create a Company node that already exists.

---

## Root Cause

The conflict happens because Company nodes are created twice through different paths:

**Path One: CSV Metadata Loading**

The script reads Company_Filings.csv and creates Company nodes before entity extraction begins. These nodes have names exactly as they appear in the CSV, such as "APPLE INC" in uppercase.

**Path Two: LLM Entity Extraction**

SimpleKGPipeline reads the PDF and asks Claude to extract entities. Claude identifies companies mentioned in the text and returns them with natural casing, such as "Apple Inc." with title case.

**The Collision**

A unique constraint exists on Company.name to prevent duplicate companies. When the pipeline tries to create "Apple Inc." but "APPLE INC" already exists, Neo4j rejects the operation because the constraint considers these different values.

The entity resolution feature in SimpleKGPipeline is designed to merge similar entities, but it runs after the initial node creation attempt fails, so it never gets the chance to resolve the conflict.

---

## Secondary Issue: Incorrect Ticker Mapping

The error log shows metadata with mismatched values:

```
'name': 'APPLE INC', 'ticker': 'INTC'
```

INTC is Intel's stock ticker, not Apple's (which is AAPL). This suggests the CSV file has incorrect mappings between company names and their metadata, or the PDF filename to company lookup is returning the wrong record.

---

## Immediate Workarounds

### Option One: Skip Metadata Loading

Run the pipeline without pre-loading CSV metadata. The LLM will extract company information directly from the PDFs.

```
uv run python -m solutions.01_full_data_load --limit 1 --skip-metadata
```

This avoids the conflict entirely because Company nodes are only created through entity extraction.

**Trade-off:** You lose the structured metadata from the CSV (ticker symbols, CIK numbers, CUSIP identifiers) unless Claude extracts them from the PDF text.

### Option Two: Clear Database Before Running

Delete all nodes before running the full data load. This ensures no pre-existing nodes can conflict.

Run in Neo4j Browser:
```
MATCH (n) DETACH DELETE n
```

Then run the pipeline with skip-metadata to avoid recreating the conflict.

### Option Three: Run Metadata Load Separately After Extraction

Reverse the order of operations:

1. Run entity extraction first with skip-metadata
2. Then merge CSV metadata into existing Company nodes using a separate script

This way the LLM creates Company nodes with its preferred casing, and the metadata merge updates those nodes rather than creating new ones.

---

## Longer-Term Solutions

### Solution One: Case-Insensitive Matching in Metadata Loader

Modify the metadata loading step to check for existing Company nodes using case-insensitive matching before creating new ones. If a node with a similar name exists, update it rather than creating a duplicate.

This requires changing the Cypher in create_company_nodes to use a case-insensitive lookup:

Instead of matching on exact name, normalize both the incoming name and existing names to lowercase for comparison, then merge on the normalized value.

### Solution Two: Pre-Normalize Company Names

Standardize company name format before any nodes are created. Choose a canonical format (such as title case) and apply it consistently to both CSV metadata and LLM extraction output.

For CSV metadata, transform names when loading. For LLM output, either post-process the extracted entities or include formatting instructions in the extraction prompt.

### Solution Three: Use Entity Resolution Before Commit

Modify the pipeline to buffer extracted entities and run entity resolution before writing to Neo4j. This would catch the "APPLE INC" vs "Apple Inc." conflict and merge them into a single node before the database write occurs.

This requires changes to the neo4j-graphrag-python library's KGWriter component.

### Solution Four: Remove the Unique Constraint

Drop the unique constraint on Company.name and rely on entity resolution to merge duplicates after the fact. Run a cleanup pass after extraction to consolidate nodes with similar names.

**Trade-off:** This allows duplicates to exist temporarily and requires a post-processing step to clean them up.

### Solution Five: Use a Stable Identifier

Instead of constraining on name, use a stable identifier like CIK number (SEC's Central Index Key) as the unique constraint. Company names vary in format, but CIK numbers are consistent.

This requires:
- Modifying the schema to make CIK the primary identifier
- Ensuring the LLM extracts CIK when available
- Updating the metadata loader to merge on CIK

---

## Recommended Approach

For immediate use, run with the skip-metadata flag to avoid the conflict.

For a production-ready solution, implement case-insensitive matching in the metadata loader combined with using CIK as the stable identifier. This handles the name variation problem and provides a reliable way to link extracted entities to structured metadata.

---

## CSV Data Quality Issue

The ticker mismatch (Apple showing as INTC) should be investigated separately. Possible causes:

1. The CSV file has incorrect data in some rows
2. The filename-to-company lookup in load_company_metadata is matching the wrong record
3. The PDF filenames don't correspond to the expected companies

Review the Company_Filings.csv to verify the name, ticker, and path columns are correctly aligned.
