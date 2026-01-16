# Implementation Plan: Neo4j and AWS Bedrock Workshop

This document outlines the implementation plan for adapting the existing "Neo4j and Azure Generative AI Workshop" to Amazon Web Services. The plan is written in plain English without code examples.

---

## Executive Summary

The goal is to create a parallel AWS version of the existing Azure workshop while maintaining the educational structure and learning outcomes. The workshop teaches GraphRAG (Graph Retrieval-Augmented Generation) patterns using Neo4j Aura combined with cloud AI services.

**Key Principle**: Labs 0, 1, and 2 remain unchanged in structure and purpose. They are cloud-agnostic in their Neo4j functionality, requiring only screenshot and navigation updates for AWS Marketplace.

---

## Part 1: Labs That Require Documentation Updates Only (No Structural Changes)

### Lab 0: Sign In

**Current State**: Guides participants through OneBlink registration and Azure Portal sign-in to receive credentials and resource group information.

**AWS Adaptation Approach**:
- Replace Azure Portal sign-in instructions with AWS Console sign-in instructions
- Update screenshots to show AWS Console interface
- Replace "Resource Group" terminology with appropriate AWS concepts (e.g., "Account" or "Region")
- Maintain the OneBlink registration flow if continuing to use that service, or create equivalent credential distribution mechanism for AWS accounts
- Add region selection guidance (recommend us-east-1 or us-west-2 for Bedrock availability)

**Deliverables**:
- Updated README.md with AWS Console navigation
- New screenshot set for AWS sign-in flow
- Instructions for verifying Bedrock service access

---

### Lab 1: Neo4j Aura Setup and Exploration

**Current State**: Three-part lab covering Neo4j Aura subscription via Azure Marketplace, database restoration, and visual exploration using Neo4j tools.

**AWS Adaptation Approach**:

**Part A - Marketplace Subscription**:
- Update instructions to navigate AWS Marketplace instead of Azure Marketplace
- Replace screenshots showing Azure Marketplace interface with AWS Marketplace equivalents
- Update subscription flow documentation (AWS billing integration instead of Azure)
- Keep the same Neo4j Aura Professional (pay-as-you-go) tier recommendation
- Update region guidance to reflect AWS availability (no longer "Azure US West, Arizona" but equivalent AWS region)

**Part B - Backup Restoration**:
- No changes required - the backup file is cloud-agnostic
- Same 12MB finance_data.backup file works identically
- Instructions for restoration through Aura console remain the same

**Part C - Graph Exploration**:
- No changes required - Neo4j Explore tool is cloud-agnostic
- Same pattern searches, Graph Data Science algorithms, and visualizations
- All screenshots of Neo4j interface remain valid

**Deliverables**:
- Updated Neo4j_Aura_Signup.md with AWS Marketplace flow
- New AWS Marketplace screenshot set
- Minor updates to README.md reflecting AWS context
- EXPLORE.md and graph exploration content unchanged

---

### Lab 2: Aura Agents (No-Code)

**Current State**: Teaches participants to build AI agents using Neo4j's Aura Agents platform with Cypher Templates, Similarity Search, and Text2Cypher tools.

**AWS Adaptation Approach**:
- No changes required - Aura Agents is Neo4j's own platform
- The platform operates independently of where the Aura instance is provisioned
- All three tool types (Cypher Templates, Similarity Search, Text2Cypher) work identically
- Agent testing examples and expected outputs remain the same

**Deliverables**:
- README.md unchanged (possibly minor reference updates)
- All agent configuration and testing instructions unchanged
- Screenshots of Aura Agents interface unchanged

---

## Part 2: Labs Requiring Significant Adaptation

### Lab 3: Foundry Agents becomes Bedrock Agents

**Current State**: Manual setup of Microsoft Foundry project, gpt-4o-mini deployment, and agent creation with MCP server integration.

**AWS Adaptation Approach**:

**Section 1 - Bedrock Model Access**:
- Document navigation to Amazon Bedrock console
- Explain the model access request process
- Guide participants through enabling Claude Sonnet (or Haiku) for agent tasks
- Guide participants through enabling Amazon Titan Text Embeddings V2
- Note expected approval timeframes (instant for Titan, minutes for Claude)

