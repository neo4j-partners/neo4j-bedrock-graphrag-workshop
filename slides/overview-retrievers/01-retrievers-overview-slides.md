---
marp: true
theme: default
paginate: true
---

<style>
section {
  --marp-auto-scaling-code: false;
}

li {
  opacity: 1 !important;
  animation: none !important;
  visibility: visible !important;
}

/* Disable all fragment animations */
.marp-fragment {
  opacity: 1 !important;
  visibility: visible !important;
}

ul > li,
ol > li {
  opacity: 1 !important;
}
</style>

# GraphRAG Retriever Patterns

From Vector Search to Graph-Enriched Retrieval

---

## The neo4j-graphrag Library

The **neo4j-graphrag** Python package provides the building blocks for GraphRAG applications on Neo4j:

- **Retrievers**: `VectorRetriever` and `VectorCypherRetriever`, plus `HybridRetriever` and `HybridCypherRetriever` that fuse vector and full-text search
- **GraphRAG pipeline**: combines a retriever with an LLM to go from question to grounded answer
- **Knowledge Graph Construction**: `SimpleKGPipeline` for building graphs from text and PDFs
- **LLM and Embedder abstractions**: pluggable providers including Bedrock, OpenAI, Anthropic, Cohere, and Vertex AI
- **Vector index utilities**: `create_vector_index` and `upsert_vectors` for managing Neo4j vector indexes

Lab 3 uses the retriever and pipeline components. The optional Lab 2 uses the construction components.

---

## From Knowledge Graph to Answers

You have a knowledge graph with:
- **Entities**: Companies, products, risk factors, asset managers
- **Relationships**: OFFERS, FACES_RISK, COMPETES_WITH, OWNS
- **Embeddings**: Vector representations for semantic search
- **Chunks**: Text passages from SEC 10-K filings

**The question**: How do you *retrieve* the right information to answer user questions?

---

## The Retrieval Strategies

A **retriever** searches your knowledge graph and returns relevant information.

| Strategy | What It Does |
|----------|--------------|
| **Vector Search** | Semantic similarity across chunks |
| **Full-text Search** | Keyword match, ranked by Lucene/BM25 |
| **Hybrid Search** | Fuse vector + full-text, re-rank |
| **Graph-Enriched Search** | Vector search + graph traversal |
| **Text2Cypher** | LLM writes Cypher from schema |

Top three find the right **text**; bottom two bring in **graph** structure.

---

## The GraphRAG Class

Retrievers work with the **GraphRAG** class, which combines retrieval with LLM generation:

```
User Question
    ↓
Retriever finds relevant context
    ↓
Context passed to LLM
    ↓
LLM generates grounded answer
```

The retriever's job is finding the right context. The LLM's job is generating a coherent answer from that context.

---

## VectorRetriever

**How it works:**
- Converts your question to an embedding (Bedrock Titan)
- Queries the `chunkEmbeddings` vector index
- Returns chunks ranked by cosine similarity

**Best for:**
- "What is Apple's strategy?"
- "Tell me about cybersecurity threats"
- Conceptual, exploratory questions

**Limitation:** Returns text chunks only. No entity relationships.

---

## Full-text Search

**How it works:**
- Keyword match on a `search_chunks` full-text index (Apache Lucene)
- Ranks by Lucene relevance (BM25-style) score
- Supports fuzzy matching and boolean operators

**Best for:**
- Exact names, tickers, acronyms ("NVDA", "10-K")
- Terms that embeddings blur together
- Precise lookups over specific wording

**Limitation:** Matches words, not meaning. Misses paraphrase.

---

## Hybrid Search

**How it works:**
- Runs vector and full-text search over the same chunks
- Normalizes the two score scales, merges into one list
- Re-ranks by a weighted blend (*alpha*) of both signals

**Best for:**
- Questions mixing concepts with exact terms
- Precise names or tickers pure vector search misses

**Re-ranking:** the two score scales differ, so Hybrid normalizes each first. Both rankers normalize the same way; they differ only in how they combine:

| Ranker | What it does | Tunable? |
|--------|--------------|----------|
| **NAIVE** | takes the **max** of the two normalized scores | no knob |
| **LINEAR** | takes a **weighted blend** (*alpha*) of them | yes, via *alpha* |

`HybridRetriever` combines the two text strategies; `HybridCypherRetriever` adds the same fusion on top of graph-enriched search (covered next).

---

## VectorCypherRetriever

**How it works:**
- Vector search finds relevant chunks (same as VectorRetriever)
- Custom Cypher query traverses from chunks to related entities
- Returns content + structured graph context

