# Implementation Plan V2: Neo4j and AWS Bedrock Workshop Migration

This document provides a step-by-step migration plan with detailed todo lists for each phase. Each step is written in plain English without code examples.

---

## Overview

The migration is organized into 10 steps:

| Step | Description | Effort Level | Status |
|------|-------------|--------------|--------|
| Step 1 | Project Setup and Configuration Files | Foundation | COMPLETE |
| Step 2 | Lab 0 - AWS Console Sign-In | Documentation Only | COMPLETE |
| Step 3 | Lab 1 - Neo4j Aura via AWS Marketplace | Documentation Only | COMPLETE |
| Step 4 | Lab 2 - Aura Agents (No Changes) | Verification Only | COMPLETE |
| Step 5 | Lab 3 - Bedrock Agents | Major Rewrite | COMPLETE |
| Step 6 | Lab 4 - Development Environment | Moderate Updates | Pending |
| Step 7 | Lab 5 - Knowledge Graph Notebooks | Code Updates | Pending |
| Step 8 | Lab 6 - Retriever Notebooks | Code Updates | Pending |
| Step 9 | Lab 7 - Agent Notebooks | Full Rewrite | Pending |
| Step 10 | Lab 8 - Hybrid Search | Minor Updates | Pending |

---

## Step 1: Project Setup and Configuration Files

**Purpose**: Establish the foundation for all AWS-specific code and configuration before touching individual labs.

### What This Step Accomplishes
- Creates the AWS-specific environment configuration
- Sets up the Python dependencies for AWS
- Prepares the shared configuration module that all notebooks will use
- Establishes the CDK infrastructure skeleton

### Todo List

- [x] Create new .env.sample file with AWS environment variables
  - Add AWS_REGION variable (default to us-east-1)
  - Add AWS_BEDROCK_MODEL_ID variable for Claude Sonnet
  - Add AWS_BEDROCK_EMBEDDING_MODEL_ID variable for Titan Embeddings V2
  - Add EMBEDDING_DIMENSIONS variable set to 1024
  - Keep existing NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD variables unchanged
  - Add NEO4J_VECTOR_INDEX_NAME variable

- [x] Update pyproject.toml with AWS dependencies
  - Remove azure-identity package
  - Remove azure-ai-projects package
  - Remove azure-ai-inference package
  - Remove agent-framework-core package
  - Remove agent-framework-azure-ai package
  - Add boto3 package for AWS SDK
  - Add botocore package for AWS SDK foundation
  - Add strands-agents package for agent framework
  - Add strands-agents-tools package for pre-built tools
  - Add langchain-aws package for LangChain AWS integration
  - Add langchain-community package for Neo4j tools
  - Keep neo4j, neo4j-graphrag, python-dotenv, and pydantic unchanged

- [x] Update config.py module for AWS authentication
  - Remove Azure token acquisition function
  - Create function to initialize Bedrock Runtime client using boto3
  - Create BedrockEmbedder class that implements the neo4j-graphrag Embedder interface
  - Create BedrockLLM class that implements the neo4j-graphrag LLMInterface
  - Create get_embedder function that returns BedrockEmbedder instance
  - Create get_llm function that returns BedrockLLM instance
  - Update any configuration classes to use AWS endpoints

- [x] Create CDK infrastructure skeleton
  - Create infra/cdk directory structure
  - Create app.py as the CDK application entry point
  - Create stacks directory for stack definitions
  - Create bedrock_stack.py placeholder for Bedrock configuration
  - Create monitoring_stack.py placeholder for CloudWatch setup
  - Add cdk.json configuration file
  - Add requirements.txt for CDK dependencies

- [x] Create setup_env.py script for CDK output synchronization
  - Script should read CDK deployment outputs
  - Script should write outputs to .env file
  - Script should validate Bedrock model access

- [x] Create .devcontainer configuration for AWS tooling
  - devcontainer.json with AWS CLI and Node.js features
  - post_create.sh for initial setup
  - post_start.sh for environment configuration
  - GUIDE_DEV_CONTAINERS.md with setup instructions

### Validation Criteria
- Running pip install with new pyproject.toml succeeds
- The config.py module imports without errors
- CDK synth command runs without errors (even if stacks are empty)

---

## Step 2: Lab 0 - AWS Console Sign-In

**Purpose**: Update the sign-in instructions from Azure Portal to AWS Console.

