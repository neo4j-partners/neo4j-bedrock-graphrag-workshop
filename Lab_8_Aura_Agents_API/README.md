# Lab 8 - Aura Agents API

In this lab, you'll call the Neo4j Aura Agent you built in Lab 2 programmatically using Python. The same agent that answers questions about SEC 10-K filings through the Aura console becomes accessible via REST API, enabling integration into applications, data pipelines, and automated workflows.

## Prerequisites

Before starting, make sure you have:
- Completed **Lab 0** (AWS sign-in)
- Completed **Lab 1** (Neo4j Aura setup)
- Completed **Lab 2** (Built an Aura Agent with tools)
- Completed **Lab 3** (SageMaker setup)

## Lab Overview

In Lab 2, you built a GraphRAG agent using Neo4j's visual agent builder. That agent can:
- Answer questions about SEC 10-K filings, risk factors, and company data
- Use Cypher template tools to query company overviews and shared risk factors
- Perform semantic similarity searches across filing content
- Generate Cypher queries from natural language

Now you'll call that same agent via a REST API, enabling:
- **Application Integration**: Embed the agent in web apps, mobile apps, or microservices
- **Automation**: Include agent calls in data pipelines and workflows
- **Batch Processing**: Ask multiple questions programmatically
- **Custom UIs**: Build your own chat interfaces

## What You'll Learn

1. **OAuth2 Authentication**: How to authenticate with the Neo4j API using client credentials
2. **REST API Invocation**: How to call your Aura Agent's endpoint
3. **Pydantic Response Models**: How to parse responses into type-safe Python objects
4. **Token Management**: How to cache and refresh access tokens automatically
5. **Async Batch Queries**: How to make concurrent requests for better performance

## Getting Your API Credentials

### Step 1: Get Your API Key

1. Log in to [Neo4j Aura Console](https://console.neo4j.io/)
2. Click your **profile icon** in the top right corner
3. Go to **Settings**
4. Select the **API keys** tab
5. Click **Create API Key**
6. Copy and save both the **Client ID** and **Client Secret**

> **Important**: The Client Secret is only shown once. Save it securely!

### Step 2: Get Your Agent Endpoint

1. In the Aura Console, navigate to your agent
2. Click on your agent to open its details
3. Click the **Copy endpoint** button
4. The URL will look like: `https://api.neo4j.io/v2beta1/organizations/.../projects/.../agents/.../invoke`

### Step 3: Enable External Access (if not already done)

Your agent must have **External** visibility to be called via API:
1. Open your agent's settings
2. Ensure **External endpoint** is enabled

## Authentication Flow

The client handles authentication automatically:

```
1. Request Token
   POST https://api.neo4j.io/oauth/token
   - Basic Auth: client_id:client_secret
   - Body: grant_type=client_credentials
   → Response: { access_token, expires_in: 3600 }

2. Invoke Agent
   POST {agent_endpoint}/invoke
   - Authorization: Bearer {access_token}
   - Body: { input: "your question" }
   → Response: { content, status, usage }
```

Tokens are cached for 1 hour and automatically refreshed when expired.

## Lab Notebook

This lab contains one comprehensive notebook:

### aura_agent_client.ipynb - Python Client for Aura Agents

Build and use a complete Python client to call your Aura Agent:
- Understand OAuth2 client credentials flow
- Create type-safe response models with Pydantic
- Build a reusable client class
- Test with sample questions about SEC financial data
- Explore agent thinking and tool usage
- Make concurrent async requests

## Getting Started

1. Open the notebook: `aura_agent_client.ipynb`
2. Ensure your credentials are set in `CONFIG.txt`:
   - `NEO4J_CLIENT_ID` - Your API key Client ID
   - `NEO4J_CLIENT_SECRET` - Your API key Client Secret
   - `NEO4J_AGENT_ENDPOINT` - Your agent's endpoint URL
3. Run through the notebook cells

## Example Usage

After completing the notebook, you can call your agent like this:

```python
# Create client
client = AuraAgentClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
    endpoint_url="https://api.neo4j.io/.../invoke"
)

# Ask a question
response = client.invoke("What risk factors does Apple face according to their 10-K filing?")
print(response.text)

# View agent reasoning
print(response.thinking)

# Check tool usage
for tool in response.tool_uses:
    print(f"Used tool: {tool.type}")
```

## Sample Questions

Try these questions with your agent (same as Lab 2):

**Company Analysis:**
- "What companies are in the database and what products do they offer?"
- "Tell me about Apple's SEC filing and their major investors"

**Risk Analysis:**
- "What risk factors does Apple face according to their 10-K filing?"
- "What risks do Apple and Microsoft share?"

**Semantic Search:**
- "What do the filings say about supply chain risks and mitigation strategies?"
- "What do companies say about AI and machine learning?"

**Structured Queries:**
- "Which company has the most risk factors?"
- "What asset managers own stakes in technology companies?"

## Key Concepts

| Concept | Description |
|---------|-------------|
| **OAuth2 Client Credentials** | Authentication flow for machine-to-machine API access |
| **Bearer Token** | Access token included in API request headers |
| **Token Caching** | Reusing tokens until they expire (1 hour) |
| **Pydantic Models** | Type-safe data validation for API responses |
| **Async/Await** | Python pattern for concurrent, non-blocking operations |

## Next Steps

**Congratulations!** You have completed all labs in the workshop.

You now have hands-on experience with:
- Building no-code AI agents with Neo4j Aura Agents
- Building GraphRAG pipelines with the neo4j-graphrag library
- Connecting LLM agents to Neo4j via the Model Context Protocol
- Calling Aura Agents programmatically via REST API

## Resources

- [Neo4j Aura Agents Documentation](https://neo4j.com/developer/genai-ecosystem/aura-agent/)
- [Neo4j API Authentication](https://neo4j.com/docs/aura/platform/api/authentication/)
- [Build a GraphRAG Agent in Minutes](https://neo4j.com/blog/genai/build-context-aware-graphrag-agent/)
