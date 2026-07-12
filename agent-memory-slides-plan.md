# Plan: Agent Memory Slide Deck for Lab 5

## Context

Lab 5 teaches agent memory with Neo4j on top of the Lab 4 GraphRAG agent. The existing
deck (`slides/overview-agent-memory/01-agent-memory-slides.md`) only covers **two** memory
layers (short-term, long-term) and has no diagram. The Neo4j blog corpus has since converged
on a **three-part context-graph memory model** (short-term / long-term / **reasoning**), which
is exactly what `images/neo4j-agent-memory-diagram.png` depicts.

Goal: rewrite the deck so the three-part model in that PNG is the primary framework, add the
missing **reasoning memory / reasoning-trace** coverage, distill best practices from the blogs,
explain how agent memory and context graphs relate, and briefly place it in the wider agentic-AI
strategy. Keep it short and condensed: `bold term: definition` bullets, each carrying a source
tag, with a footnote line per slide and a full Sources slide. Focus on agent memory **concepts**,
not the Neo4j Agent Memory Service (NAMS) product.

## Conventions to follow

- **Format:** Marp markdown, same frontmatter + `<style>` block as the existing decks. Build via
  `slides/scripts/build-slides.mjs` (`npm run build` in `slides/`, Node 22 LTS).
- **Slide craft:** `technical-slides-guide` skill. 6x6 ceiling, fragments not sentences,
  `bold term: definition` bullets, narrative in `<!-- speaker notes -->`, no emojis/em-dashes,
  no marketing vocabulary.
- **Diagram asset:** copy `images/neo4j-agent-memory-diagram.png` into
  `slides/overview-agent-memory/` (decks reference images relative to their own dir; the build
  copies them next to the HTML with `--allow-local-files`). Optionally later re-author as an SVG
  in the `slides/images/` house style, but the PNG ships first.

## Citation scheme (source tags + footnotes)

Each concept bullet ends with a bracketed tag. Every slide that uses tags gets a small footnote
line; a final **Sources** slide lists full citations. Add a scoped `<style>` rule for a small
`footnote` class (e.g. `section .footnote { font-size: 0.5em; color: #666; }`).

- `[1]` Context graphs: why AI agents need three types of memory (Webber) — neo4j.com/blog/agentic-ai/context-graph-ai-agent-memory/
- `[2]` Agentic AI vs. generative AI (Krüger) — neo4j.com/blog/agentic-ai/agentic-ai-vs-generative-ai/
- `[3]` Modeling agent memory (Gilmore) — neo4j.com/blog/developer/modeling-agent-memory/
- `[4]` Hands on with context graphs and Neo4j (Lyon) — neo4j.com/blog/agentic-ai/hands-on-with-context-graphs-and-neo4j/
- `[5]` When your agents share a brain: multi-agent memory (Lyon) — medium.com/neo4j/...bac609f17b23
- `[6]` Agent Memory (Neo4j Labs) — neo4j.com/labs/agent-memory/
- `[7]` A tour of the Neo4j Agent Memory Service (Lyon, concepts only) — medium.com/neo4j/...0f2d535a4fdb

## Proposed slide outline

Rewrite `slides/overview-agent-memory/01-agent-memory-slides.md` to ~12 slides:

1. **Title** — "Agent Memory with Neo4j" / "Three Kinds of Memory in One Graph".
2. **Main Points** (the short summary to discuss) — 4-5 fragments: agents are amnesiacs; three
   connected memory layers in one graph; context graph captures the "why"; reasoning traces =
   auditability; one Neo4j graph beside the knowledge graph. Tags `[1][5][7]`.
3. **Why Stateless Agents Fail** — keep the Apple → "their competitors" example; frame as the
   amnesiac problem (context window resets, vector recall != understanding). Tags `[5][7]`.
