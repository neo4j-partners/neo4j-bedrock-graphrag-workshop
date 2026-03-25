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

# GraphRAG Foundations

From GenAI Limitations to Graph-Enriched Retrieval

---

## GenAI Limitations

Foundation models are powerful but have critical gaps:

- **Hallucination** — generate confident, incorrect answers
- **No private data access** — trained on public data, not your SEC filings
- **Knowledge cutoff** — training data has a fixed date
- **No domain context** — cannot traverse your company's relationships

These gaps matter when accuracy and grounding are non-negotiable.

---

## Context Rot

Even with context windows growing to hundreds of thousands of tokens, more context does not mean better answers.

**Context rot**: as the volume of retrieved context grows, model accuracy on questions about that context *decreases*. The signal gets diluted by noise.

The solution is not bigger context windows. It is **better retrieval** — finding precisely the right information and nothing more.

---

## What Is RAG?

**Retrieval-Augmented Generation** gives the LLM relevant context before it answers:

```
User Question
    ↓
Retrieve relevant documents
    ↓
Pass documents + question to LLM
    ↓
LLM generates grounded answer
```

The LLM answers from retrieved evidence rather than memory alone. Retrieval quality determines answer quality.

---

## Embeddings

An **embedding** is a list of numbers that represents the *meaning* of text, not just its words.

- "Supply chain disruption" and "logistics bottleneck risk" produce **similar vectors** because they describe related concepts
- Two texts can share zero keywords but have nearly identical embeddings
- The embedding model reads text and outputs a fixed-length vector (1024 dimensions for Amazon Nova)

Embeddings power **semantic search**: matching on meaning rather than exact keywords.

---

## Vector Search

Given a question, the system:

1. **Embeds the question** into a vector using the same embedding model
2. **Compares** that vector against all stored chunk vectors
3. **Returns** the closest matches ranked by cosine similarity

The result: text passages whose *meaning* is most similar to your question, regardless of the words they use.

---

## Chunking

Documents are too long to embed as single units. **Chunking** splits them into smaller passages:

- Each chunk becomes a **Chunk node** in the graph
- Chunks link to their source **Document** via `FROM_DOCUMENT`
- Adjacent chunks link via `NEXT_CHUNK` to preserve reading order

**Trade-off**: larger chunks give more context but less precision. Smaller chunks are more precise but may miss surrounding context. A moderate size (500-1000 characters) is a reasonable starting point.

---

## The Limitation of Vector Search Alone

Vector search returns **isolated passages**:

- You get chunk text and a similarity score
- No information about *where* the passage came from
- No knowledge of *what entities* it mentions
- No connection to *related information* in the corpus

"Here are text chunks about cybersecurity threats" — but from which company? Affecting which products?

---

## Enter GraphRAG

**GraphRAG** combines vector search with graph traversal:

| Approach | What You Get |
|----------|-------------|
| **Vector search alone** | "Here are text chunks about cybersecurity threats" |
| **GraphRAG** | "Here are text chunks about cybersecurity threats, **filed by Apple**, mentioning **iPhone** and **iCloud**, linked to **Regulatory Compliance** risk factors" |

Graph connections turn an isolated text answer into a **contextual, grounded response**.

---

## The Two-Layer Graph

![bg contain](two-layer-graph.png)

---

## How Graph-Enriched Search Works

1. **Vector search** finds chunks whose meaning matches your question
2. **Graph traversal** follows relationships from each matched chunk:
   - `(Chunk)-[:FROM_DOCUMENT]->(Document)` — which filing?
   - `(Document)<-[:FILED]-(Company)` — which company?
   - `(Company)-[:FACES_RISK]->(RiskFactor)` — what risks?
   - `(Product)-[:FROM_CHUNK]->(Chunk)` — what products mentioned?
3. **LLM** receives chunk text + structured entity context

---

![bg contain](graph-enriched-retrieval.png)

---

## SEC 10-K Example

**Question**: "What cybersecurity risks does Apple face?"

1. **Vector search** finds chunks from Apple's 10-K filing that discuss cybersecurity
2. **Graph traversal** follows connections:
   - FROM_DOCUMENT → Apple's 10-K Document
   - FILED ← Apple (Company)
   - FACES_RISK → Cybersecurity Threats (RiskFactor)
   - FROM_CHUNK → iPhone, iCloud (Products mentioned)
3. **LLM answer** is grounded in the filing text *and* the verified entity structure

---

## Why Graph Context Matters

Without graph context, the LLM must **infer** structure from raw text:
- Which company filed this document?
- Are these risk factors shared across companies?
- Which products are actually affected?

With graph context, these are **verified facts** from the knowledge graph, not LLM guesses. The graph provides the structured backbone; vector search provides the relevant text.

---

## Three Retrieval Strategies

| Strategy | How It Works | Best For |
|----------|-------------|----------|
| **Vector Search** | Embed question, find similar chunks | Conceptual, exploratory questions |
| **Graph-Enriched Search** | Vector search + graph traversal | Questions needing entity context |
| **Text2Cypher** | LLM writes Cypher from schema | Counts, lists, specific lookups |

Each strategy excels at different question types. Labs 4 and 5 implement all three.

---

## Building the Pipeline

The data pipeline that powers GraphRAG:

1. **Split** filing text into chunks
2. **Generate embeddings** for each chunk (Bedrock Nova, 1024 dimensions)
3. **Store** chunks as nodes, linked by NEXT_CHUNK and FROM_DOCUMENT
4. **Create vector index** over chunk embeddings
5. **Cross-link** chunks to entities via FROM_CHUNK relationships

Lab 4 loads pre-built data. Lab 6 builds this pipeline from scratch.

---

![bg contain](data-pipeline-v2.png)

---

## What Comes Next

- **Lab 4**: Load chunks and embeddings, run VectorRetriever and VectorCypherRetriever
- **Lab 5**: Connect agents to Neo4j via MCP, Cypher Templates and Text2Cypher
- **Lab 6**: Build the entire chunking, embedding, and indexing pipeline

The graph provides the knowledge. Retrieval strategies determine how agents access it.