### What This Step Accomplishes
- Participants can successfully sign into their AWS accounts
- Participants understand how to navigate to required AWS services
- Participants can verify they have the necessary permissions

### Todo List

- [x] Update Lab_0_Sign_In/README.md
  - Replace Azure Portal references with AWS Console references
  - Update sign-in URL from Azure to AWS Console
  - Replace Resource Group terminology with AWS Account or Region concepts
  - Add instructions for selecting the correct AWS region
  - Recommend us-east-1 or us-west-2 for Bedrock availability
  - Add section on verifying Bedrock service access in the console

- [ ] Capture new screenshots for AWS sign-in flow (pending actual AWS access)
  - AWS Console login page
  - AWS Console home page after login
  - Region selector dropdown
  - Services menu showing Bedrock option
  - Bedrock console landing page

- [x] Update credential distribution instructions
  - Document how participants receive AWS credentials (IAM users or SSO)
  - Explain any workshop-specific credential distribution mechanism
  - Include instructions for setting up AWS CLI credentials if needed

- [x] Add troubleshooting section
  - Common sign-in issues and solutions
  - How to verify correct account access
  - What to do if Bedrock is not visible in services

### Validation Criteria
- A new user can follow the instructions and sign into AWS Console
- User can navigate to Amazon Bedrock console
- All screenshots match the current AWS Console interface

---

## Step 3: Lab 1 - Neo4j Aura via AWS Marketplace

**Purpose**: Update the Neo4j Aura subscription instructions from Azure Marketplace to AWS Marketplace.

### What This Step Accomplishes
- Participants can subscribe to Neo4j Aura through AWS Marketplace
- Participants understand AWS billing integration for marketplace purchases
- Database creation and backup restore process remains unchanged

### Todo List

- [x] Update Lab_1_Aura_Setup/Neo4j_Aura_Signup.md for AWS Marketplace
  - Replace Azure Marketplace navigation with AWS Marketplace navigation
  - Update URL to AWS Marketplace Neo4j listing
  - Explain AWS Marketplace subscription workflow
  - Document the pay-as-you-go option selection
  - Explain how AWS billing integrates with Neo4j Aura
  - Note that AWS credits can be applied to usage

- [ ] Capture new AWS Marketplace screenshots (pending actual AWS access)
  - AWS Marketplace search results for Neo4j
  - Neo4j Aura product listing page
  - Subscription configuration page
  - Billing terms and pricing page
  - Subscription confirmation screen
  - Link to Neo4j Aura console from AWS

- [x] Update Lab_1_Aura_Setup/README.md
  - Replace any Azure-specific references with AWS references
  - Update region recommendations (no longer Azure US West, Arizona)
  - Keep database creation instructions unchanged (cloud-agnostic)
  - Keep backup restoration instructions unchanged

- [x] Create Lab_1_Aura_Setup/EXPLORE.md
  - Document Neo4j Explore visual navigation
  - Graph Data Science algorithm examples
  - Pattern search instructions

- [ ] Verify Part B (Backup Restoration) still works (requires testing)
  - Confirm 12MB finance_data.backup file is still valid
  - Confirm restoration instructions are accurate for AWS-provisioned Aura

- [ ] Verify Part C (Graph Exploration) needs no changes (requires testing)
  - Confirm Neo4j Explore tool screenshots are still accurate
  - Confirm all pattern searches work identically
  - Confirm Graph Data Science algorithm examples work

### Validation Criteria
- A new user can follow instructions to subscribe to Neo4j Aura via AWS Marketplace
- User can create database instance successfully
- Backup restoration completes without errors
- All graph exploration examples work as documented

---

## Step 4: Lab 2 - Aura Agents (Verification Only)

**Purpose**: Verify that Aura Agents content requires no changes since it is Neo4j's own platform.

### What This Step Accomplishes
- Confirms the lab works identically for AWS-provisioned Aura instances
- Identifies any unexpected AWS-specific issues

### Todo List

- [ ] Test all Aura Agents functionality with AWS-provisioned Neo4j (requires testing)
  - Test Cypher Template tool creation and execution
  - Test Similarity Search tool configuration
  - Test Text2Cypher tool operation
  - Verify agent testing produces expected results

- [x] Review Lab_2_Aura_Agents/README.md for any Azure references
  - Search for any Azure-specific terminology
  - Search for any Azure-specific URLs or links
  - Update any found references to be cloud-agnostic or AWS-specific

