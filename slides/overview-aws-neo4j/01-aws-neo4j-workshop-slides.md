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

# GraphRAG with Neo4j & AWS

Building Knowledge Graph-Powered AI Agents

---

## What You Will Build

- A **knowledge graph** from SEC 10-K financial filings, loaded from a governed S3 lakehouse (Apache Iceberg) via AWS Glue and the Neo4j Spark Connector
- **GraphRAG retrieval pipelines** that combine vector search with graph traversal
- **AI agents** that query the knowledge graph

By the end, an agent can answer: "Which risk factors expose BlackRock's portfolio across multiple companies?" by traversing ownership chains and risk relationships in the graph.

---

## Why Neo4j + AWS?

Two platforms solve **different problems well**.

**AWS** provides managed foundation models (Bedrock), development environments (SageMaker), serverless agent hosting (AgentCore), and the data foundation: an Amazon S3 + Apache Iceberg lakehouse, governed by AWS Lake Formation and the Glue Data Catalog, with AWS Glue (or Amazon EMR) Spark pipelines that refine and load enterprise data into the graph.

**Neo4j** provides a native graph database that stores entities and relationships as first-class structures, with built-in vector search and graph traversal.

Together: AWS aggregates and governs enterprise data in the lakehouse and provides the reasoning and generation layer, while Neo4j makes relationships traversable for retrieval.

---

![bg contain](workshop-architecture.png)

---

## Data Pipeline: AWS Lakehouse to Neo4j

The SEC 10-K data flows from the **AWS lakehouse** to **Neo4j** through AWS Glue (Spark) and the Neo4j Spark Connector:

- Governed Apache Iceberg tables on Amazon S3, refined through the **medallion pattern** (bronze, silver, gold), cataloged in the Glue Data Catalog and secured with Lake Formation
- An AWS Glue (or Amazon EMR) Spark job runs the Neo4j Spark Connector, reading from the silver/gold tables and writing nodes and relationships into the knowledge graph
- Table rows become nodes, foreign keys become relationships, shared attributes become shared nodes

This workshop's knowledge graph is **pre-loaded**. You work directly with the populated graph from Lab 1 onward.

---

## The SEC Financial Data Domain

Public companies file **10-K annual reports** with the Securities and Exchange Commission. These filings contain:

- Business operations and product descriptions
- Risk factor disclosures
- Financial results and executive information
- Institutional ownership data

The workshop builds a knowledge graph from this data, connecting companies, products, risk factors, and asset managers.

---

## The Knowledge Graph Schema

```
(Company)-[:OFFERS]->(Product)
(Company)-[:FACES_RISK]->(RiskFactor)
(Company)-[:COMPETES_WITH]->(Company)
(Company)-[:PARTNERS_WITH]->(Company)
(AssetManager)-[:OWNS {shares}]->(Company)
```

Four entity types connected by typed relationships that reflect real-world structure. Multi-hop questions follow the connections directly.

---

![bg contain](financial-data-model.png)

---

## Workshop Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Data Pipeline** | AWS Glue / EMR + S3 Iceberg lakehouse (Lake Formation) + Neo4j Spark Connector | Govern, refine, and load enterprise data into the graph |
| **Knowledge Graph** | Neo4j Aura | Store entities, relationships, vector embeddings |
| **Reasoning** | Anthropic Claude (via Bedrock) | Tool selection, response generation |
| **Embeddings** | Amazon Titan Text Embeddings V2 (via Bedrock) | Vector representations for semantic search |
| **Development** | SageMaker Studio | JupyterLab notebooks |
| **Agent Hosting** | AgentCore Runtime | Serverless agent deployment |
| **Tool Protocol** | MCP (Model Context Protocol) | Agent-to-graph connectivity |

---

## Workshop Roadmap

**Part 1: Setup & Visual Exploration** (Labs 0-1)
Sign in to AWS, provision Neo4j Aura, load the knowledge graph, and explore it with Cypher

**Part 2: Building GraphRAG Agents** (Labs 3-5)
Amazon Bedrock and Strands SDK, vector search and graph-enriched retrieval with neo4j-graphrag, MCP agents with Cypher Templates and Text2Cypher

**Part 3: Bonus — Build Your Own Pipeline** (Lab 6)
Build the GraphRAG data pipeline from scratch: data loading, embeddings, and vector-cypher retrieval

---

## Lab Progression

| Lab | Focus | Key Concept |
|-----|-------|-------------|
| **0** | AWS sign-in, Bedrock access | Foundation model access |
| **1** | Neo4j Aura setup, data loading | Graph databases, Cypher |
| **3** | Strands SDK, Bedrock agents | ReAct pattern, tool use |
| **4** | neo4j-graphrag retrievers | Vector + graph-enriched search |
| **5** | MCP server, Text2Cypher | Schema-first agent queries |
| **6** | Full data pipeline (bonus) | Chunking, embeddings, indexing |

---

## From Code-First to Full Autonomy

The labs progress along a **control spectrum**:

```
Lab 3: Strands SDK         → Code-first agents, @tool decorator
Lab 4: neo4j-graphrag      → Pre-built retriever classes
Lab 5: Cypher Templates    → Pre-written queries, MCP transport
Lab 5: Text2Cypher         → Agent writes its own Cypher
```

Each step gives the agent more autonomy. The trade-off: more flexibility means less predictability.

---

## What Each Platform Brings

| | AWS | Neo4j |
|---|-----|-------|
| **Provides** | Models, compute, hosting, lakehouse + data pipelines | Graph storage, vector index, query engine |
| **Answers** | "Generate a response", "Deploy this agent", "How much?" and "How often?" | "How is this connected?" and "What is semantically similar?" |
| **AI capability** | Bedrock (Claude, Titan), AgentCore, Athena / Amazon Q (natural language SQL) | Vector indexes, GraphRAG, MCP Server |
| **Strength** | Scale, managed services, security, governance + data pipelines | Relationships, traversal, pattern matching |

---

## Prerequisites

- **AWS account** with Bedrock access (provided for instructor-led workshops)
- **Neo4j Aura** account (free tier or provided OneBlink SSO)
- **No local setup required** — all work happens in SageMaker Studio notebooks

Let's get started with Lab 0.
