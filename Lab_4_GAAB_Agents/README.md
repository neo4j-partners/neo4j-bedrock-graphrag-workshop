# Lab 4 - AI Agent Builder (GAAB)

In this lab, you will create an AI agent that can query your Neo4j knowledge graph using the AWS Generative AI Application Builder (GAAB). The Neo4j MCP server has been pre-deployed for this workshop - you'll simply connect your agent to it.

## Prerequisites

Before starting, make sure you have:
- Completed **Lab 0** (AWS sign-in)
- Completed **Lab 1** (Neo4j Aura setup with backup restored)
- Completed **Lab 2** (Aura Agents - to understand the agent patterns)
- Completed **Lab 3** (Bedrock Setup - model access enabled)

## What is Generative AI Application Builder (GAAB)?

GAAB is an AWS Solution that provides:

- **Management Dashboard** - Web UI to create and manage AI agents
- **Agent Builder** - Configure agents with models, tools, and memory
- **MCP Integration** - Connect agents to Model Context Protocol servers
- **Enterprise Features** - Authentication, monitoring, and security built-in

In this lab, you'll:
- Access the pre-deployed GAAB dashboard
- Create an AI agent for SEC filings analysis
- Connect to the pre-deployed Neo4j MCP server
- Test the agent with natural language queries

> **Workshop Note:** The GAAB platform and Neo4j MCP server have been pre-deployed by workshop organizers. In a production environment, you would deploy these using CloudFormation or CDK.

---

## Part 1: Access the GAAB Dashboard

### Step 1: Get Your Dashboard Credentials

Your workshop instructor will provide:

| Information | Value |
|-------------|-------|
| **Dashboard URL** | `https://xxxxxxxxxx.cloudfront.net` |
| **Username** | Your workshop email |
| **Temporary Password** | Provided by instructor |

> **Note:** If you're running this workshop independently, see [Appendix A](#appendix-a-deploying-gaab) for deployment instructions.

### Step 2: Sign In to the Dashboard

1. Open the Dashboard URL in your browser
2. Enter your username (email) and temporary password
3. You'll be prompted to set a new password on first login
4. Complete any MFA setup if required

![GAAB Login](images/gaab_login.png)

### Step 3: Explore the Dashboard

After signing in, you'll see the Management Dashboard with options for:

- **Agents** - Create and manage AI agents
- **MCP Servers** - View connected MCP servers
- **Deployments** - Monitor active deployments

![GAAB Dashboard](images/gaab_dashboard.png)

---

## Part 2: Create an AI Agent

### Step 4: Navigate to Agent Builder

1. Click **Agents** in the left navigation
2. Click **Create Agent**

![Create Agent Button](images/create_agent_button.png)

### Step 5: Configure Agent Details

Fill in the basic agent information:

**Agent Name:** `sec-filings-analyst`

**Description:**
```
An AI-powered financial analyst that helps users explore SEC 10-K filings,
analyze company risk factors, and discover relationships in the knowledge graph.
```

![Agent Details](images/agent_details.png)

### Step 6: Configure System Prompt

In the **System Prompt** section, enter:

```
You are an expert financial analyst assistant specializing in SEC 10-K filings analysis.

You help users understand:
- Company risk factors and how they compare across companies
- Asset manager ownership patterns and portfolio compositions
- Financial metrics and products mentioned in company filings
- Relationships between companies, their documents, and extracted entities

When answering questions:
1. Always use the available tools to query the knowledge graph
2. Use exact company names like "APPLE INC" or "NVIDIA CORPORATION" for best results
3. Provide specific examples from the actual data
4. Ground your responses in facts from SEC filings
5. If you're unsure, say so rather than making up information

The knowledge graph contains SEC 10-K filings from major companies including Apple, Microsoft, NVIDIA, and others.
```

![System Prompt](images/system_prompt.png)

### Step 7: Select Model