- [x] Create Lab_2_Aura_Agents/README.md
  - Document all three tool types (Cypher Templates, Similarity Search, Text2Cypher)
  - Include agent configuration and testing instructions
  - Update Next Steps to point to Lab 3 Bedrock Agents

- [ ] Verify all screenshots are still accurate (requires testing)
  - Aura Agents interface screenshots should be unchanged
  - Tool configuration screenshots should be unchanged
  - Testing interface screenshots should be unchanged

### Validation Criteria
- All three tool types work correctly with AWS-provisioned Aura
- No Azure-specific references remain in documentation
- Agent testing produces same results as Azure version

---

## Step 5: Lab 3 - Bedrock Agents (Major Rewrite)

**Purpose**: Replace Microsoft Foundry Agent instructions with Amazon Bedrock Agent instructions.

### What This Step Accomplishes
- Participants learn to navigate the Amazon Bedrock console
- Participants enable required foundation models
- Participants create a Bedrock Agent with Neo4j MCP Server integration
- Participants test agent interactions through the Bedrock console

### Todo List

#### Section 1: Bedrock Model Access

- [x] Write instructions for navigating to Bedrock console
  - How to find Bedrock in the AWS services menu
  - Understanding the Bedrock console layout
  - Identifying the Model access section

- [x] Document model access request process
  - Navigate to Model access page
  - Request access for Claude Sonnet (or Claude Haiku as alternative)
  - Request access for Amazon Titan Text Embeddings V2
  - Explain that Titan is usually instant, Claude may take minutes
  - How to verify model access is granted

- [ ] Capture model access screenshots (pending actual AWS access)
  - Model access page showing available models
  - Access request form
  - Pending access status
  - Granted access confirmation

#### Section 2: Bedrock Agent Creation

- [x] Write instructions for creating a Bedrock Agent
  - Navigate to Agents section in Bedrock console
  - Click Create agent button
  - Enter agent name and description
  - Configure agent instructions (system prompt)
  - Select foundation model (recommend Claude Sonnet)
  - Understanding agent settings and options

- [x] Document action group configuration
  - What action groups are and how they work
  - Options for defining tools (Lambda, API schema, MCP)
  - Preparing for MCP server integration

- [ ] Capture agent creation screenshots (pending actual AWS access)
  - Agents list page
  - Create agent form
  - Agent instruction configuration
  - Model selection dropdown
  - Agent settings page

#### Section 3: MCP Server Integration via AgentCore

- [x] Write instructions for AgentCore Runtime deployment
  - Navigate to AgentCore section
  - Understanding AgentCore Runtime vs AgentCore Gateway
  - Deploying Neo4j MCP Server to AgentCore Runtime
  - Configuring MCP server with Neo4j connection details

- [x] Document connecting MCP tools to Bedrock Agent
  - How AgentCore Gateway discovers MCP tools
  - Adding MCP tools as action group to agent
  - Configuring tool permissions and access

- [x] Write Neo4j connection configuration
  - Where to enter Neo4j URI from Lab 1
  - Where to enter Neo4j username
  - Where to enter Neo4j password
  - Testing connection before saving

- [ ] Capture MCP integration screenshots (pending actual AWS access)
  - AgentCore Runtime console
  - MCP server deployment configuration
  - Neo4j connection settings form
  - Tool discovery results
  - Action group configuration with MCP tools

#### Section 4: Testing the Agent

- [x] Write instructions for testing agent in console
  - Navigate to agent test interface
  - Entering test prompts
  - Understanding agent responses
  - Viewing tool invocation logs

- [x] Create test scenarios
  - Test schema exploration prompt
  - Test data query prompt
  - Test multi-step reasoning prompt
  - Expected outputs for each test

- [ ] Capture testing screenshots (pending actual AWS access)
  - Agent test interface
  - Sample conversation showing tool use
  - Tool invocation details panel
  - Successful query results

#### Documentation Assembly

- [x] Create complete Lab_3_Bedrock_Agents/README.md
  - Combine all sections into cohesive document
  - Add introduction explaining Bedrock Agents concepts
  - Add summary and next steps section
  - Add troubleshooting section for common issues

- [x] Create lab folder structure
  - Created Lab_3_Bedrock_Agents folder
  - Created images subdirectory for screenshots
  - Updated cross-references from other labs

### Validation Criteria
- New user can enable model access successfully
- New user can create Bedrock Agent following instructions
- MCP server connects to Neo4j Aura successfully
- Agent responds correctly to test prompts
- All screenshots match current Bedrock console interface

