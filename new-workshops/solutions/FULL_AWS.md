# AWS Bedrock Migration Guide for Workshop Solutions

This document outlines the changes required to migrate all remaining solution files from their current implementations (Azure/OpenAI) to AWS Bedrock. The 01* files have already been updated to use AWS Bedrock as the reference implementation.

---

## Current State Summary

### Already Using AWS Bedrock (No Changes Needed)

| File | Status | Notes |
|------|--------|-------|
| `config.py` | Complete | Provides `get_embedder()` returning BedrockEmbeddings and `get_llm()` returning BedrockLLM |
| `01_01_data_loading.py` | Complete | Pure Neo4j operations, no AI components |
| `01_02_embeddings.py` | Complete | Uses `get_embedder()` from config |
| `01_03_entity_extraction.py` | Complete | Uses `get_llm()` and `get_embedder()` from config |
| `01_04_full_dataset_queries.py` | Complete | Pure Neo4j operations |
| `01_full_data_load.py` | Complete | Uses config-based components |
| `02_01_vector_retriever.py` | Complete | Already uses `get_embedder()` and `get_llm()` from config |
| `02_03_text2cypher_retriever.py` | Complete | Already uses `get_llm()` from config |
| `05_01_fulltext_search.py` | Complete | Pure Neo4j fulltext operations, no AI components |

### Requires Changes

| File | Effort | Primary Issue |
|------|--------|---------------|
| `02_02_vector_cypher_retriever.py` | Low | Has leftover OpenAI imports and type hints |
| `05_02_hybrid_search.py` | Low | Minor attribute name fix for embedder |
| `03_01_simple_agent.py` | High | Uses Microsoft Azure Agent Framework |
| `03_02_vector_graph_agent.py` | High | Uses Microsoft Azure Agent Framework |
| `03_03_text2cypher_agent.py` | High | Uses Microsoft Azure Agent Framework and OpenAI LLM |

---

## Detailed Change Requirements

### 02_02_vector_cypher_retriever.py

**Issue:** Contains leftover OpenAI imports and type hints that should reference AWS Bedrock types instead.

**What Needs to Change:**
- Remove the unused import for OpenAIEmbeddings from neo4j_graphrag.embeddings
- Remove the unused import for OpenAILLM from neo4j_graphrag.llm
- Update the type hint in the create_vector_cypher_retriever function parameter from OpenAIEmbeddings to the generic Embedder type or simply remove the type hint
- Update the type hint in the demo_retriever function parameter from OpenAILLM to the generic LLMInterface type or simply remove the type hint

**Functional Impact:** None. The code already calls get_embedder() and get_llm() from config which return Bedrock components. This is purely a cleanup of misleading imports and type annotations.

---

### 05_02_hybrid_search.py

**Issue:** Accesses an attribute on the embedder that may not exist on BedrockEmbeddings.

**What Needs to Change:**
- The print statement that displays the embedder model name references embedder.model which is the OpenAI attribute naming convention
- For BedrockEmbeddings, the attribute is called model_id instead of model
- Update the display line to use model_id to match the Bedrock embedder

**Functional Impact:** Very minor. This only affects a diagnostic print statement. The actual hybrid search functionality works correctly.

---

### 03_01_simple_agent.py

**Issue:** Built entirely on Microsoft Azure Agent Framework using Azure Foundry as the AI backend.

**What Needs to Change:**

The entire agent infrastructure needs replacement:

1. **Remove Azure Dependencies**
   - Remove the import for AzureAIClient from agent_framework.azure
   - Remove the import for AzureCliCredential from azure.identity.aio
   - Remove the call to get_agent_config() which returns Azure-specific configuration

2. **Add AWS Agent Infrastructure**
   - Choose an AWS-native agent framework such as AWS Strands Agents, Amazon Bedrock Agents, or LangChain with Bedrock
   - Import the chosen framework components
   - Configure authentication using AWS credentials via boto3 default credential chain

