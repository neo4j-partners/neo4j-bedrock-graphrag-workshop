# Lab 8 - GraphRAG Agents with Strands SDK

In this lab, you will build AI agents using the [Strands Agents SDK](https://strandsagents.com) with Amazon Bedrock and Neo4j.

## Prerequisites

Before starting, make sure you have:
- Completed **Lab 5** (Codespace setup with AWS credentials configured)
- Completed **Lab 6** (Knowledge Graph with full dataset loaded)
- Completed **Lab 7** (Understanding of retriever patterns)
- Your `.env` file configured with Neo4j and AWS credentials

## What You'll Learn

1. **Simple Agent** - Create an agent with a schema exploration tool
2. **Vector Graph Agent** - Combine vector search with graph traversal
3. **Multi-Tool Agent** - Build an agent that selects between different retrieval strategies

## Notebooks

| Notebook | Description |
|----------|-------------|
| [01_simple_agent.ipynb](01_simple_agent.ipynb) | Agent with schema tool using Strands SDK |
| [02_vector_graph_agent.ipynb](02_vector_graph_agent.ipynb) | Agent with vector + graph context |
| [03_text2cypher_agent.ipynb](03_text2cypher_agent.ipynb) | Multi-tool agent with Text2Cypher |

## Strands Agents SDK Overview

Strands Agents is an open-source SDK from AWS that simplifies building AI agents. It follows a model-driven approach where the LLM decides which tools to use based on the user's query.

### Key Concepts

**Tools with @tool decorator:**
```python
from strands import Agent, tool

@tool
def get_graph_schema() -> str:
    """Get the schema of the graph database."""
    return schema_string
```

**Agent creation with Bedrock:**
```python
from strands import Agent
from strands.models import BedrockModel

model = BedrockModel(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    temperature=0.3
)

agent = Agent(
    model=model,
    system_prompt="You are a helpful assistant...",
    tools=[get_graph_schema]
)
```

**Running the agent:**
```python
response = agent("What is the database schema?")
print(response)
```

### Tool Definition Best Practices

| Practice | Description |
|----------|-------------|
| **Clear docstrings** | The agent uses docstrings to decide when to use a tool |
| **Type hints** | Include parameter and return type hints |
| **Error handling** | Return helpful error messages on failure |
| **Focused scope** | Each tool should do one thing well |

### When to Use Each Tool

| Tool Type | Best For | Example Questions |
|-----------|----------|-------------------|
| **Schema** | Understanding the graph structure | "What types of data are in the database?" |
| **Vector Search** | Semantic similarity queries | "What risks does Apple face?" |
| **Text2Cypher** | Specific facts and aggregations | "How many companies are owned by BlackRock?" |

## Installing Strands SDK

The workshop Codespace includes Strands. To install manually:

```bash
pip install strands-agents strands-agents-tools
```

## Best Practices

### Agent System Prompts
- Be specific about the agent's role and capabilities
- List available tools and when to use each
- Provide guidance on how to handle ambiguous queries

### Tool Selection
- The agent automatically selects tools based on the query
- Good docstrings are critical for accurate tool selection
- Consider providing examples in the system prompt

### Error Handling
- Tools should return helpful error messages
- The agent will retry or explain the error to the user
- Use try/except blocks in tool implementations

## Common Issues

| Problem | Solution |
|---------|----------|
| Agent doesn't use tools | Check tool docstrings are clear and descriptive |
| Wrong tool selected | Improve docstring specificity or add examples |
| Bedrock access denied | Verify AWS credentials and model access |
| Tool errors | Check Neo4j connection and query syntax |

## References

- [Strands Agents Documentation](https://strandsagents.com/latest/documentation/docs/user-guide/quickstart/)
- [Amazon Bedrock Integration](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/amazon-bedrock/)
- [Strands GitHub](https://github.com/strands-agents/sdk-python)
- [AWS Blog: Introducing Strands Agents](https://aws.amazon.com/blogs/opensource/introducing-strands-agents-an-open-source-ai-agents-sdk/)

## Next Steps

After completing this lab:
- Continue to [Lab 9 - Hybrid Search](../Lab_9_Hybrid_Search/) for advanced search patterns
- Explore deploying agents with Amazon Bedrock AgentCore
- Build custom tools for your specific use cases