---

## Step 6: Lab 4 - Development Environment Setup

**Purpose**: Update the GitHub Codespaces configuration for AWS tooling and create CDK deployment workflow.

### What This Step Accomplishes
- Codespaces launch with AWS CLI and CDK pre-installed
- Participants can deploy infrastructure using CDK
- Environment variables sync from CDK outputs

### Todo List

#### Devcontainer Updates

- [ ] Update .devcontainer/devcontainer.json
  - Replace Azure CLI feature with AWS CLI v2 feature
  - Replace Azure Developer CLI with Node.js for CDK CLI
  - Keep Python 3.12 feature unchanged
  - Update postCreateCommand to install AWS CDK globally
  - Update postCreateCommand to install strands-agents packages
  - Remove Azure-specific VS Code extensions
  - Add AWS Toolkit VS Code extension

- [ ] Update .devcontainer/post-create.sh (if exists)
  - Remove any Azure CLI configuration
  - Add AWS CLI configuration verification
  - Add CDK version check
  - Add Python dependency installation

#### CDK Deployment Documentation

- [ ] Write CDK bootstrap instructions
  - Explain what CDK bootstrap does (one-time setup)
  - Provide the bootstrap command
  - Explain region considerations for bootstrap
  - Document expected bootstrap output

- [ ] Write CDK deployment instructions
  - Document the cdk deploy command
  - Explain what resources are created
  - Document how to view deployment progress
  - Explain stack outputs and their meaning

- [ ] Document output synchronization
  - How to run setup_env.py script
  - What environment variables are populated
  - How to verify configuration is complete

#### Lab Documentation

- [ ] Update Lab_4_Start_Codespace/README.md
  - Replace azd references with CDK references
  - Update environment setup instructions
  - Document AWS credential configuration in Codespaces
  - Explain how to set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
  - Or explain how to use AWS SSO with Codespaces

- [ ] Add local machine setup alternative
  - Document requirements for local development
  - AWS CLI installation instructions
  - CDK CLI installation instructions
  - Python environment setup

- [ ] Capture new screenshots
  - Codespaces launch screen
  - Terminal showing AWS CLI version
  - Terminal showing CDK version
  - CDK deploy output
  - setup_env.py execution

### Validation Criteria
- Codespaces launches successfully with all tools installed
- aws --version returns expected version
- cdk --version returns expected version
- CDK deploy creates resources without errors
- setup_env.py populates .env file correctly

---

## Step 7: Lab 5 - Knowledge Graph Notebooks

**Purpose**: Update the four Jupyter notebooks to use Bedrock embeddings and LLM instead of Azure OpenAI.

### What This Step Accomplishes
- Notebooks use BedrockEmbedder from config.py
- Notebooks use BedrockLLM from config.py
- Vector indexes use 1024 dimensions instead of 1536
- All knowledge graph building functionality works with AWS services

### Todo List

#### Notebook 01: Data Loading

- [ ] Review notebook for any Azure references
  - This notebook should be cloud-agnostic (Neo4j only)
  - Search for any Azure imports or configuration
  - Verify Document and Chunk node creation works unchanged

- [ ] Test notebook execution
  - Run all cells in order
  - Verify data loads correctly
  - Confirm no errors or warnings

#### Notebook 02: Embeddings

- [ ] Update imports section
  - Remove any Azure-related imports
  - Add import for BedrockEmbedder from config
  - Keep Neo4j imports unchanged

- [ ] Update embedder initialization
  - Replace Azure OpenAI embedder with BedrockEmbedder
  - Use get_embedder() function from config module
  - Remove any Azure-specific configuration

- [ ] Update vector index creation
  - Change dimension from 1536 to 1024
  - Update index creation Cypher statement
  - Document the dimension change in markdown cell

- [ ] Update any dimension references in code
  - Search for 1536 throughout notebook
  - Replace with 1024 or EMBEDDING_DIMENSIONS variable
  - Update any explanatory text about dimensions

- [ ] Test notebook execution
  - Run all cells in order
  - Verify embeddings generate correctly
  - Verify vector index creates successfully
  - Confirm chunk nodes have embedding properties

#### Notebook 03: Entity Extraction

- [ ] Update imports section
  - Remove Azure AI client imports
  - Add import for BedrockLLM from config
  - Keep Neo4j imports unchanged