**Section 2 - Bedrock Agents Setup**:
- Create instructions for Bedrock Agent creation in AWS Console
- Document agent instruction configuration (same prompts work across platforms)
- Explain foundation model selection (recommend Claude Sonnet)
- Document action group configuration for Neo4j tools

**Section 3 - MCP Server Integration**:
- Document AgentCore Runtime deployment of Neo4j MCP Server
- Explain AgentCore Gateway's zero-code MCP tool creation
- Configure Neo4j Aura connection using credentials from Lab 1
- Test agent interactions through Bedrock console

**Deliverables**:
- Complete README.md rewrite for Bedrock console navigation
- New screenshot set for Bedrock interface (approximately 15-20 images)
- Step-by-step agent creation guide
- MCP server integration documentation

---

### Lab 4: Start Codespace (Development Environment)

**Current State**: GitHub Codespaces setup with Azure CLI, Azure Developer CLI (azd), and Python environment configuration.

**AWS Adaptation Approach**:

**Section 1 - Devcontainer Configuration**:
- Replace Azure CLI installation with AWS CLI v2
- Replace Azure Developer CLI with AWS CDK CLI
- Add Strands Agents SDK to Python dependencies
- Update VS Code extensions (AWS Toolkit instead of Azure extensions)
- Keep GitHub Codespaces as the platform (unchanged)

**Section 2 - Infrastructure Deployment**:
- Replace "azd up" workflow with "cdk deploy" workflow
- Document CDK bootstrap process (one-time setup)
- Create equivalent deployment experience to azd
- Sync CDK outputs to environment variables

**Section 3 - Environment Configuration**:
- Create new .env.sample with AWS variables
- Remove all AZURE_ prefixed variables
- Add AWS_REGION, AWS_BEDROCK_MODEL_ID, AWS_BEDROCK_EMBEDDING_MODEL_ID
- Keep NEO4J_ variables unchanged

**Deliverables**:
- Updated devcontainer.json for AWS tooling
- New README.md with AWS-specific setup instructions
- New setup_env.py script for AWS CDK output synchronization
- Updated .env.sample file

---

### Lab 5: Building a Knowledge Graph

**Current State**: Four Jupyter notebooks for data loading, embeddings, entity extraction, and full dataset processing using Azure OpenAI.

**AWS Adaptation Approach**:

**Notebook 01 - Data Loading**:
- No changes required - pure Neo4j operations
- Document and Chunk node creation is cloud-agnostic

**Notebook 02 - Embeddings**:
- Replace Azure OpenAI embedder initialization with Bedrock embedder
- Update embedding dimensions from 1536 (ada-002) to 1024 (Titan V2)
- Update vector index creation to use 1024 dimensions
- Create BedrockEmbedder wrapper compatible with neo4j-graphrag

**Notebook 03 - Entity Extraction**:
- Replace Azure AI client with Bedrock client for LLM calls
- Use Bedrock Converse API for unified model interface
- Maintain same entity extraction prompts and logic

**Notebook 04 - Full Dataset**:
- Apply same changes as Notebooks 02 and 03
- Consider documenting Bedrock batch inference option for large-scale processing

**Deliverables**:
- Updated config.py with Bedrock authentication and client initialization
- BedrockEmbedder class implementation
- BedrockLLM class implementation
- Four updated Jupyter notebooks with AWS integrations

---

### Lab 6: GraphRAG Retrievers

**Current State**: Three Jupyter notebooks demonstrating VectorRetriever, VectorCypherRetriever, and Text2CypherRetriever using Azure OpenAI.

**AWS Adaptation Approach**:

**Notebook 01 - Vector Retriever**:
- Replace embedder initialization with BedrockEmbedder
- VectorRetriever from neo4j-graphrag works with any embedder
- Same retrieval patterns and examples

**Notebook 02 - Vector + Cypher Retriever**:
- Same embedder replacement
- VectorCypherRetriever patterns remain identical
- Custom Cypher queries unchanged

