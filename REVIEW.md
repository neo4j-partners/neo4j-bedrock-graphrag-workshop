# Site Documentation Review

Review of `site/modules/ROOT/pages/` — flow, content accuracy, and internal consistency.

---

## Critical: Lab 3 LangGraph vs Strands Mismatch

The most impactful issue across the site. Lab 3 has been transitioned to Strands (the notebook is `01_basic_strands_agent.ipynb`, the deleted solution file is `03_01_basic_langgraph_agent.py`, replaced by `03_01_basic_strands_agent.py`), but the documentation still describes LangGraph throughout.

Affected files:
- **lab3.adoc** — "At a Glance" lists "LangGraph — builds agents as directed graphs." The entire "LangGraph Agent Architecture" and "Key Code Patterns" sections show `StateGraph`, `MessagesState`, `ChatBedrockConverse`, `ToolNode`, and `bind_tools`. All of this is LangChain/LangGraph code that no longer matches the notebook.
- **lab3-instructions.adoc** — Line 107 says "Open `01_basic_langgraph_agent.ipynb`" — this file has been deleted/renamed.
- **index.adoc** — Line 96 describes Lab 3 as "Amazon Bedrock, SageMaker setup, LangGraph agents, and AgentCore deployment."
- **index.adoc** — Line 29 "Agent Orchestration" section says "LangGraph agents use the ReAct pattern to select retrieval tools."
- **aws-services.adoc** — Line 134 correctly says "Lab 3 deploys a Strands agent to AgentCore" but this contradicts lab3.adoc which is entirely LangGraph-focused.

**Recommendation**: Rewrite lab3.adoc concepts and code examples for Strands (`strands.Agent`, `BedrockModel`, `@tool` decorator). Update index.adoc and lab3-instructions.adoc to match.

---

## Critical: Data Loading Dependency / Lab Ordering

Lab 4 (MCP Retrieval) requires embeddings, Document/Chunk nodes, and fulltext indexes. Lab 4 prerequisites say "Data loaded into Neo4j with embeddings, entity nodes, and fulltext indexes (from the data loading pipeline)." But these are created in Lab 6 notebooks 01 and 02, which come *after* Lab 4 in the workshop flow.

This creates a circular dependency: Lab 4 depends on Lab 6 data, but Lab 6 comes after Lab 4. Either:
1. A separate data loading step runs before Lab 4 (the `financial_data_load/` pipeline?), or
2. Lab 6 notebooks 01-02 should be moved before Lab 4, or
3. The ordering should be documented explicitly with a note telling participants which notebooks to run first.

Currently this is not explained anywhere. A participant following the labs in order will hit Lab 4 with no embeddings, no Chunk nodes, and no fulltext indexes.

---

## Critical: Lab 2 Similarity Search Requires Lab 6 Data

Lab 2 instructions (Step 5) suggest testing Similarity Search with questions like "What do the filings say about AI and machine learning?" The concepts page says "Similarity Search performs semantic retrieval over embedded filing text using the `chunkEmbeddings` vector index."

At Lab 2 in the workshop flow, participants only have the structured data from Lab 1 (Company, Product, RiskFactor, AssetManager). No Document/Chunk nodes, no embeddings, no `chunkEmbeddings` index. The Similarity Search tool will have nothing to search.

**Recommendation**: Either note that Similarity Search requires additional data loading, move the data load earlier, or remove Similarity Search from Lab 2 testing and focus on Cypher Templates and Text2Cypher.

---

## High: Missing Lab 5

The navigation jumps from Lab 4 to Lab 6 with no explanation. Participants will notice the gap and wonder if they missed something. Either renumber Lab 6 to Lab 5, or add a brief note explaining why Lab 5 was removed/skipped.

---

## High: Lab 8 Referenced but Not in Navigation