**Best for:**
- "Which asset managers are affected by crypto regulations?"
- "What risks do tech companies face?"
- Questions needing both content and relationships

**Key insight:** The chunk is the anchor. Graph traversal enriches what vector search finds.

---

<style scoped>
section { font-size: 25px; }
</style>

## The Retrieval Query

The `VectorCypherRetriever` accepts a `retrieval_query` that runs on each matched chunk:

```cypher
MATCH (node)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (doc)<-[:FILED]-(company:Company)
OPTIONAL MATCH (company)-[:FACES_RISK]->(risk:RiskFactor)
OPTIONAL MATCH (product:Product)-[:FROM_CHUNK]->(node)
```

Starting from the matched chunk (`node`), the query traverses:
1. **FROM_DOCUMENT** → which filing?
2. **FILED** ← which company?
3. **FACES_RISK** → what risk factors?
4. **FROM_CHUNK** ← what products mentioned?

---

## What the Library Does Under the Hood

When you call a retriever, it:

1. **Embeds your question**: sends text to Bedrock Titan, gets a 1024-dimensional vector
2. **Queries the vector index**: runs Cypher against the `chunkEmbeddings` index
3. **Traverses the graph** (Cypher retrievers only): executes the `retrieval_query`
4. **Formats results for the LLM**: packages text and metadata into prompt-ready format

In Lab 6, the agent writes its own Cypher and runs it over MCP.

---

## VectorRetriever vs VectorCypherRetriever

| Aspect | VectorRetriever | VectorCypherRetriever |
|--------|----------------|----------------------|
| **Search** | Vector similarity | Vector similarity + graph traversal |
| **Returns** | Chunk text + score | Chunk text + entities + relationships |
| **Context** | Isolated passages | Passages with company, product, risk data |
| **Complexity** | Simple setup | Requires retrieval query design |
| **Best for** | Exploratory questions | Questions needing entity context |

---

## The Chunk-as-Anchor Pattern

Graph traversal starts from what vector search finds:

```
Question → Embedding → Vector Index → Matched Chunks
                                          ↓
                              Graph Traversal from each chunk
                                          ↓
                              Entities, relationships, metadata
```

If vector search does not surface relevant chunks, no amount of graph traversal compensates. The chunk is the anchor.

---

## When Vector Search Is Not Enough

**"How many products does NVIDIA offer?"**

This question targets a **count over relationships**, not a semantically similar passage. Vector search may find chunks that *mention* NVIDIA products, but the accurate answer requires:

```cypher
MATCH (c:Company {name: 'NVIDIA Corporation'})-[:OFFERS]->(p:Product)
RETURN count(p)
```

For counts, lists, and specific lookups, **Text2Cypher** (Lab 6) writes the query directly.

---

## Matching Strategy to Need

Retrieval strategies aren't either/or. They layer to cover what a question needs:

| The question needs… | Add this capability |
|---------------------|---------------------|
| Meaning / concepts | **Vector Search** (the foundation) |
| Exact terms, names, tickers | **+ Full-text** → Hybrid |
| Surrounding entity context | **+ Graph traversal** → Graph-Enriched |
| Precise counts, lists, facts | **Text2Cypher** (structured, exact) |

Most real questions need more than one. Vector search is the base; full-text, graph traversal, and Text2Cypher add precision, context, and structure on top.

---

## Lab 3 Notebook Progression

**Notebook 01: VectorRetriever**
Semantic search plus the `GraphRAG` pipeline

**Notebook 02: VectorCypherRetriever**
Graph-enriched traversal across companies, products, risk factors

**Notebook 03: HybridRetriever**
Full-text search fused with vector, re-ranked (NAIVE / LINEAR)

Chunks and embeddings come from the Lab 1 seed load, so Lab 3 starts from a populated graph.

**Next:** Lab 4 wraps the vector and graph-enriched retrievers as `@tool` functions to build the GraphRAG agent.

---

## Summary

- **Vector Search** is the foundation: semantic similarity across chunks
- **+ Full-text** → **Hybrid**: adds keyword precision (Lucene/BM25), re-ranked
- **+ Graph traversal** → **Graph-Enriched**: adds entity context around each chunk
- **Text2Cypher**: a distinct mode for structured, exact counts, lists, and lookups (Lab 6)
- **The strategies layer**: most real questions need more than one
- **The chunk is the anchor**: graph traversal enriches what search finds

**Next:** Lab 6 adds MCP, Cypher Templates, and Text2Cypher for full agent autonomy.