**Notebook 03 - Text2Cypher Retriever**:
- Replace Azure LLM with BedrockLLM for Cypher generation
- Claude models excel at code generation (mention this as advantage)
- Same Text2Cypher patterns and examples

**Deliverables**:
- Three updated Jupyter notebooks using Bedrock models
- Minor documentation updates explaining AWS model selection

---

### Lab 7: GraphRAG Agents

**Current State**: Three Jupyter notebooks using Microsoft Agent Framework with AzureAIClient for schema agent, vector+graph agent, and text2cypher agent.

**AWS Adaptation Approach**:

This lab requires the most significant rewrite. The Microsoft Agent Framework will be replaced with Strands Agents SDK.

**Notebook 01 - Simple Agent (Schema Tool)**:
- Replace AzureAIClient initialization with Strands Agent creation
- Use @tool decorator for tool definition instead of docstring-only approach
- Maintain same get_graph_schema tool functionality
- Update streaming patterns for Strands SDK

**Notebook 02 - Vector + Graph Agent**:
- Define search_content tool using @tool decorator
- Maintain multi-tool agent pattern with Strands
- Same agent reasoning and tool selection behavior
- Consider demonstrating LangChain tool integration

**Notebook 03 - Text2Cypher Agent**:
- Add query_database tool with @tool decorator
- Same three-tool agent architecture
- Maintain same system prompts and tool selection guidance
- Demonstrate agent handling of different query types

**Key Strands SDK Differences to Document**:
- Uses Bedrock Claude by default (no explicit credential management)
- Synchronous, simpler agent creation API
- @tool decorator provides explicit tool registration
- Built-in streaming without explicit async handling
- Native MCP support as alternative approach

**Deliverables**:
- Three completely rewritten Jupyter notebooks using Strands Agents SDK
- New agent patterns documentation
- LangChain integration examples (optional)

---

### Lab 8: Hybrid Search (Optional)

**Current State**: Two Jupyter notebooks for fulltext search and hybrid search using Neo4j indexes.

**AWS Adaptation Approach**:
- Update embedder initialization to use Bedrock
- All Neo4j fulltext index operations remain identical
- Hybrid search combining vector and keyword matching unchanged
- HybridRetriever and HybridCypherRetriever patterns unchanged

**Deliverables**:
- Two updated Jupyter notebooks with Bedrock embedder
- Minor documentation updates

---

## Part 3: Infrastructure and Configuration

### CDK Infrastructure

**Current State**: Azure Bicep templates in /infra/ directory deploying Cognitive Services, Microsoft Foundry, and monitoring.

**AWS Adaptation Approach**:

**New Directory Structure**:
- Create /infra/cdk/ directory with Python CDK application
- BedrockStack for agent configuration and model access
- MonitoringStack for CloudWatch log groups
- Optional AppRunnerStack for production deployment

**Key CDK Constructs**:
- BedrockAgentConstruct for agent creation and IAM roles
- Neo4jToolsConstruct for action group configuration
- CloudWatch integration for observability

**Deployment Commands**:
- Document "cdk bootstrap" for one-time setup
- Document "cdk deploy" as replacement for "azd up"
- Create output retrieval equivalent to "azd env get-values"

**Deliverables**:
- Complete CDK application in Python
- BedrockStack implementation
- MonitoringStack implementation
- Deployment documentation

---

### Python Dependencies

**Current Dependencies to Replace**:
- azure-identity: Remove (replaced by boto3 credential handling)
- azure-ai-projects: Remove
- azure-ai-inference: Remove
- agent-framework-core: Remove
- agent-framework-azure-ai: Remove

**New AWS Dependencies**:
- boto3: Core AWS SDK
- botocore: AWS SDK foundation
- strands-agents: AWS agent framework
- strands-agents-tools: Pre-built Strands tools
- langchain-aws: LangChain AWS integration
- langchain-community: LangChain tools including Neo4j

**Unchanged Dependencies**:
- neo4j: Core Neo4j driver
- neo4j-graphrag: GraphRAG patterns library
- python-dotenv: Environment configuration
- pydantic: Data validation

**Deliverables**:
- Updated pyproject.toml with AWS dependencies
- Dependency documentation in README