The Configuration Reference (configuration.adoc) documents three Lab 8 fields (`NEO4J_CLIENT_ID`, `NEO4J_CLIENT_SECRET`, `NEO4J_AGENT_ENDPOINT`) and the `Lab_8_Aura_Agents_API/` directory exists, but Lab 8 has no page in the site and no entry in `nav.adoc`. Lab 1 instructions (line 79) also reference "Labs 3-8" for CONFIG.txt usage.

**Recommendation**: Either add Lab 8 to the navigation or remove Lab 8 references from configuration.adoc and lab1-instructions.adoc.

---

## Medium: Lab 2 Embedding Provider Mismatch

Lab 2 instructions configure Aura Agents with `OpenAI` as the embedding provider and `text-embedding-3-small` as the model. Every other lab in the workshop uses Amazon Bedrock Nova for embeddings. This is likely an Aura Agents platform constraint (it may not support Bedrock embeddings natively), but no note explains the discrepancy. Participants may be confused about why they're suddenly using OpenAI.

**Recommendation**: Add a note explaining why OpenAI is used here and how it differs from the Bedrock Nova embeddings used elsewhere.

---

## Medium: Admin Setup Incomplete for MCP Server Deployment

The admin-setup.adoc page covers AgentCore IAM setup and CONFIG.txt preparation but does not explain how to deploy the Neo4j MCP Server that Labs 4 and 7 depend on. It says "The MCP Gateway URL and access token come from the Neo4j MCP Server deployment on AgentCore" without providing deployment steps.

**Recommendation**: Add MCP Server deployment instructions or link to external documentation.

---

## Medium: aws-services.adoc Next Steps Skip Essential Labs

The "Next Steps" section says: "proceed directly to Lab 3 if your environment is already set up." This skips Labs 1 and 2 — Lab 1 creates the Neo4j database that every subsequent lab depends on. A participant following this suggestion would have no database.

**Recommendation**: Reword to indicate that Lab 1 (Neo4j setup) is required before Lab 3.

---

## Low: Lab 1 "9 Filing Companies" Note

Lab 1 instructions (line 201): "The Company count is higher than 9 because COMPETES_WITH and PARTNERS_WITH relationships reference companies mentioned in filings." The index page says "approximately 76 companies." The note implies there are 9 primary filing companies, but this number isn't established elsewhere. It could confuse participants who see ~76 in the count and wonder where 9 comes from.

**Recommendation**: Clarify or remove the specific number 9, or establish it earlier in the page.

---

## Low: Part 3 Has Only One Lab

"Part 3: Advanced Agents" contains only Lab 7. A single-lab "Part" feels structurally thin. If Lab 8 (Aura Agents API) is planned, adding it here would round out Part 3. Otherwise, Lab 7 could fold into Part 2.

---

## Low: sample-queries.adoc Undirected Relationship

The "Cross-Entity Analysis" query uses `(r:RiskFactor)-[:FACES_RISK]-(c:Company)` with an undirected relationship. The schema everywhere else shows `(Company)-[:FACES_RISK]->(RiskFactor)` with direction. While undirected works in Neo4j, it's inconsistent with the workshop's consistent use of directed patterns and could confuse learners.

---

## Low: Lab 7 LangGraph Option Without Prior LangGraph Exposure

If Lab 3 now uses Strands exclusively, participants encounter LangGraph for the first time in Lab 7. The LangGraph notebook option in Lab 7 assumes familiarity that participants would not have. Either Lab 3 should introduce both frameworks, or the Lab 7 concepts page should note that the LangGraph option is for participants with prior LangGraph experience.

---

## Informational: No Overall Workshop Duration

Individual lab durations total ~195 minutes (3h 15m). No overall estimated duration is provided on the index page. Adding one helps participants and event organizers plan.

---

## Informational: "How the Notebooks Connect" Duplication in Lab 4

Lab 4 (lab4.adoc) has a "How the Notebooks Connect" section (lines 37-38) that essentially restates the "Three Retrieval Strategies" section above it, nearly word for word. This is redundant and could be removed or merged.
