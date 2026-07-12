import { execFileSync } from "node:child_process";
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { basename, join } from "node:path";

// Shared image library; decks reference some assets that live here rather than
// in the deck folder (e.g. two-layer-graph.png used by overview-graphrag).
const SHARED_IMAGES_DIR = "images";

const decks = [
  {
    key: "business-story",
    dir: "overview-business-story",
    source: "01-business-story-slides.md",
    title: "The Business Case for GraphRAG",
    description:
      "The stakes, why vectors alone fall short, decision governance, the hero questions, and the Neo4j + AWS partnership.",
  },
  {
    key: "aws-neo4j",
    dir: "overview-aws-neo4j",
    source: "01-aws-neo4j-workshop-slides.md",
    title: "Workshop Architecture & Roadmap",
    description:
      "The AWS + Neo4j architecture, the production lakehouse-to-graph pipeline, the SEC 10-K data domain, and the four-part lab roadmap.",
  },
  {
    key: "knowledge-graph",
    dir: "overview-knowledge-graph",
    source: "01-knowledge-graph-foundations-slides.md",
    title: "Knowledge Graph Foundations",
    description:
      "Graph databases vs relational, Cypher, the SEC financial knowledge graph schema, Neo4j Aura, and visual exploration.",
  },
  {
    key: "graphrag",
    dir: "overview-graphrag",
    source: "01-graphrag-foundations-slides.md",
    title: "GraphRAG Foundations",
    description:
      "GenAI limitations and the GraphRAG solution: hallucination, embeddings, vector search, RAG, and graph context.",
  },
  {
    key: "retrievers",
    dir: "overview-retrievers",
    source: "01-retrievers-overview-slides.md",
    title: "Retrievers Overview",
    description:
      "VectorRetriever, VectorCypherRetriever, the two-layer graph, and choosing the right retriever for a question.",
  },
  {
    key: "agent-agentcore",
    dir: "overview-agent-agentcore",
    source: "01-agent-agentcore-slides.md",
    title: "GraphRAG Agent & AgentCore",
    description:
      "The ReAct pattern, the Strands Agents SDK, wrapping GraphRAG retrievers as tools, and deploying the agent to Amazon Bedrock AgentCore.",
  },
  {
    key: "agent-memory",
    dir: "overview-agent-memory",
    source: "01-agent-memory-slides.md",
    title: "Agent Memory with Neo4j",
    description:
      "Why stateless agents fail across turns, neo4j-agent-memory for short and long-term memory, and one Neo4j instance as both knowledge graph and memory store.",
  },
  {
    key: "mcp",
    dir: "overview-mcp",
    source: "01-mcp-slides.md",
    title: "Neo4j MCP Agent",
    description:
      "The Model Context Protocol, the Neo4j MCP Server tools, Cypher Templates vs Text2Cypher, and MCP as a framework-agnostic production pattern.",
  },
];

rmSync("build", { force: true, recursive: true });
mkdirSync("build", { recursive: true });

for (const deck of decks) {
  const outDir = join("build", deck.key);
  mkdirSync(outDir, { recursive: true });

  execFileSync(
    "marp",
    [
      join(deck.dir, deck.source),
      "-o",
      join(outDir, "index.html"),
      "--allow-local-files",
    ],
    { stdio: "inherit" },
  );

  // Marp keeps background images as bare relative file references
  // (e.g. background-image:url("foo.png")), so copy every image the deck
  // references next to its generated HTML, resolving from the deck folder
  // first and the shared image library second.
  for (const name of referencedImages(join(deck.dir, deck.source))) {
    const fromDeck = join(deck.dir, name);
    const fromShared = join(SHARED_IMAGES_DIR, name);
    const src = existsSync(fromDeck)
      ? fromDeck
      : existsSync(fromShared)
        ? fromShared
        : null;

    if (!src) {
      throw new Error(
        `${deck.dir}/${deck.source} references missing image "${name}" ` +
          `(looked in ${deck.dir}/ and ${SHARED_IMAGES_DIR}/)`,
      );
    }

    copyFileSync(src, join(outDir, name));
  }
}

