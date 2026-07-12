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

# Neo4j MCP Agent

Model Context Protocol, the Neo4j MCP Server, and Text2Cypher

---

## Model Context Protocol (MCP)

**MCP** is an open standard that defines how AI agents discover and interact with external tools:

```
AI Agent (Client)  ←→  MCP Server  ←→  Data Source
```

- **Agent** discovers available tools by asking the MCP server
- **MCP Server** translates between protocol and native API
- **Data Source** (Neo4j, REST API, file system) holds the data

Any MCP-compatible agent connects to any MCP-compatible server.

---

![bg contain](lab6-mcp-agent-architecture.svg)

---

## Neo4j MCP Server Tools

The Neo4j MCP Server exposes two tools (read-only mode):

| Tool | Description |
|------|-------------|
| **`get_neo4j_schema`** | Reads the graph schema via APOC: node labels, relationship types, properties. Token-efficient format for LLM consumption. |
| **`read_neo4j_cypher`** | Executes a read-only Cypher query. Runs `EXPLAIN` first to verify no write operations (CREATE, MERGE, DELETE, SET). |

The agent discovers these tools automatically through the MCP protocol.

---

## AWS Deployment Architecture

```
Agent (Notebook)  →  AgentCore Gateway (HTTPS)  →  Neo4j MCP Server  →  Neo4j Aura
                            ↑
                     Secrets Manager
                     (Neo4j credentials)
```

- **AgentCore Gateway**: AWS-managed HTTPS endpoint, authenticates and routes
- **Neo4j MCP Server**: read-only, Streamable HTTP transport
- **Secrets Manager**: stores Neo4j credentials, retrieved at runtime

All pre-deployed. You connect with a URL and access token from `CONFIG.txt`.

Deployment code: `neo4j-partners/aws-starter` (`neo4j-agentcore-mcp-server/`).

---

## Cypher Templates: Covered Earlier in Lab 3

Pre-written queries wrapped in `@tool` functions:

```python
@tool
def search_company_risks(company_name: str) -> str:
    """Search for risk factors facing a specific company."""
    cypher = """
    MATCH (c:Company {name: $name})-[:FACES_RISK]->(r:RiskFactor)
    RETURN r.name AS risk
    """
    return mcp_client.execute("read_neo4j_cypher", cypher, {"name": company_name})
```

The agent **selects** which template to execute. The queries are expert-reviewed and deterministic. Lab 3 covered this pattern with the neo4j-graphrag library; here the same idea runs over MCP.

---

## Text2Cypher (Lab 6)

The agent writes its own Cypher from scratch after schema discovery:

1. **Retrieve the schema**: call `get_neo4j_schema` to learn labels, types, properties
2. **Write a Cypher query**: based on the actual schema, not assumptions
3. **Execute the query**: call `read_neo4j_cypher` with the generated Cypher

The agent can answer **any question the schema supports**, but query quality depends on LLM reasoning.

---

## Schema-First Approach

**Without schema**: LLM guesses `MATCH (c:Corp)-[:HAS_PRODUCT]->(p)`. Label `Corp` does not exist, `HAS_PRODUCT` is not a relationship type. Query returns zero results silently.

**With schema**: Agent sees actual labels (`Company`, `Product`) and types (`OFFERS`, `FACES_RISK`). Generated Cypher uses the correct vocabulary.

The schema step is critical. Empty results genuinely mean no matching data rather than a query targeting non-existent elements.

---

## Guardrails in the System Prompt

Schema grounding tells the agent *what* to query. The system prompt also constrains *how* it queries, through explicit rules baked into the prompt:

- **Read-only allowlist**: permit only `MATCH`, `RETURN`, `WITH`, `WHERE`, `ORDER BY`, `LIMIT`. No `CREATE`, `MERGE`, `SET`, or `DELETE`.
- **Mandatory `LIMIT`**: cap result size so a broad question cannot flood the context window.
- **Null safety**: use `COALESCE()` or `IS NOT NULL` for properties that may be missing.

Guardrails turn a capable-but-unpredictable generator into a bounded one, before the query ever reaches the database.

---

## Modern Cypher Rules

The prompt also steers the agent toward current Neo4j 5+ syntax, so generated queries do not fail on removed or deprecated constructs:

- **`elementId(n)`** instead of `id(n)`; `id()` is removed in Neo4j 5+
- **`COUNT{ pattern }`** instead of `size((pattern))` for counting
- **`EXISTS{ pattern }`** instead of `exists((pattern))` for existence checks
- **`$parameter`** syntax for dynamic values, never string concatenation

Parameterization is both a correctness and a safety measure: values are bound, not spliced into query text.

This is prompt engineering as a control surface. The `read_neo4j_cypher` tool still runs `EXPLAIN` as a final backstop, but the prompt keeps most bad queries from being written at all.

---

<style scoped>
section { font-size: 25px; }
</style>

## Cypher Templates vs Text2Cypher

| Aspect | Cypher Templates | Text2Cypher |
|--------|-----------------|-------------|
| **Cypher source** | Pre-written in `@tool` functions | Agent writes from scratch |
| **Schema discovery** | No; queries use known labels | Yes; agent calls `get_neo4j_schema` first |
| **Flexibility** | Limited to defined patterns | Any question the schema supports |
| **Failure mode** | Predictable, expert-reviewed | Silent failures possible |
| **MCP role** | Transport for pre-written queries | Discovery (schema) + execution |
| **Best for** | Known patterns, high reliability | Ad-hoc exploration |

---

## The Reliability Spectrum

```
More Reliable                                    More Flexible
←─────────────────────────────────────────────────────────→

Cypher Templates          VectorCypherRetriever          Text2Cypher
(pre-written,             (pre-written traversal,        (agent-generated,
 deterministic)            vector-driven anchor)          schema-driven)
```

Production systems typically use templates for known patterns and Text2Cypher for the long tail.

---

## MCP as a Production Pattern

MCP is the recommended way to connect agents to Neo4j in production:

- **Framework-agnostic**: Strands, LangChain, Claude Desktop, and custom frameworks all speak the same protocol
- **One server, any agent**: deploy the graph integration once, and every framework connects without embedding driver code in each application
- **Schema-aware tools**: agents discover capabilities at runtime rather than hard-coding them
- **Available on AWS Marketplace**: deploy the Neo4j MCP Server once, then connect from any framework

Write the integration once, reuse it everywhere.

---

## Lab 6 Notebook

**Notebook 01: `01_mcp_text2cypher_agent.ipynb`**

MCP tool discovery and schema inspection, then full autonomy: the agent reads the schema and writes its own Cypher, executing it over MCP.

The Cypher Templates pattern (pre-written vector search plus graph traversal) was covered earlier with the neo4j-graphrag library in Lab 3.

---

## Summary

- **MCP**: open standard for agent-to-tool connectivity
- **Cypher Templates**: reliable, pre-written queries, covered earlier in Lab 3 and available over MCP in Lab 6
- **Text2Cypher**: flexible, agent-generated queries after schema discovery, over MCP (Lab 6)
- **Schema-first**: critical for accurate Cypher generation
- **Guardrails**: prompt rules constrain Text2Cypher to read-only, limited, modern-syntax queries
- **Production pattern**: framework-agnostic, one server for any framework, on AWS Marketplace

The agents use the knowledge graph from Labs 1-3 as their intelligence layer.
