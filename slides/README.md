# Workshop Slides

Presentation-ready slides formatted for [Marp](https://marp.app/).

## Quick Start

Requires Node.js 22 LTS (`brew install node@22`) and a one-time `npm install` in this directory.

```bash
npm install
npm run build   # render all decks + the gallery into build/
npm run serve   # build, then serve the gallery at http://localhost:8080/
```

`npm run build` renders each deck to `build/<deck>/index.html`, copies its images
alongside, and generates `build/index.html`, a gallery linking to every deck.

When published, the slides live at `/slides/`, the workshop site at `/workshop/`,
and the landing page (in `../landing/index.html`) at the site root `/`. The
GitHub Pages workflow (`.github/workflows/deploy-antora.yml`) builds all three
and deploys them as a single site.

## Develop a Single Deck

```bash
npx marp overview-aws-neo4j --server
```

Opens at http://localhost:8080/. Replace `overview-aws-neo4j` with any slide deck
directory name. If Node defaults to v25+, run Marp under Node 22, e.g.
`/opt/homebrew/opt/node@22/bin/node ./node_modules/.bin/marp overview-aws-neo4j --server`.

## Export to PDF

```bash
for dir in overview-*/; do
  npx marp "$dir" --pdf --allow-local-files
done
```

## Troubleshooting

**`require is not defined in ES module scope` error?**
- Marp CLI is incompatible with Node.js 25+. Use Node 22 LTS: `brew install node@22`

**Images not showing?**
- The build script copies each deck's images next to its HTML and uses
  `--allow-local-files`. For ad-hoc Marp commands, pass `--allow-local-files`.

---

## Slide Decks

The eight decks below follow the workshop run of show: the business-story opening, the architecture and roadmap, graph and GraphRAG foundations, retrievers, the GraphRAG agent with AgentCore, agent memory, and the Neo4j MCP agent.

### `overview-business-story/`
The business case for GraphRAG (opening): the stakes, why vector search alone falls short, the shift to GraphRAG, decision governance, the hero questions, what the workshop builds, and the Neo4j + AWS partnership.

### `overview-aws-neo4j/`
Workshop architecture and roadmap: the AWS + Neo4j architecture, the production lakehouse-to-graph pipeline, the SEC 10-K financial data domain, and the four-part lab roadmap.

### `overview-knowledge-graph/`
Knowledge graph foundations: graph databases vs relational, Cypher query language, the SEC financial knowledge graph schema, Neo4j Aura, and visual exploration tools.

### `overview-graphrag/`
GenAI limitations and the GraphRAG solution: hallucination, context rot, embeddings, vector search, RAG, and how graph context transforms retrieval quality.

### `overview-retrievers/`
GraphRAG retriever patterns: VectorRetriever, VectorCypherRetriever, the two halves of one graph, retrieval query design, and choosing the right retriever for your question type.

### `overview-agent-agentcore/`
The GraphRAG agent and AgentCore: the ReAct pattern, the Strands Agents SDK, wrapping GraphRAG retrievers as tools, and deploying the agent to Amazon Bedrock AgentCore.

### `overview-agent-memory/`
Agent memory with Neo4j: why stateless agents fail across turns, the three-part memory model of short-term, long-term, and reasoning traces, the memory graph schema and how it forms a context graph, and one Neo4j instance serving as both knowledge graph and memory store.

### `overview-mcp/`
The Neo4j MCP agent: Model Context Protocol architecture, the Neo4j MCP Server tools, Cypher Templates vs Text2Cypher, the schema-first approach, and MCP as a framework-agnostic production pattern.

---

## Slide Format

All slides use Marp markdown format with pagination, syntax-highlighted code blocks, tables, and two-column layouts. See any slide file for the frontmatter template.

## Additional Resources

- [Marp Documentation](https://marpit.marp.app/)
- [Marp CLI Usage](https://github.com/marp-team/marp-cli)
- [Marp Themes](https://github.com/marp-team/marp-core/tree/main/themes)
- [Creating Custom Themes](https://marpit.marp.app/theme-css)