---

### Configuration Files

**Environment Variables**:
- Create new .env.sample with AWS-specific variables
- Document required versus optional variables
- Explain embedding dimension change (1536 to 1024)

**Config Module Updates**:
- Replace _get_azure_token() with AWS credential handling
- Create get_embedder() returning BedrockEmbedder
- Create get_llm() returning BedrockLLM or Strands model wrapper
- Update configuration classes for AWS endpoints

**Deliverables**:
- New .env.sample file
- Updated config.py module
- Configuration documentation

---

## Part 4: Presentation Materials

### Slides Requiring Major Updates

**Lab 3 Slides**:
- Replace azure-ai-foundry-slides.md with aws-bedrock-slides.md
- New content covering Bedrock concepts, model access, and console navigation
- Updated screenshots throughout

**Lab 7 Slides**:
- Replace microsoft-agent-framework-slides.md with strands-agents-slides.md
- New content covering Strands SDK architecture and patterns
- Updated code examples (conceptual, not executable)
- LangChain integration explanation

### Slides Requiring Minor Updates

**Lab 2 Slides (MCP)**:
- Update example references from Foundry to Bedrock
- Add note about AgentCore MCP support
- Keep MCP protocol explanation unchanged

### Slides Requiring No Changes

- Lab 1 slides (Neo4j-focused, cloud-agnostic)
- Lab 5 slides (conceptual knowledge graph content)
- Lab 6 slides (retriever architecture concepts)

**Deliverables**:
- Two new slide decks for Labs 3 and 7
- Minor updates to Lab 2 MCP slides

---

## Part 5: Implementation Phases

### Phase 1: Foundation (Start Here)

**Objective**: Establish core AWS infrastructure and configuration patterns.

**Tasks**:
1. Create CDK infrastructure skeleton
2. Implement BedrockStack with model access configuration
3. Create BedrockEmbedder and BedrockLLM wrapper classes in config.py
4. Update .env.sample and configuration documentation
5. Update devcontainer.json for AWS tooling
6. Create setup_env.py for CDK output synchronization

**Validation**: Successfully deploy CDK stack and verify Bedrock model access.

---

### Phase 2: Labs 0-2 Documentation (Parallel with Phase 1)

**Objective**: Update documentation and screenshots for AWS Marketplace flow.

**Tasks**:
1. Document AWS Console sign-in flow for Lab 0
2. Capture AWS Marketplace Neo4j subscription screenshots for Lab 1
3. Update navigation instructions for AWS context
4. Review and update any Azure-specific terminology

**Validation**: Walk through Labs 0-2 with AWS account and verify accuracy.

---

### Phase 3: Lab 3 - Bedrock Agents

**Objective**: Complete rewrite of no-code agent lab for Bedrock.

**Tasks**:
1. Document Bedrock model access request workflow
2. Create Bedrock Agent setup instructions
3. Document MCP server integration via AgentCore
4. Capture all required screenshots (approximately 15-20)
5. Test complete agent workflow end-to-end

**Validation**: Successfully create and test Bedrock agent with Neo4j MCP tools.

---

### Phase 4: Lab 4 - Development Environment

**Objective**: Update development environment for AWS tooling.

**Tasks**:
1. Finalize devcontainer.json configuration
2. Complete CDK deployment documentation
3. Test Codespaces launch and AWS CLI functionality
4. Verify environment variable synchronization
5. Document local machine setup alternative

**Validation**: Launch Codespace, deploy CDK, and verify all environment variables.

---

### Phase 5: Labs 5-6 - Knowledge Graph and Retrievers

**Objective**: Update notebooks for Bedrock embeddings and LLM.

**Tasks**:
1. Update Lab 5 notebooks to use BedrockEmbedder
2. Update embedding dimension references throughout
3. Update Lab 6 notebooks to use Bedrock LLM
4. Test all four Lab 5 notebooks end-to-end
5. Test all three Lab 6 notebooks end-to-end

**Validation**: Successfully build knowledge graph and execute all retriever patterns.

---

### Phase 6: Lab 7 - Strands Agents

