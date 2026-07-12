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

# Workshop Architecture and Roadmap

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

![bg contain](dual-database-architecture.svg)

---

![bg contain](workshop-architecture.svg)

---

## Data Pipeline: AWS Lakehouse to Neo4j

The **production pattern** for how SEC 10-K data reaches the graph, via AWS Glue (Spark) and the Neo4j Spark Connector:

- Governed Apache Iceberg tables on Amazon S3, refined through the **medallion pattern** (bronze/silver/gold), cataloged in Glue and secured with Lake Formation
- A Glue (or EMR) Spark job reads the silver/gold tables and writes nodes and relationships via the Neo4j Spark Connector
- Rows become nodes, foreign keys become relationships, shared attributes become shared nodes

This workshop's graph is **pre-loaded** — you work with it directly from Lab 1. The optional Lab 2 rebuilds it from `financial_data.json` with Amazon Titan embeddings instead of running the full lakehouse job.

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

![bg contain](financial-data-model.svg)

---

## Workshop Architecture

<style scoped>
section { font-size: 95%; }
</style>

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

**Part 1: Setup & Exploration** (Labs 0-1)
Sign in to AWS and enable Bedrock access, provision Neo4j Aura, load the seed graph, and explore it with Cypher

**Part 2: GraphRAG Pipelines & Agents** (Labs 2-4)
Optional Lab 2 data pipeline, Lab 3 semantic search and GraphRAG (neo4j-graphrag), Lab 4 GraphRAG agent with AgentCore

**Part 3: Agent Memory** (Lab 5, optional)
Add short and long-term memory to the agent with Neo4j

**Part 4: Neo4j MCP Server** (Lab 6, optional)
Schema-first Text2Cypher agent over the Model Context Protocol

---

## Lab Progression

| Lab | Focus | Key Concept |
|-----|-------|-------------|
| **0** | AWS sign-in, Bedrock access | Foundation model access |
| **1** | Neo4j Aura setup, seed load, exploration | Graph databases, Cypher |
| **2** | Data pipeline (optional) | Chunking, embeddings, indexing |
| **3** | Semantic search + GraphRAG (neo4j-graphrag) | Vector + graph-enriched retrieval |
| **4** | GraphRAG agent + AgentCore | ReAct pattern, tool use, deployment |
| **5** | Agent memory (optional) | Short and long-term memory |
| **6** | Neo4j MCP agent (optional) | Schema-first Text2Cypher over MCP |

---

## What Each Platform Brings

| | AWS | Neo4j |
|---|-----|-------|
| **Provides** | Models, compute, hosting, lakehouse + data pipelines | Graph storage, vector index, query engine |
| **Answers** | "Generate a response", "Deploy this agent", "How much?" and "How often?" | "How is this connected?" and "What is semantically similar?" |
| **AI capability** | Bedrock (Claude, Titan), AgentCore, Athena / Amazon Quick (natural language SQL) | Vector indexes, GraphRAG, MCP Server |
| **Strength** | Scale, managed services, security, governance + data pipelines | Relationships, traversal, pattern matching |

---

## Prerequisites

- **AWS account** with Bedrock access (provided for instructor-led workshops)
- **Neo4j Aura** account (free tier or provided OneBlink SSO)
- **No local setup required**: all work happens in SageMaker Studio notebooks

Let's get started with Lab 0.
