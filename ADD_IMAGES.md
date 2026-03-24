# Add Diagram Images to Site Pages

Eight architectural diagrams exist as excalidraw files in `images/` with exported PNGs in `site/modules/ROOT/images/`, but none are referenced in any `.adoc` page. Several pages use ASCII art where a proper diagram would be clearer.

## Diagram Inventory

| PNG File | Diagram Title | Content |
|----------|--------------|---------|
| `financial-data-model.png` | SEC 10-K Financial Data Model | Three-layer schema: Structured (Company, Product, RiskFactor, AssetManager, Executive) + Cross-Link (FILED) + Unstructured (Document, Chunk) with all relationships |
| `workshop-architecture.png` | Workshop Architecture | User Query → AI Agent → Tool Selection (Vector/Text2Cypher/Template) → Neo4j Aura → SEC 10-K Knowledge Graph |
| `graphrag-retrieval-flow.png` | GraphRAG: Graph-Enriched Retrieval | Full retrieval pipeline: User Question → Vector/Hybrid Search → Graph Traversal → Graph-Enriched Context → Answer |
| `lab4-mcp-retrieval-architecture.png` | Lab 4: MCP Retrieval Architecture | Agent → MCP Client → Neo4j MCP Server → three notebook strategies → Neo4j Aura |
| `lab4-graph-enriched-retrieval.png` | SEC 10-K GraphRAG Retrieval Flow | Retrieval pipeline with retrievers (VectorRetriever, VectorCypherRetriever, HybridRetriever) + knowledge graph structure |
| `lab6-data-pipeline.png` | Lab 5: Data Pipeline | CSV Seed Data + 10-K Filing Text → Load/Chunk/Embed → Neo4j Aura (nodes, vector index, fulltext indexes) |
| `lab6-retriever-comparison.png` | Lab 5: Retriever Comparison | Side-by-side VectorRetriever vs VectorCypherRetriever showing what each returns |
| `lab7-mcp-agent-architecture.png` | Lab 6: MCP Agent Architecture | ReAct Loop: User Question → LLM Reasoning → Tool Selection → MCP Tool Call → Neo4j Aura |

Note: "Lab 6" in the codebase = Lab 5 in the site; "Lab 7" in the codebase = Lab 6 in the site.

## Proposed Placements

### 1. `index.adoc` — Two diagrams

**a. Replace ASCII schema (lines 41-48) with `financial-data-model.png`**

The current ASCII Cypher notation is functional but the diagram shows the full three-layer architecture with structured, cross-link, and unstructured layers — much clearer for orientation.

**b. Replace ASCII architecture (lines 52-66) with `workshop-architecture.png`**

The current ASCII tree shows the tool selection flow. The diagram adds color-coding and component grouping.

### 2. `lab4.adoc` — Two diagrams

**a. Add `lab4-mcp-retrieval-architecture.png` after the "At a Glance" block (before "What Is MCP Retrieval?")**

Shows the overall MCP retrieval architecture with the three notebook strategies branching from the MCP server.

**b. Add `lab4-graph-enriched-retrieval.png` in the "Graph-Enriched Search" subsection**

Shows the retrieval flow with knowledge graph node types and retrievers.

### 3. `lab5.adoc` — Three diagrams

**a. Replace ASCII pipeline (line 65) with `lab6-data-pipeline.png` in "The Pipeline" section**

The current one-line text (`01 Data Loading → 02 Embeddings → ...`) becomes a proper flow diagram showing both data paths (CSV seed data and 10-K filing text) converging into Neo4j.

**b. Add `lab6-retriever-comparison.png` in "Four Retrievers Explained" section (after VectorCypherRetriever paragraph)**

Visual side-by-side comparison showing what VectorRetriever returns vs what VectorCypherRetriever returns with graph enrichment.

**c. Add `graphrag-retrieval-flow.png` in "From Documents to Knowledge Graph" section**

Shows the full GraphRAG retrieval flow from user question through search and traversal to answer.

### 4. `lab6.adoc` — One diagram

**Replace ASCII MCP three-component diagram (lines 23-26) with `lab7-mcp-agent-architecture.png`**

The current `AI Agent <--> MCP Server <--> Data Source` text becomes a full diagram showing the ReAct loop, LLM reasoning, tool selection, and MCP tool calls.

Keep the ASCII art for "AWS Deployment Architecture" (lines 74-76) — that's a different linear deployment diagram not covered by an excalidraw file.

## Summary

| Page | Diagram | Action |
|------|---------|--------|
| `index.adoc` | `financial-data-model.png` | Replace ASCII schema |
| `index.adoc` | `workshop-architecture.png` | Replace ASCII architecture |
| `lab4.adoc` | `lab4-mcp-retrieval-architecture.png` | Insert after At a Glance |
| `lab4.adoc` | `lab4-graph-enriched-retrieval.png` | Insert in Graph-Enriched section |
| `lab5.adoc` | `lab6-data-pipeline.png` | Replace ASCII pipeline |
| `lab5.adoc` | `lab6-retriever-comparison.png` | Insert after VectorCypherRetriever |
| `lab5.adoc` | `graphrag-retrieval-flow.png` | Insert in From Docs to KG section |
| `lab6.adoc` | `lab7-mcp-agent-architecture.png` | Replace ASCII MCP diagram |

**8 diagrams → 4 pages. 4 replace ASCII art, 4 are new insertions.**