3. **Rewrite Agent Creation**
   - Replace AzureAIClient initialization with the AWS agent client
   - Replace the async context manager pattern for Azure with the equivalent AWS pattern
   - Update the create_agent call to use AWS-compatible parameters

4. **Rewrite Agent Execution**
   - Replace the run_stream method with the AWS equivalent streaming approach
   - Update the response handling to match AWS agent response format

5. **Update Config**
   - Add any necessary AWS agent configuration to config.py if needed such as Bedrock Agent IDs or Lambda function ARNs if using Bedrock Agents

**Functional Impact:** High. The agent behavior should remain the same (schema retrieval tool) but the underlying infrastructure changes completely.

---

### 03_02_vector_graph_agent.py

**Issue:** Built on Microsoft Azure Agent Framework with vector retrieval tools.

**What Needs to Change:**

Similar to 03_01 with additional considerations:

1. **Remove Azure Dependencies**
   - Same as 03_01: remove AzureAIClient, AzureCliCredential, and get_agent_config imports

2. **Add AWS Agent Infrastructure**
   - Same framework choice as 03_01 for consistency across agent demos

3. **Preserve Neo4j Integration**
   - The VectorCypherRetriever usage stays exactly the same
   - The get_embedder() call already returns BedrockEmbeddings
   - The get_graph_schema tool function stays the same
   - The retrieve_financial_documents tool function stays the same

4. **Rewrite Agent Wrapper**
   - Only the outer agent orchestration layer changes
   - The tools themselves remain Neo4j and Bedrock based

5. **Update Agent Instructions**
   - May need minor adjustments to system prompt based on AWS agent prompt format requirements

**Functional Impact:** High for infrastructure, but the core retrieval logic using Neo4j GraphRAG remains unchanged.

---

### 03_03_text2cypher_agent.py

**Issue:** Most complex file combining Azure Agent Framework with OpenAI LLM for Cypher generation.

**What Needs to Change:**

1. **Remove Azure Dependencies**
   - Remove AzureAIClient import
   - Remove both AzureCliCredential and DefaultAzureCredential imports
   - Remove get_agent_config import and usage

2. **Remove OpenAI LLM for Cypher Generation**
   - Remove the import for OpenAILLM from neo4j_graphrag.llm
   - Remove the DefaultAzureCredential token acquisition code
   - Remove the OpenAILLM instantiation that uses Azure Foundry endpoint

3. **Add Bedrock LLM for Cypher Generation**
   - Import BedrockLLM from neo4j_graphrag.llm (already available via get_llm)
   - Use get_llm() from config to get a BedrockLLM instance for the Text2CypherRetriever
   - This ensures consistent LLM usage across all components

4. **Add AWS Agent Infrastructure**
   - Same framework choice as 03_01 and 03_02

5. **Preserve Tool Functions**
   - The get_graph_schema tool stays the same
   - The retrieve_financial_documents tool stays the same (already uses Bedrock via get_embedder)
   - The query_database tool stays the same once the Text2CypherRetriever uses BedrockLLM

**Functional Impact:** High for infrastructure. The Text2Cypher functionality needs verification that BedrockLLM produces quality Cypher queries comparable to the Azure/OpenAI version.

---

## Configuration Changes Required

The current config.py already provides the necessary AWS Bedrock components. If implementing AWS Strands Agents or Bedrock Agents, additional configuration may be needed:

**Potential Additions to config.py:**

1. **For AWS Strands Agents**
   - No additional configuration needed beyond existing BedrockLLM
   - Strands can use the existing get_llm() function directly

2. **For Amazon Bedrock Agents**
   - Agent ID configuration
   - Agent Alias ID configuration
   - Optional Knowledge Base ID if using Bedrock Knowledge Bases
   - Lambda function ARN if using action groups

---

## Agent Framework Options

When replacing the Microsoft Azure Agent Framework, consider these AWS-native options:

### Option A: AWS Strands Agents (Recommended)

