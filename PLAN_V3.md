# Implementation Plan V3: Neo4j and AWS Bedrock Workshop

This document provides the updated implementation plan with completed work, remaining tasks, AWS best practices references, and guidance for the migration from the Azure workshop.

---

## Workshop Structure

### Lab Overview

| Lab | Title | Type | Status |
|-----|-------|------|--------|
| **Lab 0** | Sign In | No-Code | COMPLETE |
| **Lab 1** | Aura Setup | No-Code | COMPLETE |
| **Lab 2** | Aura Agents | No-Code | COMPLETE |
| **Lab 3** | Bedrock Setup | No-Code | COMPLETE |
| **Lab 4** | GAAB Agents | No-Code | COMPLETE |
| **Lab 5** | Start Codespace | Setup | COMPLETE |
| **Lab 6** | Knowledge Graph | Coding | COMPLETE |
| **Lab 7** | Retrievers | Coding | COMPLETE |
| **Lab 8** | Agents | Coding | COMPLETE |
| **Lab 9** | Hybrid Search | Coding | COMPLETE |

### Part 1: No-Code Track (Labs 0-4)

Workshop participants can complete these labs without writing any code:

- **Lab 0**: AWS Console sign-in and Bedrock access verification
- **Lab 1**: Neo4j Aura setup via AWS Marketplace, restore backup, explore graph
- **Lab 2**: Build a no-code AI agent using Neo4j Aura Agent platform
- **Lab 3**: Amazon Bedrock setup - model access and playground testing
- **Lab 4**: Create an agent with GAAB using pre-deployed Neo4j MCP server

### Part 2: Coding Track (Labs 5-9)

For developers who want to build agents programmatically:

- **Lab 5**: Configure Codespace development environment
- **Lab 6**: Build knowledge graph with embeddings and entity extraction
- **Lab 7**: Implement Vector, VectorCypher, and Text2Cypher retrievers
- **Lab 8**: Build agents using Strands Agents SDK
- **Lab 9**: Combine vector and fulltext search (optional)

---

## Reference Implementation

The AWS workshop is being adapted from the Azure reference implementation located at:

```
/Users/ryanknight/projects/hands-on-lab-neo4j-and-azure
```

This reference contains:
- 8 complete labs with documentation and screenshots
- 12 Jupyter notebooks for coding labs
- GraphAcademy course content and slides
- Infrastructure as Code (Bicep)
- Pre-built backup file with SEC 10-K filings data

---

## AWS Best Practices References

The following AWS documentation and best practices should be followed throughout the implementation:

### Generative AI Application Builder (GAAB) Best Practices