**Objective**: Complete rewrite of agent notebooks using Strands SDK.

**Tasks**:
1. Implement Notebook 01 with Strands simple agent
2. Implement Notebook 02 with multi-tool agent
3. Implement Notebook 03 with Text2Cypher agent
4. Document key differences from Azure implementation
5. Create optional LangChain tool integration examples

**Validation**: Successfully run all three agent notebooks with expected behavior.

---

### Phase 7: Lab 8 and Polish

**Objective**: Complete optional lab and final testing.

**Tasks**:
1. Update Lab 8 notebooks for Bedrock embedder
2. Update all presentation slides
3. Complete end-to-end workshop testing
4. Create troubleshooting guide
5. Document common issues and solutions

**Validation**: Complete full workshop flow from Lab 0 through Lab 8.

---

## Part 6: Testing and Validation Plan

### Unit Testing

- Verify BedrockEmbedder produces valid 1024-dimension vectors
- Verify BedrockLLM returns expected response format
- Verify Strands agent tool registration works correctly

### Integration Testing

- Complete Lab 1 through AWS Marketplace with new account
- Verify knowledge graph builds correctly with Bedrock embeddings
- Verify all retriever types return expected results
- Verify all agent types demonstrate correct tool selection

### End-to-End Testing

- Run complete workshop flow (Labs 0-8) with fresh AWS account
- Document actual time required for each lab
- Identify and resolve any blocking issues
- Verify all screenshots match current AWS/Bedrock interface

---

## Part 7: Documentation Checklist

### Root Level Files
- [ ] README.md - Update for AWS context
- [ ] .env.sample - AWS variables
- [ ] pyproject.toml - AWS dependencies
- [ ] setup_env.py - AWS CDK integration
- [ ] GUIDE_DEV_CONTAINERS.md - AWS setup instructions

### Lab Documentation
- [ ] Lab_0_Sign_In/README.md
- [ ] Lab_1_Aura_Setup/README.md
- [ ] Lab_1_Aura_Setup/Neo4j_Aura_Signup.md
- [ ] Lab_2_Aura_Agents/README.md (minimal changes)
- [ ] Lab_3_Foundry_Agents → Lab_3_Bedrock_Agents/README.md (full rewrite)
- [ ] Lab_4_Start_Codespace/README.md
- [ ] Lab_5_Knowledge_Graph/README.md
- [ ] Lab_6_Retrievers/README.md
- [ ] Lab_7_Agents/README.md (full rewrite)
- [ ] Lab_8_Hybrid_Search/README.md

### Code Files
- [ ] config.py - AWS authentication and model clients
- [ ] All Lab 5 notebooks (4 files)
- [ ] All Lab 6 notebooks (3 files)
- [ ] All Lab 7 notebooks (3 files - full rewrite)
- [ ] All Lab 8 notebooks (2 files)

### Infrastructure
- [ ] /infra/cdk/app.py
- [ ] /infra/cdk/stacks/bedrock_stack.py
- [ ] /infra/cdk/stacks/monitoring_stack.py
- [ ] .devcontainer/devcontainer.json

### Presentation Slides
- [ ] Lab 3 Bedrock slides (new)
- [ ] Lab 7 Strands Agents slides (new)
- [ ] Lab 2 MCP slides (minor updates)

---

## Notes and Considerations

### Cost Optimization
- Recommend Claude Haiku for workshop exercises (lower cost than Sonnet)
- Amazon Titan Embeddings V2 is more cost-effective than ada-002
- Consider pre-provisioning shared account for instructor-led workshops

### Regional Considerations
- Recommend us-east-1 for widest Bedrock model availability
- Document any region-specific model restrictions
- Note that Neo4j Aura region selection is independent of Bedrock region

### Backward Compatibility
- Maintain same knowledge graph structure for data portability
- Same backup file works across Azure and AWS versions
- Consider documenting migration path for existing Azure workshop users

### Future Enhancements
- Document AgentCore deployment option for production workloads
- Consider adding Bedrock Knowledge Bases comparison (uses Neptune Analytics)
- Explore Bedrock Guardrails integration for content safety