- Lightweight Python framework for building agents
- Direct integration with Bedrock models
- Tool registration similar to current pattern
- Streaming support
- Best fit for current code structure

### Option B: Amazon Bedrock Agents (Managed Service)

- Fully managed agent service
- Requires AWS console setup or CloudFormation
- Uses Lambda functions for tool execution
- More operational overhead but fully managed
- Better for production deployments

### Option C: LangChain with Bedrock

- Popular framework with Bedrock integration
- Different programming model from current code
- Larger dependency footprint
- Well documented

---

## Implementation Plan

### Phase 1: Low-Effort Cleanup

**Objective:** Clean up files that functionally already work with AWS Bedrock but have misleading code.

**Files:**
- 02_02_vector_cypher_retriever.py
- 05_02_hybrid_search.py

**Steps:**

1. **Step 1.1:** Update 02_02_vector_cypher_retriever.py imports
   - Remove OpenAIEmbeddings import
   - Remove OpenAILLM import
   - Update or remove type hints referencing OpenAI types

2. **Step 1.2:** Update 05_02_hybrid_search.py embedder attribute
   - Change embedder.model to embedder.model_id in the print statement

3. **Step 1.3:** Verification
   - Run each updated file to confirm no import errors
   - Verify the demos produce expected output

**Success Criteria:**
- No OpenAI or Azure imports remain in these files
- All demos run successfully with Bedrock

---

### Phase 2: Agent Framework Selection

**Objective:** Choose and validate the AWS agent framework for the 03* files.

**Steps:**

1. **Step 2.1:** Evaluate AWS Strands Agents
   - Review Strands documentation and examples
   - Create a minimal proof-of-concept agent with one tool
   - Verify streaming output works
   - Confirm tool calling functions correctly

2. **Step 2.2:** Evaluate alternative if needed
   - If Strands does not meet requirements, evaluate Bedrock Agents or LangChain
   - Document the decision rationale

3. **Step 2.3:** Create agent utility functions
   - Add helper functions to config.py for agent creation if needed
   - Ensure consistent patterns across all agent files

**Success Criteria:**
- Working proof-of-concept agent using chosen framework
- Clear documentation of framework choice rationale
- Reusable patterns identified for all three agent files

---

### Phase 3: Simple Agent Migration

**Objective:** Migrate 03_01_simple_agent.py to AWS.

**Files:**
- 03_01_simple_agent.py

**Steps:**

1. **Step 3.1:** Remove Azure dependencies
   - Delete Azure imports
   - Delete get_agent_config usage

2. **Step 3.2:** Add AWS agent infrastructure
   - Import chosen framework components
   - Set up AWS authentication pattern

3. **Step 3.3:** Rewrite run_agent function
   - Create agent with chosen framework
   - Register get_graph_schema tool
   - Implement streaming output

4. **Step 3.4:** Testing
   - Run the schema summarization query
   - Verify tool is called correctly
   - Verify response quality matches Azure version

**Success Criteria:**
- Agent correctly calls schema tool when asked about database structure
- Streaming output displays progressively
- Response accurately describes the graph schema

---

### Phase 4: Vector Graph Agent Migration

**Objective:** Migrate 03_02_vector_graph_agent.py to AWS.

**Files:**
- 03_02_vector_graph_agent.py

**Steps:**

1. **Step 4.1:** Remove Azure dependencies
   - Same pattern as Phase 3

2. **Step 4.2:** Preserve retrieval infrastructure
   - Verify VectorCypherRetriever continues using Bedrock embedder
   - Keep all tool function implementations unchanged

3. **Step 4.3:** Add AWS agent wrapper
   - Use same pattern established in Phase 3
   - Register both get_graph_schema and retrieve_financial_documents tools

4. **Step 4.4:** Testing
   - Run queries about Apple risk factors
   - Verify vector search returns relevant chunks
   - Verify graph traversal enriches results with company and risk data
   - Verify agent synthesizes coherent answers