- [ ] Update LLM initialization
  - Replace Azure AI client with BedrockLLM
  - Use get_llm() function from config module
  - Remove any Azure-specific configuration

- [ ] Verify entity extraction prompts work with Claude
  - Review extraction prompts for compatibility
  - Test that Claude returns expected entity format
  - Adjust prompts if needed for better results

- [ ] Test notebook execution
  - Run all cells in order
  - Verify entities extract correctly
  - Verify entity nodes create in Neo4j
  - Verify relationships create correctly

#### Notebook 04: Full Dataset Processing

- [ ] Apply same changes as Notebooks 02 and 03
  - Update embedder initialization
  - Update LLM initialization
  - Update dimension references

- [ ] Consider batch processing documentation
  - Add note about Bedrock batch inference option
  - Document cost considerations for large datasets
  - Keep current sequential approach but mention alternatives

- [ ] Test notebook execution
  - Run all cells (may take longer)
  - Verify complete dataset processes
  - Verify all nodes and relationships created

#### Lab Documentation

- [ ] Update Lab_5_Knowledge_Graph/README.md
  - Replace Azure OpenAI references with Bedrock references
  - Document the 1024 dimension change from 1536
  - Update any model name references
  - Keep learning objectives unchanged

### Validation Criteria
- All four notebooks run without errors
- Vector embeddings have 1024 dimensions
- Entity extraction produces correct entities
- Knowledge graph matches expected structure
- All validation queries in notebooks pass

---

## Step 8: Lab 6 - Retriever Notebooks

**Purpose**: Update the three retriever notebooks to use Bedrock embeddings and LLM.

### What This Step Accomplishes
- VectorRetriever works with BedrockEmbedder
- VectorCypherRetriever works with BedrockEmbedder
- Text2CypherRetriever works with BedrockLLM
- All retrieval patterns demonstrate correctly

### Todo List

#### Notebook 01: Vector Retriever

- [ ] Update imports section
  - Remove any Azure-related imports
  - Add import for BedrockEmbedder from config
  - Keep neo4j-graphrag imports unchanged

- [ ] Update embedder initialization
  - Replace Azure OpenAI embedder with BedrockEmbedder
  - Use get_embedder() function from config module

- [ ] Verify VectorRetriever works with BedrockEmbedder
  - neo4j-graphrag VectorRetriever should work with any Embedder
  - Test similarity search queries
  - Verify results match expected outputs

- [ ] Test notebook execution
  - Run all cells in order
  - Verify retrieval returns relevant results
  - Confirm similarity scores are reasonable

#### Notebook 02: Vector + Cypher Retriever

- [ ] Update embedder initialization
  - Same changes as Notebook 01
  - Replace Azure embedder with BedrockEmbedder

- [ ] Verify VectorCypherRetriever works correctly
  - Test with existing Cypher queries
  - Verify combined results are correct
  - Confirm graph traversal after vector search works

- [ ] Test notebook execution
  - Run all cells in order
  - Verify combined retrieval works
  - Confirm Cypher enhancement produces better results

#### Notebook 03: Text2Cypher Retriever

- [ ] Update imports section
  - Remove Azure LLM imports
  - Add import for BedrockLLM from config
  - Keep neo4j-graphrag imports unchanged

- [ ] Update LLM initialization
  - Replace Azure LLM with BedrockLLM
  - Use get_llm() function from config module

- [ ] Verify Text2CypherRetriever works with Claude
  - Claude excels at code generation including Cypher
  - Test with various natural language queries
  - Verify generated Cypher is syntactically correct
  - Verify query results are accurate

- [ ] Add documentation about Claude Cypher generation
  - Note that Claude models are strong at code generation
  - Mention this as an advantage for Text2Cypher

- [ ] Test notebook execution
  - Run all cells in order
  - Test multiple query types
  - Verify Cypher generation and execution

#### Lab Documentation

- [ ] Update Lab_6_Retrievers/README.md
  - Replace Azure references with Bedrock references
  - Document any model-specific behavior differences
  - Keep learning objectives unchanged

### Validation Criteria
- All three notebooks run without errors
- Vector similarity search returns relevant results
- VectorCypher retrieval enhances basic vector search
- Text2Cypher generates valid and accurate Cypher
- All example queries produce expected results

---

## Step 9: Lab 7 - Agent Notebooks (Full Rewrite)

**Purpose**: Replace Microsoft Agent Framework notebooks with Strands Agents SDK notebooks.