1. In the **Model** section, click **Configure**
2. Select **Amazon Bedrock** as the provider
3. Choose **Claude 3.5 Sonnet v2** (or Claude 3 Haiku for lower cost)
4. Set recommended parameters:
   - Temperature: `0.3`
   - Max Tokens: `2048`

![Select Model](images/select_model.png)

---

## Part 3: Connect to Neo4j MCP Server

The Neo4j MCP server has been pre-deployed for this workshop. You'll now connect your agent to it.

### Step 8: Add MCP Server Connection

1. In the **Tools** section, click **Add MCP Server**
2. Select **Connect to existing MCP Server**

![Add MCP Server](images/add_mcp_server.png)

### Step 9: Configure MCP Server Details

Your instructor will provide the MCP server endpoint. Enter:

| Field | Value |
|-------|-------|
| **Server Name** | `neo4j-knowledge-graph` |
| **Endpoint URL** | `https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/mcp` |
| **Authentication** | Select **OAuth2** (pre-configured) |

![MCP Server Config](images/mcp_server_config.png)

Click **Connect** to establish the connection.

### Step 10: Verify Tool Discovery

After connecting, GAAB will automatically discover the available tools from the MCP server:

| Tool | Description |
|------|-------------|
| `get_neo4j_schema` | Returns the graph schema (node labels, relationships, properties) |
| `read_neo4j_cypher` | Executes read-only Cypher queries against the knowledge graph |

![Tools Discovered](images/tools_discovered.png)

Ensure both tools show a green checkmark indicating they're available.

### Step 11: Deploy the Agent

1. Review your agent configuration
2. Click **Deploy Agent**
3. Wait for the deployment to complete (typically 1-2 minutes)

![Deploy Agent](images/deploy_agent.png)

---

## Part 4: Test the Agent

Now test your agent with natural language queries about SEC filings.

### Step 12: Open the Test Console

1. After deployment completes, click **Test Agent**
2. The test console will open in a chat interface

![Test Console](images/test_console.png)

### Step 13: Test Schema Query

Enter this query to verify the MCP connection:

```
What is the schema of the knowledge graph? What types of nodes and relationships exist?
```

**Expected behavior:**
1. Agent recognizes this needs the schema tool
2. Calls `get_neo4j_schema` via MCP
3. Returns information about node labels (Company, Document, RiskFactor, etc.)

![Schema Query](images/schema_query.png)

### Step 14: Test Company Query

Try a query about a specific company:

```
What can you tell me about Apple's SEC filing? What are their main risk factors?
```

**Expected behavior:**
1. Agent formulates a Cypher query
2. Calls `read_neo4j_cypher` with the query
3. Returns company information and risk factors

![Company Query](images/company_query.png)

> **Tip:** Use exact company names like "APPLE INC" or "NVIDIA CORPORATION" for best results.

### Step 15: Test Comparison Query

Try a more complex comparative query:

```
Which company has the most risk factors? List the top 3 companies by number of risks.
```

**Expected behavior:**
1. Agent generates appropriate Cypher aggregation query
2. Executes query against the graph
3. Returns ranked list of companies

![Comparison Query](images/comparison_query.png)

### Step 16: Test Relationship Query

Explore relationships in the graph:

```
What asset managers own both Apple and Microsoft? What risks do these companies share?
```

**Expected behavior:**
1. Agent may make multiple tool calls
2. Explores ownership and risk relationships
3. Synthesizes findings into a coherent response

![Relationship Query](images/relationship_query.png)

---

## Part 5: Review Agent Traces

GAAB provides visibility into how the agent processes requests.

### Step 17: View Execution Traces

1. After running queries, click **View Traces** (or expand the trace panel)
2. You'll see the agent's reasoning process:
   - Tool selection decisions
   - MCP server calls
   - Query results
   - Response synthesis

![Agent Traces](images/agent_traces.png)

This helps you understand how the agent:
- Interprets user questions
- Selects appropriate tools
- Constructs Cypher queries
- Formulates responses

---

## Troubleshooting

