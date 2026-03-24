# AWS Site Content Update Plan — IMPLEMENTED

The `site/` Antora documentation was recently updated with conceptual overviews and structured instruction pages for each lab. This document outlined how to bring the AWS GenAI content up to the same standard. The plan has been implemented.

## Scope: Three Services, GenAI Patterns

The site content focuses on the three AWS services participants interact with as GenAI practitioners:

1. **Amazon Bedrock** — Foundation model access (Claude for reasoning, Nova for embeddings), the Converse API, cross-region inference, tool use
2. **Amazon Bedrock AgentCore** — Managed agent deployment runtime, direct code deploy, session isolation, MCP server hosting
3. **Amazon SageMaker Studio** — Notebook development environment (domains, JupyterLab spaces, execution roles)

Infrastructure services (Secrets Manager, Marketplace, IAM) are referenced where relevant but do not get dedicated coverage. Participants click through them; they do not need conceptual understanding of them.

## Content Plan

### 1. New Page: `aws-services.adoc`

**Purpose:** Ground participants in the AWS GenAI stack before they encounter services piecemeal across labs.

**Structure:**

- The three-service stack and how it maps to the GraphRAG architecture
- **Amazon Bedrock** section:
  - Two model families: Claude (reasoning, tool selection, generation) and Nova (embeddings)
  - The Converse API as the unified model invocation interface
  - Tool use: how tool definitions flow to the model and tool_use responses flow back
  - Cross-region inference profiles: geographic vs global, the `us.` model ID prefix, no additional routing cost
  - Model IDs used in the workshop
- **Amazon Bedrock AgentCore** section:
  - What it solves: going from notebook prototype to managed deployment
  - The deployment model: direct_code_deploy packages agent code without Docker
  - Session isolation in microVMs
  - Framework agnostic (LangGraph, Strands, CrewAI)
  - MCP server hosting capability
- **Amazon SageMaker Studio** section:
  - The hierarchy: domain > space > application
  - JupyterLab spaces with EBS storage
  - Why the workshop uses ml.t3.medium (sufficient for API-calling notebooks)

**Nav placement:**
```
* xref:index.adoc[Home]
* xref:aws-services.adoc[AWS GenAI Services]    <-- NEW
* xref:sample-queries.adoc[Sample Queries]
```

### 2. Expand `lab3.adoc` — DONE

The Lab 3 concepts page was expanded with:

- Dedicated Converse API and tool use section explaining the request/response flow
- Two model families (Claude for reasoning, Nova for embeddings) with their distinct roles
- Cross-region inference section with link to aws-services.adoc for the full comparison
- Expanded AgentCore deployment section explaining what happens during `agentcore deploy`
- Cross-references to aws-services.adoc and admin-setup.adoc

### 3. `configuration.adoc` — DONE

Created CONFIG.txt field reference with:

- Full field table (field, description, source, required-by labs)
- Example file
- How notebooks load configuration (python-dotenv and pydantic-settings)
- Model ID notes and security guidance

### 4. `admin-setup.adoc` — DONE

Created pre-workshop admin setup page with:

- Bedrock model access enablement
- AgentCore IAM setup (execution role, S3 bucket, SageMaker permissions)
- CONFIG.txt preparation
- Optional SageMaker lifecycle configuration
- Cleanup instructions

### 5. Lab 8 — SKIPPED

The `Lab_8_Aura_Agents_API/` directory does not exist in the repository (only referenced in root README). No source material to base site pages on.

## Using the AWS Documentation MCP Server

The `awslabs.aws-documentation-mcp-server` provides four tools for researching content while writing pages.

### Workflow

1. **`search_documentation`** — Find relevant pages. Use `product_types` filter for broad queries. Returns URLs, titles, section titles.
2. **`read_sections`** — Extract specific sections by title from a URL. Faster than reading whole pages.
3. **`read_documentation`** — Read full pages. Paginate with `start_index` for long documents.
4. **`recommend`** — Discover related content. The "New" category surfaces recently released features.

### Research Queries Used

| Topic | Search Phrase | Product Filter |
|-------|--------------|----------------|
| Converse API + tool use | `"Amazon Bedrock Converse API tool use"` | Amazon Bedrock |
| Cross-region inference | `"Amazon Bedrock cross-region inference profiles"` | Amazon Bedrock |
| Nova embeddings | `"Amazon Nova multimodal embeddings model"` | Amazon Bedrock |
| AgentCore Runtime | `"Amazon Bedrock AgentCore Runtime deploy agent"` | — |
| SageMaker spaces | `"SageMaker Studio JupyterLab spaces domains"` | Amazon SageMaker AI |

### Key Findings

- **Converse API** is the unified interface; tool definitions go in `toolConfig`, tool results come back as `toolUse` content blocks
- **Cross-region inference** has two types: Geographic (data residency) and Global (max throughput, ~10% savings). The `us.` prefix means US geographic profile. No additional routing cost.
- **Nova Multimodal Embeddings** supports text, image, and video input. Outputs embedding vectors. Invoked via `bedrock-runtime` endpoint (not Converse API).
- **AgentCore Runtime** runs each session in an isolated microVM. Supports LangGraph, Strands, CrewAI. Direct code deploy skips Docker. Supports MCP and A2A protocols.
- **SageMaker spaces** have a 1:1 relationship with app instances. Each gets its own EBS volume. Can be private or shared.