writeFileSync(join("build", ".nojekyll"), "");
writeFileSync(join("build", "index.html"), renderIndex());

// Extract local image filenames referenced from a Marp markdown file, covering
// both inline images and background directives — all written as ![...](file).
function referencedImages(markdownPath) {
  const markdown = readFileSync(markdownPath, "utf8");
  const names = new Set();

  for (const match of markdown.matchAll(/!\[[^\]]*\]\(([^)]+)\)/g)) {
    const target = match[1].trim();
    if (/^[a-z]+:\/\//i.test(target)) {
      continue; // skip remote URLs
    }
    if (/\.(png|jpe?g|gif|webp|svg)$/i.test(target)) {
      names.add(basename(target));
    }
  }

  return names;
}

function renderIndex() {
  const cards = decks
    .map(
      (deck) => `        <a class="deck-card" href="./${deck.key}/">
          <strong>${escapeHtml(deck.title)}</strong>
          <span>${escapeHtml(deck.description)}</span>
        </a>`,
    )
    .join("\n");

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GraphRAG Workshop Slides</title>
    <style>
      :root {
        color-scheme: light;
        --ink: #172033;
        --muted: #5b6678;
        --line: #d9e0ea;
        --accent: #0f766e;
        --accent-2: #2563eb;
        --surface: #ffffff;
        --bg: #f8fafc;
      }

      * {
        box-sizing: border-box;
      }

      body {
        background:
          linear-gradient(90deg, var(--accent) 0 10px, transparent 10px),
          var(--bg);
        color: var(--ink);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 0;
      }

      main {
        margin: 0 auto;
        max-width: 1080px;
        padding: 72px 24px 64px 42px;
      }

      h1 {
        font-size: clamp(36px, 6vw, 64px);
        line-height: 1;
        margin: 0 0 16px;
      }

      p {
        color: var(--muted);
        font-size: 19px;
        line-height: 1.5;
        margin: 0;
        max-width: 760px;
      }

      .eyebrow {
        color: var(--accent);
        font-size: 14px;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-bottom: 14px;
        text-transform: uppercase;
      }

      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin: 32px 0 8px;
      }

      .button {
        align-items: center;
        background: var(--accent);
        border-radius: 6px;
        color: white;
        display: inline-flex;
        font-weight: 700;
        min-height: 44px;
        padding: 0 16px;
        text-decoration: none;
      }

      .button.secondary {
        background: var(--ink);
      }

      .decks {
        display: grid;
        gap: 16px;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        margin: 36px 0 0;
      }

      .deck-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 8px;
        color: inherit;
        display: block;
        padding: 18px;
        text-decoration: none;
        transition: border-color 0.15s ease, transform 0.15s ease;
      }

      .deck-card:hover {
        border-color: var(--accent);
        transform: translateY(-2px);
      }

      .deck-card strong {
        color: var(--ink);
        display: block;
        font-size: 17px;
        margin-bottom: 8px;
      }

      .deck-card span {
        color: var(--muted);
        display: block;
        font-size: 15px;
        line-height: 1.45;
      }
    </style>
  </head>
  <body>
    <main>
      <div class="eyebrow">Neo4j + AWS Bedrock</div>
      <h1>GraphRAG Workshop Slides</h1>
      <p>Presentation decks for the GraphRAG workshop. Each deck covers one stage of the workshop, from the AWS and Neo4j overview through knowledge graphs, GraphRAG, retrievers, and agents.</p>
      <div class="actions">
        <a class="button" href="../workshop/">Open the workshop</a>
        <a class="button secondary" href="../">Back to home</a>
      </div>
      <section class="decks" aria-label="Slide decks">
${cards}
      </section>
    </main>
  </body>
</html>
`;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