### What This Step Accomplishes
- Participants learn Strands Agents SDK patterns
- Schema agent demonstrates basic tool usage
- Multi-tool agent shows vector and graph combination
- Text2Cypher agent shows complex tool selection
- All agents use Bedrock Claude as the foundation model

### Todo List

#### Notebook 01: Simple Agent (Schema Tool)

- [ ] Create new notebook structure
  - Add title and introduction markdown cells
  - Explain Strands Agents SDK concepts
  - Document the @tool decorator pattern

- [ ] Write imports section
  - Import Agent from strands
  - Import tool decorator from strands.tools
  - Import Neo4j driver from config
  - Import any needed utilities

- [ ] Create get_graph_schema tool
  - Use @tool decorator
  - Write clear docstring describing what the tool does
  - Implement function to return schema from Neo4j driver
  - Add parameter and return type hints

- [ ] Create simple agent
  - Define system prompt explaining the agent's purpose
  - Add get_graph_schema as the only tool
  - Explain that Strands uses Bedrock Claude by default

- [ ] Write agent execution examples
  - Example query asking about graph structure
  - Show agent response with schema information
  - Demonstrate the agent's reasoning process

- [ ] Add explanatory markdown cells
  - Explain how @tool decorator works
  - Explain how agent selects tools
  - Compare briefly to Azure approach (at high level)

#### Notebook 02: Vector + Graph Agent

- [ ] Create new notebook structure
  - Add title and introduction
  - Explain multi-tool agent concepts
  - Document tool selection behavior

- [ ] Write imports section
  - All imports from Notebook 01
  - Add vector retriever import
  - Consider LangChain tool integration import

- [ ] Create get_graph_schema tool
  - Same implementation as Notebook 01

- [ ] Create search_content tool
  - Use @tool decorator
  - Write docstring explaining semantic search capability
  - Implement function using vector retriever
  - Return formatted search results

- [ ] Create multi-tool agent
  - Define system prompt with tool selection guidance
  - Add both tools to agent
  - Explain how agent chooses between tools

- [ ] Write agent execution examples
  - Example query requiring schema tool
  - Example query requiring semantic search
  - Example query that might use both
  - Show agent reasoning for tool selection

- [ ] Document LangChain tool integration option
  - Explain that Strands can use LangChain tools
  - Show alternative approach using existing Neo4j LangChain tools
  - Note this is optional/advanced

#### Notebook 03: Text2Cypher Agent

- [ ] Create new notebook structure
  - Add title and introduction
  - Explain three-tool agent architecture
  - Document query type routing

- [ ] Write imports section
  - All imports from Notebook 02
  - Add Text2Cypher retriever import

- [ ] Create all three tools
  - get_graph_schema tool (same as before)
  - search_content tool (same as before)
  - query_database tool using Text2Cypher retriever

- [ ] Create three-tool agent
  - Define comprehensive system prompt
  - Include guidance on when to use each tool
  - Explain schema queries vs semantic queries vs factual queries

- [ ] Write agent execution examples
  - Example requiring schema exploration
  - Example requiring semantic search
  - Example requiring database query (counts, lists, specifics)
  - Example showing multi-step reasoning

- [ ] Add troubleshooting section
  - Common issues with tool selection
  - How to improve prompts for better routing
  - Debugging tool execution

#### Lab Documentation

- [ ] Create complete Lab_7_Agents/README.md rewrite
  - Remove all Microsoft Agent Framework content
  - Document Strands Agents SDK concepts
  - Explain @tool decorator pattern
  - Document system prompt best practices
  - Add section on Strands advantages

- [ ] Document key differences from Azure version
  - Synchronous vs asynchronous API
  - @tool decorator vs docstring-only approach
  - Implicit Bedrock authentication vs explicit credentials
  - Built-in streaming behavior

- [ ] Add optional advanced content
  - MCP server integration with Strands (alternative approach)
  - Multi-agent patterns for complex workflows
  - AgentCore deployment for production

### Validation Criteria
- All three notebooks run without errors
- Schema agent correctly returns graph structure
- Multi-tool agent selects appropriate tool based on query
- Text2Cypher agent handles all three query types correctly
- Agent responses are coherent and accurate
- All example interactions produce expected behavior

---

## Step 10: Lab 8 - Hybrid Search (Minor Updates)

**Purpose**: Update the optional hybrid search notebooks for Bedrock embeddings.