**Success Criteria:**
- Both tools registered and callable by agent
- Vector search returns relevant financial document chunks
- Agent correctly answers questions about company risks and products

---

### Phase 5: Text2Cypher Agent Migration

**Objective:** Migrate 03_03_text2cypher_agent.py to AWS.

**Files:**
- 03_03_text2cypher_agent.py

**Steps:**

1. **Step 5.1:** Remove Azure and OpenAI dependencies
   - Delete all Azure credential imports
   - Delete OpenAILLM import and instantiation

2. **Step 5.2:** Update Cypher LLM to Bedrock
   - Use get_llm() to get BedrockLLM for Text2CypherRetriever
   - Verify the custom Cypher prompt works with Claude models

3. **Step 5.3:** Test Cypher generation quality
   - Run several Text2Cypher queries in isolation
   - Verify generated Cypher follows modern Neo4j 5+ syntax
   - Check for correct entity name handling
   - Ensure LIMIT clauses are present

4. **Step 5.4:** Add AWS agent wrapper
   - Same pattern as Phases 3 and 4
   - Register all three tools: schema, vector search, and database query

5. **Step 5.5:** Full agent testing
   - Run queries requiring each tool type
   - Verify agent selects appropriate tool for each question type
   - Test multi-turn conversations

**Success Criteria:**
- BedrockLLM generates valid Cypher queries
- All three tools function correctly within agent
- Agent demonstrates appropriate tool selection logic

---

### Phase 6: Final Validation

**Objective:** Comprehensive testing and documentation update.

**Steps:**

1. **Step 6.1:** Run all solution files
   - Execute each 02*, 03*, and 05* file
   - Capture output for documentation
   - Note any errors or warnings

2. **Step 6.2:** Update file docstrings
   - Change references from Azure/OpenAI to AWS Bedrock
   - Update model names in comments
   - Ensure run instructions remain accurate

3. **Step 6.3:** Update README if present
   - Document AWS Bedrock requirement
   - List required AWS permissions
   - Update environment variable documentation

4. **Step 6.4:** Clean up config.py
   - Remove any Azure-related configuration if present
   - Ensure only AWS configuration remains
   - Verify all helper functions are used

**Success Criteria:**
- All solution files run without errors
- Documentation accurately reflects AWS Bedrock usage
- No Azure or OpenAI references remain in codebase

---

## Risk Considerations

### Cypher Generation Quality

The Text2CypherRetriever relies heavily on LLM quality for generating valid Cypher. Claude models may produce different Cypher patterns than GPT models. Testing should verify:
- Correct syntax for Neo4j 5+
- Proper handling of NULL values in ORDER BY
- Appropriate use of LIMIT clauses
- Correct relationship direction in MATCH patterns

### Agent Tool Calling

Different agent frameworks have different tool calling patterns. Verify:
- Tool descriptions are parsed correctly
- Parameter types are inferred properly
- Return values are handled as expected

### Streaming Behavior

The current demos use streaming output. Ensure the chosen AWS agent framework supports streaming with similar user experience.

---

## Environment Variables

After migration, the following environment variables will be required:

```
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# AWS Bedrock
AWS_REGION=us-east-1
AWS_BEDROCK_INFERENCE_PROFILE_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
AWS_BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0

# AWS Credentials (via standard AWS credential chain)
# AWS_ACCESS_KEY_ID (optional if using IAM roles)
# AWS_SECRET_ACCESS_KEY (optional if using IAM roles)
```

---

## Summary

The migration involves three categories of work:

1. **Trivial changes** (Phase 1): Remove misleading imports and fix attribute names in two files
2. **Framework replacement** (Phases 2-5): Replace Microsoft Azure Agent Framework with AWS-native agent solution for three files
3. **Validation** (Phase 6): Comprehensive testing and documentation updates

The most significant effort is in the agent files (03*) which require selecting and implementing an AWS-native agent framework. The core Neo4j GraphRAG functionality using retrievers, embeddings, and LLMs is already compatible with AWS Bedrock through the existing config.py implementation.
