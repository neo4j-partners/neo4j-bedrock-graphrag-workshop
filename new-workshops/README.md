# Neo4j GraphRAG Workshop with AWS Bedrock

**Early Prototype** - This workshop demonstrates an early prototype of using AWS Bedrock for creating data sources for a GraphRAG knowledge graph. It uses a fork of the [neo4j-graphrag-python](https://github.com/neo4j/neo4j-graphrag-python) project that includes Bedrock integration.

## Prerequisites

### 1. Clone the neo4j-graphrag-python Fork

This workshop requires a local fork of the neo4j-graphrag-python library with Bedrock support. Clone it to your machine:

```bash
# Clone the fork (replace with your fork URL)
git clone https://github.com/YOUR_USERNAME/neo4j-graphrag-python.git ~/projects/neo4j-graphrag-python
```

### 2. Update pyproject.toml to Point to Your Local Clone

After cloning, update the `pyproject.toml` in this directory to point to your local copy. Open `new-workshops/pyproject.toml` and find this line:

```toml
"neo4j-graphrag[bedrock] @ file:///Users/ryanknight/projects/neo4j-graphrag-python",
```

Replace it with the path to your local clone:

```toml
"neo4j-graphrag[bedrock] @ file:///YOUR/PATH/TO/neo4j-graphrag-python",
```

For example:
- macOS/Linux: `file:///home/username/projects/neo4j-graphrag-python`
- Windows: `file:///C:/Users/username/projects/neo4j-graphrag-python`

### 3. Environment Configuration

Create a `.env` file in this directory with the following variables:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
AWS_REGION=us-east-1
```

The workshop uses sensible defaults for AWS Bedrock models. You can optionally override them:

```
AWS_BEDROCK_INFERENCE_PROFILE_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
AWS_BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
```

### 4. AWS Credentials

AWS credentials must be configured via one of:
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- `~/.aws/credentials` file
- IAM role (if running on AWS infrastructure)

## Quick Start

All commands should be run from the `new-workshops/` directory:

```bash
cd new-workshops

# Install dependencies
uv sync

# Test connections
uv run python -m solutions.test_connection
```

## Lab 01: Data Pipeline (Updated)

Labs 01_xx build the foundation for GraphRAG: loading data, generating embeddings, and extracting entities to create a knowledge graph.

### Step 1: Basic Data Loading

Create Document and Chunk nodes in Neo4j:

```bash
uv run python -m solutions.01_01_data_loading
```

This demonstrates basic data ingestion patterns.

### Step 2: Generate Embeddings

Generate vector embeddings using AWS Bedrock Titan:

```bash
uv run python -m solutions.01_02_embeddings
```

This creates embeddings for semantic search capabilities.

### Step 3: Entity Extraction

Build the knowledge graph using SimpleKGPipeline:

```bash
uv run python -m solutions.01_03_entity_extraction
```

This is the core of the GraphRAG pipeline. It uses Claude Sonnet 4.5 on AWS Bedrock to read text and identify entities and relationships, then stores them in Neo4j as a knowledge graph.

#### What It Does

The entity extraction pipeline takes unstructured text and transforms it into structured graph data. For example, given SEC 10-K filing text about Apple, it identifies:

**Entities** are the things mentioned in the text. The pipeline extracts three types:
- Companies such as Apple Inc.
- Products such as iPhone, Mac, iPad, and their variants
- Services such as AppleCare, Apple Pay, and Cloud Services

**Relationships** describe how entities connect to each other:
- OFFERS_PRODUCT links a company to the products it sells
- OFFERS_SERVICE links a company to the services it provides

**Provenance** tracks where information came from. Each entity links back to the text chunk it was extracted from via FROM_CHUNK relationships. This enables you to trace any fact in the graph back to its source document.

#### How It Works

The SimpleKGPipeline orchestrates the extraction process:

1. The text is split into manageable chunks
2. Each chunk is sent to Claude Sonnet 4.5 with a schema describing what entities and relationships to look for
3. Claude reads the text and returns structured JSON with the entities and relationships it found
4. The pipeline creates nodes and relationships in Neo4j for each extracted item
5. Embeddings are generated for each entity using Amazon Titan, enabling semantic search

#### Schema-Driven Extraction

The extraction is guided by a schema you define. The schema tells the LLM what types of entities to look for, what relationships are valid, and which entity types can connect to which. This keeps the extraction focused and consistent.

For the SEC 10-K example, the schema specifies that Companies can offer Products and Services, but Products cannot offer other Products. This prevents the LLM from creating nonsensical relationships.

#### Expected Results

Running the extraction on the sample Apple 10-K text produces:
- One Company node for Apple Inc.
- Twelve Product nodes including iPhone models, Mac, iPad, and general categories
- Seven Service nodes including AppleCare, Apple Pay, and Cloud Services
- Nineteen relationships connecting Apple to its products and services
- Twenty provenance links connecting entities to their source chunk

The extraction typically completes in under sixty seconds.

### Step 4: Query the Full Dataset

Run queries against the populated knowledge graph:

```bash
uv run python -m solutions.01_04_full_dataset_queries
```

#### Expected Output (Full Dataset)

After running the full data load, the query script should display a summary like this:

```
============================================================
KNOWLEDGE GRAPH SUMMARY
============================================================

NODE COUNTS BY LABEL:
   __KGBuilder__: 3221
   __Entity__: 2795
   RiskFactor: 1073
   FinancialMetric: 844
   Product: 656
   Chunk: 417
   Company: 173
   Executive: 51
   AssetManager: 15
   Document: 9

RELATIONSHIP COUNTS BY TYPE:
   FROM_CHUNK: 3152
   FROM_DOCUMENT: 417
   NEXT_CHUNK: 408
   OWNS: 103
   FACES_RISK: 77
   REPORTS: 73
   OFFERS: 59
   PARTNERS_WITH: 1
   HAS_EXECUTIVE: 1

LEXICAL GRAPH:
   Documents: 9
   Chunks: 417

EXTRACTED ENTITIES BY TYPE:
   RiskFactor: 1073
   FinancialMetric: 844
   Product: 656
   Company: 171
   Executive: 51

PROVENANCE TRACKING:
   Entities with FROM_CHUNK links: 2795
   Total provenance links: 3152

EMBEDDINGS:
   Chunks with embeddings: 417
   Embedding dimensions: 1024

SCHEMA RELATIONSHIPS (Company -> ...):
   Company-[FACES_RISK]->RiskFactor: 77
   Company-[REPORTS]->FinancialMetric: 73
   Company-[OFFERS]->Product: 59
   Company-[PARTNERS_WITH]->Company: 1
   Company-[HAS_EXECUTIVE]->Executive: 1

ASSET MANAGER HOLDINGS:
   Asset managers: 15
   Total holdings: 103

------------------------------------------------------------
TOTALS: 9254 nodes, 4291 relationships
============================================================
```

### Full Data Load (Optional)

Process all SEC 10-K PDFs with `SimpleKGPipeline` + Bedrock:

```bash
# Test with just 1 PDF first
uv run python -m solutions.01_full_data_load --limit 1

# Process all PDFs
uv run python -m solutions.01_full_data_load
```

> **Note:** This requires SEC 10-K PDFs in `~/projects/workshops/workshop-financial-data/form10k-sample/`. Uses `SimpleKGPipeline` with `BedrockLLM` (Claude) and `BedrockEmbeddings` (Titan V2).

## Additional Labs (Reference)

### Retrievers (02_xx)

Explore different retrieval strategies for GraphRAG.

```bash
# 02_01: Vector retriever - semantic search with VectorRetriever
uv run python -m solutions.02_01_vector_retriever

# 02_02: Vector + Cypher - enrich results with graph traversal
uv run python -m solutions.02_02_vector_cypher_retriever

# 02_03: Text2Cypher - natural language to Cypher queries
uv run python -m solutions.02_03_text2cypher_retriever
```

### Agents (03_xx)

Build AI agents with Neo4j tools.

```bash
# 03_01: Simple agent - schema retrieval tool
uv run python -m solutions.03_01_simple_agent

# 03_02: Vector + graph agent - semantic search with graph context
uv run python -m solutions.03_02_vector_graph_agent

# 03_03: Multi-tool agent - schema, vector, and Text2Cypher tools
uv run python -m solutions.03_03_text2cypher_agent
```

### Advanced Search (05_xx)

Fulltext and hybrid search patterns.

```bash
# 05_01: Fulltext search - keyword-based entity search
uv run python -m solutions.05_01_fulltext_search

# 05_02: Hybrid search - combine vector and fulltext
uv run python -m solutions.05_02_hybrid_search
```

## Architecture

- **AWS Bedrock** - LLM (Claude 4.5 Sonnet via inference profile) and embeddings (Titan V2)
- **neo4j-graphrag-python** - GraphRAG retrievers and pipelines (local fork)
- **Neo4j** - Graph database with vector search

## AWS Bedrock Configuration

### Inference Profiles vs Direct Model Access

AWS Bedrock offers two ways to invoke models:

| Approach | Description | Use Case |
|----------|-------------|----------|
| **Direct Model Access** | Invoke models directly in a single Region | Simple single-Region inference |
| **Inference Profiles** | Define model + Regions for routing requests | Cost tracking, metrics, cross-Region |

**Why Claude 4.5 Sonnet requires an inference profile:**

Newer models like Claude 4.5 Sonnet only support inference profile access (not direct on-demand). This provides:

- **Usage Metrics**: CloudWatch logs for model invocation metrics
- **Cost Tracking**: Attach tags for billing analysis with AWS cost allocation
- **Cross-Region Inference**: Distribute requests across multiple AWS Regions for increased throughput
- **Resilience**: Failover capabilities across Regions

### Regional Inference Profile IDs

| Region | Inference Profile ID |
|--------|---------------------|
| US | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| EU | `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| APAC | `apac.anthropic.claude-sonnet-4-5-20250929-v1:0` |

### Model Configuration Example

```python
from neo4j_graphrag.llm import BedrockLLM

llm = BedrockLLM(
    model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
    inference_profile_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name="us-east-1",
    model_params={
        "maxTokens": 4096,
        "temperature": 0,  # Use 0 for deterministic entity extraction
    },
)
```

### Best Practices

1. **Use the Converse API**: Write code once and switch between models easily. The `BedrockLLM` class uses Converse internally.

2. **Temperature Settings**:
   - Use `temperature: 0` for entity extraction and structured outputs
   - Use `temperature: 0.7-1.0` for creative/conversational tasks
   - Note: Claude 4.5 only supports `temperature` OR `top_p`, not both

3. **Extended Thinking** (for complex reasoning):
   ```python
   model_params={
       "maxTokens": 20000,
       "thinking": {"type": "enabled", "budget_tokens": 16000},
   }
   ```
   Do not set `temperature`, `topP`, or `topK` when using extended thinking.

4. **Pricing**: Costs are calculated based on the price in the Region from which you call the inference profile.

### Sources

- [AWS Bedrock Inference Profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)
- [Supported Regions and Models](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html)
- [Claude Model Parameters](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html)
- [Introducing Claude Sonnet 4.5 in Amazon Bedrock](https://aws.amazon.com/blogs/aws/introducing-claude-sonnet-4-5-in-amazon-bedrock-anthropics-most-intelligent-model-best-for-coding-and-complex-agents/)
- [Optimizing Claude Models on Bedrock](https://repost.aws/articles/ARRfe9jE4dQmK8Y2oMYMqbfQ/how-to-optimize-workload-performance-when-using-anthropic-claude-models-on-bedrock)

## Developing with Local neo4j-graphrag-python

When making changes to the local `neo4j-graphrag-python` library, you need to reinstall it for changes to take effect.

### Force Reinstall After Library Changes

```bash
# From the new-workshops/ directory
uv pip install --force-reinstall /path/to/neo4j-graphrag-python

# Example with absolute path
uv pip install --force-reinstall ~/projects/neo4j-graphrag-python
```

**Why `--force-reinstall`?** The `uv sync` command caches installed packages. Even if you modify the library source code, `uv sync` won't detect changes because the package path hasn't changed. Use `--force-reinstall` to ensure your latest changes are picked up.

### Verify Installation

Check that your changes are installed:

```bash
# Verify a specific function or class exists
uv run python -c "from neo4j_graphrag.neo4j_queries import upsert_node_query_merge; print('OK')"

# Print the generated query to verify changes
uv run python -c "from neo4j_graphrag.neo4j_queries import upsert_node_query_merge; print(upsert_node_query_merge(True))"
```

### Run Tests

After making library changes, run the test suite:

```bash
# Run all tests (MERGE behavior + graph structure)
uv run python -m solutions.01_test_full_data_load

# Run only graph structure validation (faster)
uv run python -m solutions.01_test_full_data_load --graph-only
```

## Test Suite: What It Tests and How

The test file `solutions/01_test_full_data_load.py` validates two things: that the MERGE fix works correctly, and that the knowledge graph is properly structured after running the pipeline.

### Part 1: MERGE Behavior Tests

These tests verify that the library correctly prevents duplicate nodes.

**Query Generation Test**
Checks that the Cypher query is built correctly. The query must use `apoc.merge.node` instead of `CREATE`, merge on only the primary label (like `Company`), and add auxiliary labels afterward. This is important because merging on all labels would fail to find pre-existing nodes.

**KGWriter Parameters Test**
Confirms that the `Neo4jWriter` class has the new parameters `use_merge` and `merge_property`, and that they default to `True` and `"name"` respectively. This ensures the fix is enabled by default.

**Validation Test**
Tests that the library correctly separates nodes into three categories:
- Entity nodes that have a `name` property go through MERGE
- Lexical graph nodes (Chunk, Document) go through CREATE because each chunk is unique
- Entity nodes missing the `name` property are skipped with a warning

This prevents the library from trying to merge Chunk nodes on a non-existent `name` property.

**Pre-existing Nodes Test**
Creates a Company node directly in Neo4j (simulating a CSV import), then runs the same merge logic the library uses. Verifies that the merge finds and updates the existing node instead of creating a duplicate. The test checks that the node ID stays the same after merge.

**Deduplication Test**
Simulates what happens when the LLM extracts the same entity from multiple document chunks. Creates three rows for "Apple Inc." with different internal IDs (like three different chunks mentioning Apple). Verifies that only one node is created in the database.

**Uniqueness Constraint Test**
This is the original problem that started everything. Creates a uniqueness constraint on `Company.name`, creates an initial Company node, then tries to merge another Company with the same name. The test passes if no constraint violation occurs.

### Part 2: Graph Structure Validation

These tests examine the actual graph after running the pipeline to verify it was built correctly.

**Node Counts Test**
Queries the database to count nodes by label. Checks that Company nodes exist, that the `__KGBuilder__` infrastructure label exists, and that at least one entity type (Company, Product, RiskFactor, etc.) was extracted. This catches cases where the pipeline ran but failed to create any entities.

**Relationship Counts Test**
Counts relationships by type. Checks that relationships exist in general, that `FROM_CHUNK` relationships exist (which track where each entity was extracted from), and that at least one schema relationship type exists (like `FACES_RISK` or `OFFERS`). Missing `FROM_CHUNK` relationships would indicate the provenance tracking is broken.

**Schema Compliance Test**
Verifies that relationships connect the correct node types according to the schema. For example, `FACES_RISK` should only go from Company to RiskFactor, never from Product to Executive. The test queries each relationship type and checks for violations where the start or end node has the wrong label.

**Lexical Structure Test**
Examines the document-chunk-entity chain. Checks that Chunk nodes have `text` and `index` properties, and that entities are linked to chunks via `FROM_CHUNK` relationships. This provenance chain is essential for RAG applications that need to cite sources.

**Embeddings Test**
Verifies that Chunk nodes have vector embeddings. Checks the count of chunks with embeddings and reports the embedding dimension (typically 1024 for Titan). Missing embeddings would break vector similarity search.

**Entity Properties Test**
Confirms that all Company nodes have a `name` property and all entities have the merge key property. Nodes missing the `name` property would have been skipped during merge, which could indicate extraction issues.

**Orphan Entities Test**
Looks for entities that have no relationships at all. Some orphans are acceptable (a company mentioned in passing), but more than 10% orphans suggests the LLM failed to connect entities properly. The test reports examples of orphan entities for investigation.

**No Duplicates Test**
The final verification that MERGE worked. Searches for any nodes with the same label and name that appear more than once. Finding duplicates would indicate the MERGE logic failed somewhere.

### Understanding the Output

When you run the tests, each test prints detailed information:

```
=== Test: Graph Node Counts ===
  Node counts by label:
    __KGBuilder__: 245
    __Entity__: 217
    RiskFactor: 118
    Product: 47
    Chunk: 27
    Company: 15
  PASS: Has Company nodes
  PASS: Has __KGBuilder__ nodes
  PASS: Total nodes > 0
  PASS: Has at least one entity type

  Result: 4/4 checks passed
```

The node counts tell you what was extracted. In this example, the LLM found 118 risk factors, 47 products, and 45 financial metrics from the SEC filing. The 27 Chunk nodes mean the document was split into 27 pieces for processing.

The graph summary at the end shows overall statistics:

```
=== Graph Summary ===
  Total nodes: 268
  Total relationships: 382
  Entity nodes: 217
  Company nodes: 15
  Chunk nodes: 27
  Entities per chunk: 8.04
  Relationships per entity: 1.76
```

"Entities per chunk" tells you how many entities the LLM extracted from each text chunk on average. "Relationships per entity" indicates how connected the graph is. Higher numbers generally mean richer extraction.

## File Structure

```
new-workshops/
├── pyproject.toml              # Dependencies (uses local neo4j-graphrag fork)
├── .env                        # Configuration (not committed)
├── README.md
└── solutions/
    ├── __init__.py
    ├── config.py               # Shared configuration
    ├── test_connection.py      # Connection test
    ├── name_utils.py           # Company name normalization
    ├── 01_01_data_loading.py   # Demo: basic data loading
    ├── 01_02_embeddings.py
    ├── 01_03_entity_extraction.py
    ├── 01_04_full_dataset_queries.py
    ├── 01_full_data_load.py    # Full PDF processing with SimpleKGPipeline
    ├── 01_test_full_data_load.py  # MERGE behavior test suite
    ├── 02_01_vector_retriever.py
    ├── 02_02_vector_cypher_retriever.py
    ├── 02_03_text2cypher_retriever.py
    ├── 03_01_simple_agent.py
    ├── 03_02_vector_graph_agent.py
    ├── 03_03_text2cypher_agent.py
    ├── 05_01_fulltext_search.py
    └── 05_02_hybrid_search.py
```

---

## Lessons Learned: Entity Deduplication in KG Pipelines

During development of this workshop, we encountered and resolved a significant issue with entity duplication. This section documents the problem, root cause analysis, and solution for future reference.

### The Problem

When running `01_full_data_load.py`, the pipeline failed with:

```
IndexEntryConflictException: Node already exists with label `Company` and property `name` = 'Apple Inc.'
```

### Root Cause Analysis

The issue had multiple layers:

1. **Document Chunking Creates Duplicate Extractions**
   - Documents are split into chunks (e.g., 2000 characters each)
   - The LLM extracts entities from each chunk independently
   - If "Apple Inc." appears in chunks 1, 3, and 7, it's extracted three times
   - Each extraction has a unique internal ID

2. **Library Used CREATE Instead of MERGE**
   - The original `KGWriter` used Cypher `CREATE` statements
   - This attempted to create three separate "Apple Inc." nodes
   - With a uniqueness constraint on `Company.name`, the second creation failed

3. **Entity Resolution Runs Too Late**
   - The pipeline has an entity resolution step, but it runs AFTER the writer
   - The constraint violation occurs at write time, before resolution can help

4. **Label Mismatch Prevented Merging**
   - Even after switching to `apoc.merge.node`, merging failed
   - Pre-existing nodes (from CSV) had only `Company` label
   - Extracted nodes had `['Company', '__Entity__']` labels
   - `apoc.merge.node(['Company', '__Entity__'], ...)` couldn't find nodes with only `Company` label

### The Solution

We modified the `neo4j-graphrag-python` library to:

1. **Use MERGE by default** (`use_merge=True` in `Neo4jWriter`)
2. **Merge on primary label only** - Use `[row.labels[0]]` (e.g., `['Company']`) for matching
3. **Add auxiliary labels after merge** - Labels like `__Entity__` and `__KGBuilder__` are added post-merge

The final query pattern:

```cypher
-- Merge on primary label only (finds pre-existing nodes)
CALL apoc.merge.node(['Company'], {name: 'Apple Inc.'}, props, props) YIELD node
-- Add auxiliary labels afterward
CALL apoc.create.addLabels(node, ['Company', '__Entity__', '__KGBuilder__'])
```

### Key Takeaways

| Lesson | Details |
|--------|---------|
| **CREATE vs MERGE** | Always use MERGE for entities that may be extracted multiple times |
| **Label Strategy** | Merge on semantic labels (Company), add technical labels (__KGBuilder__) afterward |
| **Pre-existing Data** | Design for integration with nodes created outside the pipeline |
| **Constraint Timing** | Uniqueness constraints are checked at write time, not resolution time |
| **uv Caching** | Use `--force-reinstall` when developing local packages |
| **APOC Required** | Dynamic labels require `apoc.merge.node` (native MERGE doesn't support parameterized labels) |

### Related Documentation

- `CONFLICT_V2.md` - Detailed root cause analysis
- `CREATE_MERGE.md` (in neo4j-graphrag-python) - Library changes documentation
- `01_test_full_data_load.py` - Test suite validating MERGE behavior