### What This Step Accomplishes
- Fulltext search functionality verified (no changes needed)
- Hybrid search uses BedrockEmbedder for vector component
- All hybrid retrieval patterns work correctly

### Todo List

#### Notebook 01: Fulltext Search

- [ ] Review notebook for any Azure references
  - Fulltext search is pure Neo4j functionality
  - Should require no embedding or LLM changes
  - Verify fulltext index creation works

- [ ] Test notebook execution
  - Run all cells in order
  - Verify fulltext search returns expected results
  - Confirm keyword matching works correctly

#### Notebook 02: Hybrid Search

- [ ] Update embedder initialization
  - Replace Azure embedder with BedrockEmbedder
  - Use get_embedder() function from config module

- [ ] Verify HybridRetriever works correctly
  - Test combined vector and keyword search
  - Verify result ranking is appropriate
  - Confirm fusion of results works

- [ ] Verify HybridCypherRetriever works correctly
  - Test hybrid search with Cypher enhancement
  - Verify combined approach produces better results

- [ ] Test notebook execution
  - Run all cells in order
  - Compare hybrid results to vector-only results
  - Verify hybrid approach provides value

#### Lab Documentation

- [ ] Update Lab_8_Hybrid_Search/README.md
  - Replace any Azure references with Bedrock references
  - Keep Neo4j fulltext index documentation unchanged
  - Document any behavior differences observed

### Validation Criteria
- Both notebooks run without errors
- Fulltext search returns keyword-matched results
- Hybrid search combines vector and keyword effectively
- HybridCypherRetriever enhances hybrid results with graph data

---

## Final Steps: Polish and Testing

**Purpose**: Complete end-to-end testing and documentation cleanup.

### Todo List

- [ ] Run complete workshop flow (Labs 0-8)
  - Use fresh AWS account or credentials
  - Follow all instructions as a new participant would
  - Document actual execution issues

- [ ] Update all presentation slides
  - Lab 3 slides: Create new aws-bedrock-slides.md
  - Lab 7 slides: Create new strands-agents-slides.md
  - Lab 2 slides: Minor MCP reference updates
  - Verify Labs 1, 5, 6 slides need no changes

- [ ] Create troubleshooting guide
  - Common Bedrock model access issues
  - Common CDK deployment issues
  - Common Neo4j connection issues
  - Common notebook execution issues

- [ ] Update root level README.md
  - Replace Azure workshop description with AWS
  - Update prerequisites for AWS
  - Update architecture diagram reference
  - Update any Azure-specific links

- [ ] Archive or remove Azure-specific files
  - Decide whether to keep Azure Bicep templates
  - Document any files that were replaced vs archived
  - Clean up any orphaned Azure references

### Validation Criteria
- Complete workshop flow works end-to-end
- All documentation is consistent (no mixed Azure/AWS references)
- Troubleshooting guide covers observed issues
- Repository is clean and organized

---

## Dependency Graph

The following shows which steps depend on others:

```
Step 1 (Foundation) ─┬─→ Step 6 (Codespace) ─┬─→ Step 7 (Lab 5)
                     │                        ├─→ Step 8 (Lab 6)
                     │                        ├─→ Step 9 (Lab 7)
                     │                        └─→ Step 10 (Lab 8)
                     │
                     └─→ Step 5 (Lab 3 Bedrock)

Step 2 (Lab 0) ─→ Step 3 (Lab 1) ─→ Step 4 (Lab 2)
                                          │
                                          └─→ (All coding labs need Neo4j)
```

**Recommended Order**:
1. Complete Steps 1-4 first (foundation and no-code labs)
2. Complete Step 5 (Lab 3 Bedrock) - can be parallel with Steps 2-4
3. Complete Step 6 (Codespace) after Step 1
4. Complete Steps 7-10 after Step 6, in order or parallel as resources allow
5. Complete Final Steps last

---

## Notes

### Cost Considerations
- Recommend Claude Haiku for workshop exercises to reduce costs
- Amazon Titan Embeddings V2 is more cost-effective than Azure ada-002
- Consider pre-provisioning shared account for instructor-led workshops

### Regional Guidance
- us-east-1 has widest Bedrock model availability
- Document any model restrictions in other regions
- Neo4j Aura region is independent of Bedrock region

### Testing Requirements
- Each step should be tested before moving to dependent steps
- Keep notes on actual vs expected behavior
- Document any workarounds discovered