### Can't access the dashboard
- Verify you have the correct URL from your instructor
- Check that you're using the right email and password
- Try refreshing the page or clearing browser cache

### MCP server connection fails
- Verify the endpoint URL is correct
- Check that the MCP server is running (ask instructor)
- Ensure OAuth authentication is properly configured

### Agent doesn't use tools
- Review the system prompt for clarity
- Check that tools are enabled (green checkmark)
- Try more specific questions that clearly need data

### Cypher queries return no results
- Use exact company names (e.g., "APPLE INC" not "Apple")
- Check if the backup was restored correctly in Lab 1
- Try asking for the schema first to understand the data

### Slow responses
- Agent processing can take 10-30 seconds for complex queries
- Multiple tool calls increase response time
- Try simpler queries if timeouts occur

---

## Summary

You have now created an AI agent with:
- **Claude 3.5 Sonnet** for reasoning
- **System prompt** tailored for SEC filings analysis
- **Neo4j MCP Server** connection for knowledge graph queries
- **Working tools** for schema exploration and Cypher queries

**This completes Part 1 (No-Code Track) of the workshop.**

## Comparing Approaches

| Feature | Aura Agents (Lab 2) | GAAB Agents (Lab 4) |
|---------|---------------------|---------------------|
| Platform | Neo4j Aura console | AWS GAAB dashboard |
| Model | OpenAI (via Neo4j) | Claude (via Bedrock) |
| Tool Integration | Pre-built templates | MCP server connection |
| Deployment | Aura-managed | AWS-managed |
| Tracing | Basic | Detailed execution traces |
| Best for | Quick prototyping | AWS-integrated apps |

Both approaches achieve similar results - the choice depends on your infrastructure preferences.

## What's Next

To continue with the coding labs in Part 2:

1. Continue to [Lab 5 - Start Codespace](../Lab_5_Start_Codespace/) to set up your development environment
2. Then proceed to [Lab 6 - Building a Knowledge Graph](../Lab_6_Knowledge_Graph/) to build your own knowledge graph from SEC filings
3. In [Lab 8 - Agents](../Lab_8_Agents/), you'll build similar agents programmatically using the Strands Agents SDK

---

## Appendix A: Deploying GAAB

If you're running this workshop independently, here's how to deploy GAAB:

### Option 1: CloudFormation (Recommended)

1. Go to the [GAAB AWS Solutions page](https://aws.amazon.com/solutions/implementations/generative-ai-application-builder-on-aws/)
2. Click **Launch in the AWS Console**
3. Fill in the required parameters:
   - Admin email address
   - VPC configuration (optional)
4. Wait for stack creation (~10 minutes)
5. Check your email for dashboard access credentials

### Option 2: CDK Deployment

```bash
# Clone the repository
git clone https://github.com/aws-solutions/generative-ai-application-builder-on-aws.git
cd generative-ai-application-builder-on-aws

# Install dependencies
cd source/infrastructure
npm install
npm run build

# Deploy
cdk deploy DeploymentPlatformStack --parameters AdminUserEmail=your@email.com
```

### Deploying the Neo4j MCP Server

The Neo4j MCP server can be deployed to GAAB using the Runtime method:

1. Build a Docker image with the Neo4j MCP server
2. Push to Amazon ECR
3. In GAAB dashboard, create new MCP Server → Runtime method
4. Configure with your Neo4j Aura credentials

See the [Neo4j MCP Server documentation](https://github.com/neo4j/mcp-neo4j) for details.

---

## References

- [Generative AI Application Builder on AWS](https://aws.amazon.com/solutions/implementations/generative-ai-application-builder-on-aws/)
- [GAAB GitHub Repository](https://github.com/aws-solutions/generative-ai-application-builder-on-aws)
- [GAAB Implementation Guide](https://docs.aws.amazon.com/solutions/latest/generative-ai-application-builder-on-aws/)
- [Neo4j MCP Server](https://github.com/neo4j/mcp-neo4j)
- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)
