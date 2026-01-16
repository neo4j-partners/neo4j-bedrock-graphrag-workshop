# Lab 3 - Amazon Bedrock Setup

In this lab, you will set up Amazon Bedrock and enable access to the foundation models needed for the remaining labs. Amazon Bedrock is AWS's fully managed service for accessing foundation models from leading AI companies.

## Prerequisites

Before starting, make sure you have:
- Completed **Lab 0** (AWS sign-in)
- Completed **Lab 1** (Neo4j Aura setup with backup restored)
- Completed **Lab 2** (Aura Agents - to understand the agent patterns)

## What is Amazon Bedrock?

Amazon Bedrock provides:

- **Foundation Models** - Access to Claude (Anthropic), Titan (Amazon), Llama (Meta), and more
- **Playground** - Test models with prompts before building applications
- **Bedrock Agents** - Build AI agents that can use external tools
- **Knowledge Bases** - Connect agents to your data sources for RAG
- **Guardrails** - Content filtering and safety controls

In this lab, you'll:
- Navigate to Amazon Bedrock in the AWS Console
- Enable access to Claude and Titan models
- Test the models in the Bedrock Playground
- Understand the models you'll use in later labs

---

## Part 1: Enable Bedrock Model Access

Before using any foundation models, you must request access in the Bedrock console.

### Step 1: Navigate to Amazon Bedrock

1. Sign in to the [AWS Console](https://console.aws.amazon.com)
2. In the search bar, type **Bedrock** and select **Amazon Bedrock**

![Find Bedrock](images/find_bedrock.png)

3. You should see the Amazon Bedrock welcome page

![Bedrock Console](images/bedrock_console.png)

### Step 2: Access Model Access Settings

1. In the left sidebar, click **Model access** under the "Bedrock configurations" section

![Model Access Menu](images/model_access_menu.png)

2. You'll see a list of available foundation models and their access status

![Model Access List](images/model_access_list.png)

### Step 3: Request Model Access

1. Click the **Manage model access** button (or **Modify model access**)

![Manage Model Access](images/manage_model_access.png)

2. Enable the following models by checking their boxes:

| Model | Provider | Purpose |
|-------|----------|---------|
| **Claude 3.5 Sonnet v2** | Anthropic | Agent reasoning and responses |
| **Claude 3 Haiku** | Anthropic | Cost-effective alternative |
| **Titan Text Embeddings V2** | Amazon | Vector embeddings (for Labs 6-7) |

![Select Models](images/select_models.png)

3. Click **Request model access** (or **Save changes**)

### Step 4: Wait for Approval

- **Amazon Titan** models are typically approved instantly
- **Anthropic Claude** models may take 1-5 minutes
- Refresh the page to check status

![Access Granted](images/access_granted.png)

Once you see **Access granted** for Claude and Titan, you can proceed.

> **Note:** If access is not granted after 10 minutes, check that you agreed to any required terms and that your account doesn't have restrictions.

---

## Part 2: Explore the Bedrock Playground

The Bedrock Playground lets you test models before building applications.

### Step 5: Navigate to the Playground

1. In the left sidebar, click **Playgrounds** under "Getting started"
2. Select **Chat playground**

![Playground Menu](images/playground_menu.png)

### Step 6: Select a Model

1. In the playground, click **Select model**
2. Choose **Anthropic** as the provider
3. Select **Claude 3.5 Sonnet v2**
4. Click **Apply**

![Select Playground Model](images/select_playground_model.png)

### Step 7: Test the Model

Try asking the model about SEC filings to see how it responds:

**Prompt 1: General knowledge**
```
What information is typically found in an SEC 10-K filing?
```

![Playground Test 1](images/playground_test_1.png)

**Prompt 2: Financial analysis**
```
What are common risk factors that technology companies disclose in their 10-K filings?
```

**Prompt 3: Cypher query (preview for later labs)**
```
Write a Cypher query to find all companies and their risk factors in a Neo4j graph database where companies have a HAS_RISK relationship to RiskFactor nodes.
```

### Step 8: Adjust Model Parameters (Optional)

Click the **Configuration** panel to adjust:

| Parameter | Description | Recommended |
|-----------|-------------|-------------|
| **Temperature** | Randomness (0=focused, 1=creative) | 0.3 for analysis |
| **Top P** | Nucleus sampling threshold | 0.9 |
| **Max tokens** | Maximum response length | 2048 |

![Model Configuration](images/model_configuration.png)

---

## Part 3: Understand the Models

### Models You'll Use in This Workshop

| Model | Use Case | Cost | Labs |
|-------|----------|------|------|
| **Claude 3.5 Sonnet v2** | Agent reasoning, text generation, Cypher queries | ~$3/M input tokens | 4, 8 |
| **Claude 3 Haiku** | Fast, cost-effective responses | ~$0.25/M input tokens | Alternative |
| **Titan Text Embeddings V2** | Vector embeddings (1024 dimensions) | ~$0.02/M tokens | 6-7 |

### Claude vs GPT (Comparison with Azure)

| Feature | Claude (Bedrock) | GPT-4o (Azure) |
|---------|------------------|----------------|
| Provider | Anthropic | OpenAI |
| Strengths | Reasoning, long context, safety | General purpose, vision |
| Context window | 200K tokens | 128K tokens |
| Workshop use | Agent reasoning | Agent reasoning |

Both models work well for this workshop - the patterns are the same regardless of the underlying model.

### Titan Embeddings Best Practices

For the coding labs, you'll use Titan Text Embeddings V2 with these settings:

- **Dimensions**: 1024 (optimized for performance)
- **Normalize**: true (for cosine similarity)
- **Document segmentation**: 512 tokens recommended

---

## Part 4: (Optional) Test Text Embeddings

Preview the embedding model you'll use in Lab 6.

### Step 9: Navigate to Text Playground

1. In the left sidebar, click **Playgrounds**
2. Select **Text playground**

### Step 10: Test Titan Embeddings

1. Select **Amazon** as the provider
2. Choose **Titan Text Embeddings V2**
3. Enter a test phrase:

```
Apple Inc faces risks related to global supply chain disruptions
```

4. Click **Run**

You'll see a vector of 1024 floating-point numbers - this is how text is converted to embeddings for semantic search.

![Embeddings Test](images/embeddings_test.png)

---

## Summary

You have now set up Amazon Bedrock with:
- **Model access** granted for Claude and Titan models
- **Playground experience** testing Claude's capabilities
- **Understanding** of the models you'll use in later labs

## Model Access Checklist

Before proceeding, verify you have access to:

- [ ] Claude 3.5 Sonnet v2 (or Claude 3 Haiku)
- [ ] Titan Text Embeddings V2

## What's Next

Continue to [Lab 4 - AI Agent Builder](../Lab_4_GAAB_Agents/) to create an AI agent that can query your Neo4j knowledge graph using the pre-deployed MCP server.

---

## References

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Claude Model Card](https://docs.anthropic.com/claude/docs/models-overview)
- [Titan Embeddings Best Practices](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)
