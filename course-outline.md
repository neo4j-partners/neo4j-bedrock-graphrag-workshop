# Proposed AWS Workshop Outline

A condensed proposal for the revamped Neo4j + AWS GraphRAG workshop. Three changes drive the new flow: lead with the why, show the finished build before any setup work, and close with a real call to action.

---

## 1. Workshop Overview and What We're Building

Deliver the why before anything technical. Attendees hear the business story, then watch a live demo of the finished agent, so every setup step afterward is progress toward a destination they have already seen.

* Frame the problem: LLMs hallucinate, and vector search cannot traverse relationships. In financial data that means missing shared executives, cross-portfolio risk exposure, and parent company disclosures
* GraphRAG grounds agents in connected, verifiable facts, anchoring answers in real relationships rather than statistical guesses
* Answers become explainable and auditable, so you can trace why an answer was given, which matters critically in regulated industries like finance
* Graph traversal surfaces the multi-hop connections vector search cannot reach, and that richer context reduces hallucination
* What we're building today: a GraphRAG agent over real SEC 10-K data, deployed to Amazon Bedrock AgentCore
* Neo4j + AWS Strategic Collaboration Agreement and 2026 roadmap
* Live demo: the instructor runs hero questions against the finished agent, pre-deployed before the event. Example: "Which risk factors expose BlackRock's portfolio across multiple companies?"

## 2. Sign In and Set Up Aura

Setup is streamlined to protect momentum. Lab 0 signs in to AWS and enables Bedrock model access; Lab 1 sets up Neo4j Aura and loads the data.

* Lab 0: sign in to AWS and enable Amazon Bedrock access for Claude and Titan Text Embeddings V2
* Lab 1: walk through the Aura free trial sign-up and save connection credentials to CONFIG.txt
* Lab 1: load the seed dataset so the 10-K graph, embeddings, and vector index are ready for the labs
* Goal: everyone signed in, connected, and oriented in under 30 minutes

## 3. Explore the SEC 10-K Knowledge Graph

Attendees get hands-on with the graph immediately, running Cypher against companies, products, risk factors, and executives.

* Introductory Cypher queries in the Neo4j browser
* Graph schema: node types and the relationships connecting them
* Why SEC filings are naturally graph-shaped, with a sample traversal from one company to shared executives and overlapping risks

## 4. Data Pipeline (Optional, Audience-Dependent)

How the unstructured layer gets built: chunks, embeddings, and the vector index. Run it for advanced or full-day audiences; skip it when time is short since later labs work from the seed dataset loaded during setup.

* Load SEC 10-K chunks into Neo4j
* Generate embeddings with Amazon Titan via Bedrock
* Create the vector index and link chunks to graph entities

## 5. Semantic Search and GraphRAG (Core Lab)

The core payoff: attendees see side by side why graph traversal returns richer context than vector search alone.

* VectorRetriever: find relevant chunks by semantic similarity
* VectorCypherRetriever: vector match first, then traverse to connected companies, products, and risk factors
* Same question answered with vector-only context vs. GraphRAG context, and why the richer context reduces hallucination

## 6. GraphRAG Agent and AgentCore Deployment (Core Lab)

Attendees build and deploy the exact agent they saw in the opening demo. A production deployment of a real artifact, not a toy.

* Wire the VectorCypherRetriever into a Strands agent as a tool
* Run multi-hop questions the agent must traverse the graph to answer
* Deploy to AgentCore Runtime and invoke the deployed agent via REST

## 7. Agent Memory (Optional)

Extend the agent with persistent memory using neo4j-agent-memory. One Aura database serves as both knowledge graph and memory store.

* Add short-term memory so the agent resolves references like "their competitors" across turns
* Inspect memory nodes alongside the 10-K graph in Neo4j Browser

## 8. MCP Server (Optional / Advanced)

MCP is the production integration pattern: one server, any agent framework, no driver code per application.

* Schema discovery and simple queries through the pre-deployed Neo4j MCP Server
* Cypher Templates: tool wrappers combining vector search and graph traversal
* Text2Cypher: an autonomous agent writes its own Cypher against the live schema

## 9. Call to Action (The Close)

Close by turning what attendees built into their next step. Talk through other potential use cases tailored to the audience, share customer proof, and make one clear ask so attendees leave ready to book a conversation about their own data.

* Talk through use cases tailored to the companies in the room, prepared by the AE/SE before the event
* Share customer proof: where other companies are seeing value with GraphRAG in production
* Make one clear ask: book a scoping session with an AE or SE, with a QR code on the final slide
* Run a short exit survey with a qualifying question about graph use cases, and route interested attendees to the account team

---

*Removed: the Aura Agents no-code demo — it interrupts flow for engineers, so the workshop goes straight from graph exploration into code. Moved to an appendix: the "What Is an Agent?" basics, available for mixed or non-technical audiences.*