**Source**: [GAAB AWS Solutions](https://aws.amazon.com/solutions/implementations/generative-ai-application-builder-on-aws/)

| Practice | Description |
|----------|-------------|
| **Pre-deployment** | Deploy GAAB CloudFormation stack before workshop for faster participant experience |
| **MCP Server Hosting** | Use AgentCore Runtime method for containerized MCP servers |
| **Authentication** | Configure Amazon Cognito for secure dashboard access |
| **Monitoring** | Enable CloudWatch for agent execution traces and debugging |

### Amazon Bedrock Model Access Best Practices

**Source**: [Amazon Bedrock User Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)

| Practice | Description |
|----------|-------------|
| **Model Access** | Request access to Claude and Titan models before starting labs |
| **Region Selection** | Use us-east-1 for widest model availability |
| **Playground Testing** | Test models in playground before building agents |
| **Cost Management** | Use Claude Haiku for workshops instead of Sonnet when possible |

### Amazon Titan Text Embeddings V2 Best Practices

**Source**: [Titan Embedding Models Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)

| Parameter | Recommendation |
|-----------|----------------|
| **Dimensions** | Use 1024 (default) for best quality, 512 or 256 for cost optimization |
| **Document Segmentation** | Segment documents into paragraphs or logical chunks before embedding |
| **Max Input** | 8,192 tokens / 50,000 characters per request |
| **Normalization** | Enable normalization for cosine similarity searches |
| **Language** | Optimized for English; 100+ languages supported but cross-language queries may be sub-optimal |

**Critical Best Practice**: Do NOT submit entire long documents as single inputs. Segment into logical chunks for optimal retrieval performance.

### Strands Agents SDK Best Practices

**Source**: [Strands Agents GitHub](https://github.com/strands-agents/sdk-python)

| Practice | Description |
|----------|-------------|
| **Tool Decorator** | Use `@tool` decorator with clear docstrings describing tool purpose |
| **Type Hints** | Include parameter and return type hints for all tools |
| **Model Selection** | Default uses Bedrock Claude; can configure other providers |
| **Error Handling** | Tools should handle errors gracefully and return informative messages |
| **Testing** | Test tools individually before combining into agents |

**Strands Agent Pattern**:
```python
from strands import Agent, tool

@tool
def my_tool(param: str) -> str:
    """Clear description of what this tool does."""
    return result

agent = Agent(
    system_prompt="Clear instructions for the agent",
    tools=[my_tool]
)
```

### Security Best Practices

**Source**: AWS Security Best Practices

| Area | Recommendation |
|------|----------------|
| **IAM Policies** | Use least-privilege access for Bedrock operations |
| **Credentials** | Never hardcode credentials; use environment variables or AWS Secrets Manager |
| **Neo4j Connection** | Store connection strings in environment variables, not in code |
| **CloudWatch Logging** | Enable logging for audit and debugging |
| **VPC Endpoints** | Consider private connectivity for production deployments |

### Cost Optimization Best Practices

| Strategy | Implementation |
|----------|----------------|
| **Model Selection** | Use Claude Haiku (~$0.25/M tokens) for workshop exercises instead of Sonnet (~$3/M tokens) |
| **Embedding Dimensions** | Use 512 dimensions if 1024 is not required |
| **Batch Processing** | Use Bedrock batch inference for large-scale embedding generation |
| **Resource Cleanup** | Delete unused agents, log groups, and CDK stacks after workshops |

---

## Progress Summary

### Completed Work

| Component | Status | Files Created |
|-----------|--------|---------------|
| **Foundation Setup** | COMPLETE | `.env.sample`, `pyproject.toml`, `config.py`, `setup_env.py` |
| **CDK Infrastructure** | COMPLETE | `infra/cdk/app.py`, `bedrock_stack.py`, `monitoring_stack.py` |
| **Devcontainer** | COMPLETE | `.devcontainer/devcontainer.json`, scripts |
| **Lab 0 Documentation** | COMPLETE | `Lab_0_Sign_In/README.md` |
| **Lab 1 Documentation** | COMPLETE | `Lab_1_Aura_Setup/README.md`, `Neo4j_Aura_Signup.md`, `EXPLORE.md` |
| **Lab 2 Documentation** | COMPLETE | `Lab_2_Aura_Agents/README.md` |
| **Lab 3 Documentation** | COMPLETE | `Lab_3_Bedrock_Setup/README.md` |
| **Lab 4 Documentation** | COMPLETE | `Lab_4_GAAB_Agents/README.md` |
| **Root Documentation** | COMPLETE | `README.md`, `GUIDE_DEV_CONTAINERS.md` |
| **Lab 5 Documentation** | COMPLETE | `Lab_5_Start_Codespace/README.md` |
| **Lab 6 Notebooks** | COMPLETE | `README.md`, `01_data_loading.ipynb`, `02_embeddings.ipynb`, `03_entity_extraction.ipynb`, `04_full_dataset.ipynb` |
| **Lab 7 Notebooks** | COMPLETE | `README.md`, `01_vector_retriever.ipynb`, `02_vector_cypher_retriever.ipynb`, `03_text2cypher_retriever.ipynb` |
| **Lab 8 Notebooks** | COMPLETE | `README.md`, `01_simple_agent.ipynb`, `02_vector_graph_agent.ipynb`, `03_text2cypher_agent.ipynb` (Strands SDK) |
| **Lab 9 Notebooks** | COMPLETE | `README.md`, `01_fulltext_search.ipynb`, `02_hybrid_search.ipynb` |

### Remaining Work

| Component | Status | Priority | Reference Files to Adapt |
|-----------|--------|----------|-------------------------|
| **Screenshots** | NOT STARTED | Medium | All labs require AWS console screenshots |
| **Backup File** | NOT STARTED | High | Copy `finance_data.backup` from Azure lab |
| **Neo4j MCP Server Deployment** | NOT STARTED | High | Containerized MCP server for GAAB |
| **Slides** | NOT STARTED | Low | GraphAcademy slide decks |
| **Testing** | NOT STARTED | High | End-to-end validation |

---

## Workshop Infrastructure Requirements

### Pre-Workshop Setup (Organizers)

For Lab 4 (GAAB Agents) to work, organizers must pre-deploy:

1. **GAAB Platform**
   - Deploy CloudFormation stack (~10 minutes)
   - Configure admin users with Cognito
   - Note the CloudFront dashboard URL

2. **Neo4j MCP Server**
   - Build Docker image with Neo4j MCP server
   - Push to Amazon ECR
   - Deploy to GAAB using Runtime method
   - Configure with shared Neo4j Aura credentials

3. **Participant Access**
   - Create workshop email accounts or use participant emails
   - Configure Cognito users
   - Prepare credentials handout

### Participant Requirements

- AWS Account access (provided or personal)
- GitHub account (for Codespaces in Part 2)
- Neo4j Aura credentials (from Lab 1)

---

## Detailed Remaining Tasks

### Task 1: Copy Data Assets (Immediate)

Copy the pre-built backup file from the Azure reference lab:

```bash
cp /Users/ryanknight/projects/hands-on-lab-neo4j-and-azure/Lab_1_Aura_Setup/data/finance_data.backup \
   /Users/ryanknight/projects/lab-neo4j-aws/Lab_1_Aura_Setup/data/
```

This file contains:
- SEC 10-K filings from major companies
- Pre-computed embeddings (1536 dimensions - Azure ada-002)
- Vector index `chunkEmbeddings`
- Entity nodes and relationships

**Note**: The backup uses 1536-dimension embeddings. For AWS, you may need to regenerate embeddings with Titan's 1024 dimensions, or create a new index.

### Task 2: Lab 5 - Codespace Documentation

Create `Lab_5_Start_Codespace/README.md` with:

**Content to include**:
1. How to launch GitHub Codespace
2. AWS credential configuration
3. Verifying AWS CLI and CDK installation
4. Optional CDK deployment steps
5. Environment variable configuration
6. Troubleshooting common issues

**Reference**: `/Users/ryanknight/projects/hands-on-lab-neo4j-and-azure/Lab_4_Start_Codespace/README.md`

### Task 3: Lab 6 - Knowledge Graph Notebooks (4 notebooks)

Adapt from reference: `/Users/ryanknight/projects/hands-on-lab-neo4j-and-azure/Lab_5_Knowledge_Graph/`

| Notebook | Changes Required |
|----------|-----------------|
| `01_data_loading.ipynb` | Minimal - mostly Neo4j operations |
| `02_embeddings.ipynb` | Replace Azure embedder with BedrockEmbedder, change dimensions to 1024 |
| `03_entity_extraction.ipynb` | Replace Azure LLM with BedrockLLM |
| `04_full_dataset.ipynb` | Apply embedding and LLM changes |

**Best Practice Implementation**:
- Import `get_embedder()` and `get_llm()` from config module
- Update vector index dimension from 1536 to 1024
- Add documentation about Titan embedding best practices
- Include cost notes for batch processing

### Task 4: Lab 7 - Retriever Notebooks (3 notebooks)

Adapt from reference: `/Users/ryanknight/projects/hands-on-lab-neo4j-and-azure/Lab_6_Retrievers/`

| Notebook | Changes Required |
|----------|-----------------|
| `01_vector_retriever.ipynb` | Replace embedder initialization |
| `02_vector_cypher_retriever.ipynb` | Replace embedder initialization |
| `03_text2cypher_retriever.ipynb` | Replace LLM initialization, note Claude's Cypher generation capabilities |

**Best Practice Implementation**:
- Use `neo4j-graphrag` VectorRetriever with BedrockEmbedder
- Document that Claude excels at code generation including Cypher
- Include examples of prompting best practices for Text2Cypher

### Task 5: Lab 8 - Agent Notebooks (3 notebooks) - FULL REWRITE

This is the most significant adaptation. Replace Microsoft Agent Framework with Strands Agents SDK.

**Reference**: `/Users/ryanknight/projects/hands-on-lab-neo4j-and-azure/Lab_7_Agents/`

| Notebook | Azure Pattern | AWS Pattern |
|----------|---------------|-------------|
| `01_simple_agent.ipynb` | `AzureAIClient` with async | `Agent` with `@tool` decorator |
| `02_vector_graph_agent.ipynb` | Async agent with multiple tools | Sync agent with multiple tools |
| `03_text2cypher_agent.ipynb` | Three-tool async agent | Three-tool sync agent |

**Strands Agents Best Practices to Include**:

1. **Tool Definition**:
```python
from strands import Agent, tool

@tool
def get_graph_schema() -> str:
    """Get the schema of the Neo4j graph database including node labels and relationship types."""
    return get_schema(driver)
```

2. **System Prompt Design**:
```python
agent = Agent(
    system_prompt="""You are a helpful assistant that answers questions about SEC filings.

    Choose the appropriate tool:
    1. get_graph_schema - For questions about data structure
    2. search_content - For semantic questions about topics
    3. query_database - For specific facts, counts, and lookups

    Always explain your reasoning before using a tool.""",
    tools=[get_graph_schema, search_content, query_database]
)
```

3. **Error Handling**:
```python
@tool
def query_database(question: str) -> str:
    """Execute a natural language query against the database."""
    try:
        result = text2cypher_retriever.search(question)
        return result if result else "No results found"
    except Exception as e:
        return f"Query failed: {str(e)}"
```

### Task 6: Lab 9 - Hybrid Search Notebooks (2 notebooks)

Adapt from reference: `/Users/ryanknight/projects/hands-on-lab-neo4j-and-azure/Lab_8_Hybrid_Search/`

| Notebook | Changes Required |
|----------|-----------------|
| `01_fulltext_search.ipynb` | Minimal - pure Neo4j functionality |
| `02_hybrid_search.ipynb` | Replace embedder initialization |

### Task 7: Neo4j MCP Server Deployment

Create deployment artifacts for the Neo4j MCP server:

1. **Dockerfile** for containerized deployment
2. **ECR push script**
3. **GAAB deployment instructions**
4. **Environment variable configuration**

### Task 8: Screenshots

Capture AWS console screenshots for:

| Lab | Screenshots Needed |
|-----|-------------------|
| Lab 0 | AWS Console login, region selector, Bedrock console |
| Lab 1 | AWS Marketplace Neo4j listing, subscription flow |
| Lab 3 | Model access, playground testing |
| Lab 4 | GAAB dashboard, agent creation, MCP connection, testing |
| Lab 5 | Codespaces launch, terminal with AWS CLI |

### Task 9: GraphAcademy Content (Optional)

Adapt slides from: `/Users/ryanknight/projects/hands-on-lab-neo4j-and-azure/graphacademy/slides/`

| Slide Deck | Changes Required |
|------------|-----------------|
| `lab-2-foundry/03-azure-ai-foundry-slides.md` | Replace with `aws-bedrock-slides.md` |
| `lab-7-agents/02-microsoft-agent-framework-slides.md` | Replace with `strands-agents-slides.md` |
| Other slides | Update any Azure references to AWS equivalents |

---

## Implementation Order

### Phase 1: Core Functionality ✅ COMPLETE

1. ~~**Copy backup file** to `Lab_1_Aura_Setup/data/`~~ (Pending)
2. ✅ **Create Lab 5 README** - Codespace documentation
3. ✅ **Create Lab 6 notebooks** - Knowledge graph building (4 notebooks)
4. ✅ **Create Lab 7 notebooks** - GraphRAG retrievers (3 notebooks)
5. **Test Labs 5-7** with actual AWS credentials (Pending)

### Phase 2: Agent Framework ✅ COMPLETE

6. ✅ **Create Lab 8 notebooks** - Full Strands Agents rewrite (3 notebooks)
7. **Test agent functionality** with Neo4j (Pending)
8. ✅ **Document Strands best practices** in lab README

### Phase 3: Workshop Infrastructure (Priority: High)

9. **Deploy GAAB** for workshop use
10. **Deploy Neo4j MCP server** to GAAB
11. **Test Lab 4** end-to-end with MCP integration

### Phase 4: Polish ✅ NOTEBOOKS COMPLETE

12. ✅ **Create Lab 9 notebooks** - Hybrid search (2 notebooks)
13. **Capture screenshots** for all labs (Pending)
14. **End-to-end testing** of complete workshop flow (Pending)

### Phase 5: Optional Enhancements (Priority: Low)

15. **Update GraphAcademy slides**
16. **Create troubleshooting guide**
17. **Add cost estimation documentation**

---

## File Structure Target

```
lab-neo4j-aws/
├── .devcontainer/
│   └── devcontainer.json              [COMPLETE]
├── .env.sample                        [COMPLETE]
├── config.py                          [COMPLETE]
├── pyproject.toml                     [COMPLETE]
├── setup_env.py                       [COMPLETE]
├── README.md                          [NEEDS UPDATE]
├── GUIDE_DEV_CONTAINERS.md            [COMPLETE]
├── infra/
│   └── cdk/
│       ├── app.py                     [COMPLETE]
│       ├── cdk.json                   [COMPLETE]
│       └── stacks/
│           ├── bedrock_stack.py       [COMPLETE]
│           └── monitoring_stack.py    [COMPLETE]
├── scripts/
│   ├── post_create.sh                 [COMPLETE]
│   └── post_start.sh                  [COMPLETE]
├── Lab_0_Sign_In/
│   ├── README.md                      [COMPLETE]
│   └── images/                        [NEEDS SCREENSHOTS]
├── Lab_1_Aura_Setup/
│   ├── README.md                      [COMPLETE]
│   ├── Neo4j_Aura_Signup.md          [COMPLETE]
│   ├── EXPLORE.md                     [COMPLETE]
│   ├── data/
│   │   └── finance_data.backup        [NEEDS COPY]
│   └── images/                        [NEEDS SCREENSHOTS]
├── Lab_2_Aura_Agents/
│   ├── README.md                      [COMPLETE]
│   └── images/                        [NEEDS SCREENSHOTS]
├── Lab_3_Bedrock_Setup/
│   ├── README.md                      [COMPLETE]
│   └── images/                        [NEEDS SCREENSHOTS]
├── Lab_4_GAAB_Agents/
│   ├── README.md                      [COMPLETE]
│   └── images/                        [NEEDS SCREENSHOTS]
├── Lab_5_Start_Codespace/
│   ├── README.md                      [COMPLETE]
│   └── images/                        [NEEDS SCREENSHOTS]
├── Lab_6_Knowledge_Graph/
│   ├── README.md                      [COMPLETE]
│   ├── 01_data_loading.ipynb          [COMPLETE]
│   ├── 02_embeddings.ipynb            [COMPLETE]
│   ├── 03_entity_extraction.ipynb     [COMPLETE]
│   └── 04_full_dataset.ipynb          [COMPLETE]
├── Lab_7_Retrievers/
│   ├── README.md                      [COMPLETE]
│   ├── 01_vector_retriever.ipynb      [COMPLETE]
│   ├── 02_vector_cypher_retriever.ipynb [COMPLETE]
│   └── 03_text2cypher_retriever.ipynb [COMPLETE]
├── Lab_8_Agents/
│   ├── README.md                      [COMPLETE]
│   ├── 01_simple_agent.ipynb          [COMPLETE]
│   ├── 02_vector_graph_agent.ipynb    [COMPLETE]
│   └── 03_text2cypher_agent.ipynb     [COMPLETE]
├── Lab_9_Hybrid_Search/
│   ├── README.md                      [COMPLETE]
│   ├── 01_fulltext_search.ipynb       [COMPLETE]
│   └── 02_hybrid_search.ipynb         [COMPLETE]
└── graphacademy/                      [NOT STARTED - Optional]
    └── slides/
```

---

## Quality Checklist

Before considering each lab complete, verify:

### Documentation Quality
- [ ] Clear step-by-step instructions
- [ ] AWS console navigation paths are accurate
- [ ] Screenshots match current AWS interface
- [ ] Troubleshooting section covers common issues
- [ ] Links to AWS documentation are valid

### Code Quality
- [ ] Follows Strands Agents SDK patterns
- [ ] Uses `@tool` decorator with clear docstrings
- [ ] Includes type hints
- [ ] Handles errors gracefully
- [ ] Uses config.py for credentials (not hardcoded)

### Best Practices Compliance
- [ ] Titan embeddings use recommended dimensions (1024 default)
- [ ] Documents are segmented before embedding
- [ ] Agent tools are grouped logically
- [ ] System prompts are clear and specific
- [ ] Cost-effective model choices documented

### Testing
- [ ] All notebook cells execute without errors
- [ ] Agent tools return expected results
- [ ] Neo4j queries return valid data
- [ ] End-to-end workshop flow works

---

## Documentation References

### AWS Official Documentation
- [Amazon Bedrock User Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [Generative AI Application Builder](https://aws.amazon.com/solutions/implementations/generative-ai-application-builder-on-aws/)
- [Titan Embedding Models](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)

### Strands Agents SDK
- [GitHub Repository](https://github.com/strands-agents/sdk-python)
- [AWS Blog: Introducing Strands Agents](https://aws.amazon.com/blogs/opensource/introducing-strands-agents-an-open-source-ai-agents-sdk/)

### Neo4j Integration
- [Neo4j GraphRAG Package](https://neo4j.com/docs/neo4j-graphrag-python/)
- [Neo4j on AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-xd42uzj2v7dae)
- [Knowledge Graphs and GraphRAG with Neo4j](https://docs.aws.amazon.com/architecture-diagrams/latest/knowledge-graphs-and-graphrag-with-neo4j/)
- [Neo4j MCP Server](https://github.com/neo4j/mcp-neo4j)

---

## Notes

### Embedding Dimension Compatibility

The Azure backup uses 1536-dimension embeddings (ada-002). Options for AWS:

1. **Regenerate embeddings** using Titan (1024 dimensions) - Recommended for production
2. **Create new vector index** with 1024 dimensions alongside existing
3. **Use backup as-is** for demonstration (may have compatibility issues)

### Model Selection for Workshops

| Use Case | Recommended Model | Cost |
|----------|-------------------|------|
| Agent reasoning | Claude 3 Haiku | ~$0.25/M tokens |
| Complex queries | Claude 3.5 Sonnet | ~$3/M tokens |
| Embeddings | Titan V2 (1024d) | ~$0.02/M tokens |

### Regional Availability

Recommended region: **us-east-1** (N. Virginia)
- Widest Bedrock model availability
- All Claude versions available
- Titan embeddings available

### GAAB vs Direct Bedrock Agents

| Feature | GAAB | Bedrock Agents Console |
|---------|------|------------------------|
| MCP Support | Yes (via AgentCore) | No (Lambda only) |
| No-Code UI | Yes (after deployment) | Yes |
| Pre-requisites | CloudFormation deploy | None |
| Best for | MCP integration | Simple Lambda tools |
