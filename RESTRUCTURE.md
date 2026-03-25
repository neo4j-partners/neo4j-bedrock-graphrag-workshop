Goal - restructure labs so participants use a direct neo4j python connection in Lab 4

Drops the labs Lab_4_Graph_Enriched_Search/01_vector_search_mcp.ipynb and Lab_6_Advanced_Agents/neo4j_langgraph_mcp_agent.ipynb

New Lab Order

* Lab 4 GraphRag starting with search
** Lab 01 - Load data from setup/seed-embeddings, run basic test queries 
** Lab 02 - Vector Retriever using the neo4j graphrag library based on Lab_5_GraphRAG/03_vector_retriever.ipynb
** Lab 03 - Vector Cypher Retriever using Lab_5_GraphRAG/04_vector_cypher_retriever.ipynb

* Lab 5 Neo4j MCP Server Intro  - based on current Lab 4
** Lab 01 copied from Lab_4_Graph_Enriched_Search/00_intro_strands_mcp.ipynb
** Lab 02 - Lab_4_Graph_Enriched_Search/02_graph_enriched_search_mcp.ipynb
** Lab 03 - Advanced Strands example using Lab_6_Advanced_Agents/neo4j_strands_mcp_agent.ipynb


* Lab 6 Building a GraphRag Data pipeline
* built using 01_data_loading.ipynb
02_embeddings.ipynb
04_vector_cypher_retriever.ipynb
05_hybrid_rag.ipynb
financial_data.json