4. **Agent Memory and Context Graphs** — definitions + how they relate:
   - **Agent memory:** durable, queryable store of what an agent knows and has done `[1]`
   - **Context graph:** knowledge graph capturing decision traces, grounded in real entities `[1][4]`
   - **Relationship:** the context graph *is* the memory, unified across three layers ("Sim City model") `[1]`
5. **The Three-Part Memory Model** — PRIMARY FRAMEWORK slide. `![bg right/contain]` the PNG,
   with three `bold term: definition` bullets (short-term / long-term / reasoning). Tags `[1][7]`.
   This is the spine the rest of the deck expands.
6. **Short-Term Memory** — conversation/session scope; `Conversation`/`Message` + `NEXT_MESSAGE`
   chains; recalled by `get_context(session_id=...)`; bridges knowledge and action. Tags `[1][3][5]`.
7. **Long-Term Memory** — durable entities/facts/preferences across sessions; POLE+O entity
   model (Person/Org/Location/Event/Object); `WORKS_AT`-style typed relationships; entity
   dedup. Note semantic/episodic/procedural framing in one sub-bullet. Tags `[1][3][5][7]`.
8. **Reasoning Memory / Reasoning Traces** — the new layer:
   - **Reasoning memory:** decision traces + tool calls as first-class graph nodes `[1][5]`
   - **Schema:** `Message -[:TRIGGERED]-> ReasoningTrace -[:HAS_STEP]-> ReasoningStep -[:USED_TOOL]-> ToolCall -[:CALL_OF]-> Tool`, with `RETRIEVED` links back to entities (matches the diagram) `[5]`
   - **Why:** explainability + audit ("why did the agent decide this?") `[5]`
9. **How the Layers Connect** — ASCII/short recap that all three live in one graph and traverse
   across each other (message → entity → reasoning trace); deterministic traversal vs probabilistic
   similarity; provenance chain. Tags `[1][5]`.
10. **Best Practices** — condensed: design memory explicitly (separate working vs durable);
    capture the "why" not just the "what"; reasoning traces as first-class nodes; dedup entities;
    curate/compress (messages → observations → reflection); prefer graph traversal for provenance.
    Tags `[2][3][5][7]`.
11. **Where Memory Fits the Agent Strategy** (brief) — agentic vs generative in one table row or
    two bullets: GenAI = stateless content; agentic = stateful goal loop with memory + tools +
    guardrails; evolution path LLM → RAG → GraphRAG → tool agents → agentic systems. Tags `[2]`.
12. **Sources** — full citations `[1]`-`[7]` with URLs.

Optionally fold the Lab-5 code specifics (the `ask()` wrapper, `adopt_existing_graph`, demo arc)
into speaker notes or keep 1-2 of the original code slides after slide 8, so the deck still maps
to what the notebooks do. Decide during implementation to respect the 6x6 ceiling.

## Scope decisions

- **Focus on concepts, not NAMS.** Use `[7]` only for product-agnostic ideas (three-layer model,
  POLE+O, compression pyramid). Do not describe the managed service, console, API keys, or SDKs.
- **Keep the diagram authoritative.** Where a blog's terminology differs (e.g. `[:NEXT]` vs
  `NEXT_MESSAGE`, `MENTIONS` vs `MENTIONED_IN`), match the labels in the PNG so slide and image agree.

## Files

- Rewrite: `slides/overview-agent-memory/01-agent-memory-slides.md`
- Add: `slides/overview-agent-memory/neo4j-agent-memory-diagram.png` (copy of `images/neo4j-agent-memory-diagram.png`)
- No changes to notebooks or `lib/`.

## Verification

1. Run `npm run build` in `slides/` (Node 22 LTS) and confirm the deck renders to
   `slides/build/overview-agent-memory/index.html` with no Marp errors and the gallery updates.
2. Open the built HTML: confirm the diagram renders on the three-part model slide, footnotes are
   legible, and no slide overflows (6x6 check).
3. Read through for tone/prohibitions (no emojis, em-dashes, marketing words) against the
   `technical-slides-guide` checklist.
