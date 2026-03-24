# More Cleanup: Standalone Company Nodes

## What We Found

87 total Company nodes. Only 6 are actual SEC 10-K filers with rich data. The rest were extracted by the LLM during PDF processing — mentioned in the filings as competitors, partners, or passing references.

### Tier 1 — Filing Companies (6 nodes, keep)

The core dataset. Each filed a 10-K, has a ticker, and hundreds of entity relationships.

| Company | Ticker | Risks | Products | Execs | Metrics |
|---------|--------|------:|--------:|------:|--------:|
| Amazon.com, Inc. | AMZN | 106 | 20 | 16 | 72 |
| Apple Inc. | AAPL | 109 | 41 | 2 | 64 |
| Microsoft Corporation | MSFT | 141 | 107 | 8 | 222 |
| NVIDIA Corporation | NVDA | 161 | 78 | 5 | 73 |
| PG&E Corporation | PCG | 287 | 16 | 0 | 353 |
| PayPal Holdings, Inc. | PYPL | 161 | 44 | 2 | 132 |

### Tier 2 — Leaked Entities (5 nodes, investigate)

Not filers, but the LLM extracted risk factors, products, or metrics for them during PDF processing. Likely the LLM misattributed entities that belong to a filing company.

| Company | Risks | Products | Metrics | Likely Source |
|---------|------:|--------:|--------:|---------------|
| Advanced Micro Devices, Inc. | 3 | 0 | 1 | NVIDIA's 10-K |
| Alphabet | 1 | 0 | 7 | Mentioned across multiple filings |
| Block, Inc. | 6 | 0 | 0 | PayPal's 10-K |
| Google | 1 | 2 | 1 | Mentioned across multiple filings |
| San Diego Gas & Electric Company | 1 | 0 | 0 | PG&E's 10-K |

Google and Alphabet are also effectively the same entity.

### Tier 3 — Competitors with Provenance (52 nodes, keep)

Mentioned in filing text (have FROM_CHUNK) and are targets of COMPETES_WITH relationships. These serve the competitive landscape queries and have chunk-level provenance.

Examples: Adobe, Intel, Cisco, IBM, Samsung, Tesla, Oracle, Salesforce, Meta, OpenAI, etc.

### Tier 4 — Text Mentions Only (17 nodes, candidates for removal)

Have a FROM_CHUNK relationship (so we know where they were mentioned) but no entity relationships and nobody competes with them. These are passing references in the filing text that the LLM tagged as Company entities.

Access/Google Fiber, AppNexus, Calico, Criteo, Facebook, GV, Google Capital, Kayak, Naver, Omni Logistics LLC, Rivian, Sun Microsystems Inc., Twitter, Verily, WebMD, X, Yandex

### Tier 5 — Phantom Competitors (7 nodes, candidates for removal)

Only exist as inbound COMPETES_WITH targets. They have no FROM_CHUNK provenance — the LLM named them as competitors but they were never linked to a source chunk.

Adyen N.V., Pacific Power, Sempra Energy, Shopify Inc., Southern California Edison, Stripe Inc., Walmart Inc.

## Proposal

### Clean up Tier 2 — Fix misattributed entities

The 5 non-filing companies with entity relationships are likely extraction errors. The LLM read about AMD in NVIDIA's filing and created risk factors attached to AMD instead of NVIDIA. These should be reviewed and either:
- Reassigned to the correct filing company, or
- Removed if the entities are redundant

Google and Alphabet should also be merged (they are the same parent company).

### Clean up Tier 4 — Remove text-mention-only nodes

The 17 companies with only FROM_CHUNK relationships add noise to Company queries without contributing to the graph structure. The chunk text still contains the mention — removing the Company node does not lose information. Delete these nodes and their FROM_CHUNK relationships.

### Clean up Tier 5 — Remove phantom competitors

The 7 companies that only exist as COMPETES_WITH targets have no provenance. They could be added back later from structured data (e.g., industry databases) but right now they are dangling references. Delete these nodes and their inbound COMPETES_WITH edges.

### Leave Tier 3 alone

The 52 competitor companies with FROM_CHUNK provenance are useful. They connect the competitive landscape to specific filing text and support queries like "who competes with NVIDIA and where is that mentioned?"

## Investigation Cypher

Queries used to produce this analysis:

```cypher
// Filing companies
MATCH (c:Company)-[:FILED]->(d:Document)
RETURN c.name, c.ticker

// Non-filing companies with entity relationships
MATCH (c:Company)
WHERE NOT (c)-[:FILED]->()
  AND ((c)-[:FACES_RISK]->() OR (c)-[:OFFERS]->()
       OR (c)-[:REPORTS]->() OR (c)-[:HAS_EXECUTIVE]->())
RETURN c.name

// FROM_CHUNK-only companies (no entity rels)
MATCH (c:Company)
WHERE NOT (c)-[:FILED]->()
  AND NOT (c)-[:FACES_RISK]->() AND NOT (c)-[:OFFERS]->()
  AND NOT (c)-[:REPORTS]->() AND NOT (c)-[:HAS_EXECUTIVE]->()
  AND (c)-[:FROM_CHUNK]->()
OPTIONAL MATCH (c)<-[:COMPETES_WITH]-(rival)
RETURN c.name, collect(DISTINCT rival.name) AS competitors

// Inbound-only companies (no outbound rels at all)
MATCH (c:Company)
WHERE NOT (c)-[]->() AND (c)<-[]-()
RETURN c.name
```
