# Embedding Provider Plan

Make the embedding system modular so it can support OpenAI, Azure, and Bedrock Nova.

---

## What we had before Phase 1

- Two config files that did the same thing: `src/config.py` and `solution_srcs/config.py`
- Both hardcoded `OpenAIEmbeddings` from neo4j-graphrag as the only embedder
- Azure worked because Azure AI Foundry exposes an OpenAI-compatible endpoint (same class, different base_url)
- The vector index dimension was hardcoded to 1536 in `schema.py:103`
- The solution demo `01_02_embeddings.py` also hardcoded 1536 dimensions
- Env vars were OpenAI/Azure-specific: `AZURE_AI_EMBEDDING_NAME`, `OPENAI_API_KEY`, `AZURE_AI_PROJECT_ENDPOINT`
- No provider abstraction — `get_embedder()` just returned `OpenAIEmbeddings` directly

## What needs to change

We need a single `get_embedder()` that picks the right provider based on which env vars are set, and returns a consistent interface that the rest of the code doesn't need to know about. Each provider has different auth, different SDKs, and different output dimensions.

| Provider | SDK | Auth | Model example | Dimensions |
|----------|-----|------|---------------|------------|
| OpenAI | openai (via neo4j-graphrag) | API key | text-embedding-3-small | 1536 |
| Azure | openai (via neo4j-graphrag) | az login token | text-embedding-3-small | 1536 |
| Bedrock Nova | boto3 | AWS credentials | amazon.nova-embed-v1:0 | 1024 |

---

## Phase 1 — Clean up and make embeddings modular [DONE]

The goal was to get the existing code ready so adding a new provider is just adding one new file and one new env var block. No behavior changes — OpenAI and Azure work exactly as they did before.

### What was done

1. **[DONE] Added `EMBEDDING_PROVIDER` (required) and `EMBEDDING_DIMENSIONS` env vars to `.env.sample`**
   - `EMBEDDING_PROVIDER` is required — no auto-detection. Values: `openai`, `azure`, `bedrock`
   - Existing `.env` files must be updated to include `EMBEDDING_PROVIDER=azure` (or `openai`)
   - Added placeholder for Bedrock env vars (`AWS_REGION`, `EMBEDDING_MODEL_ID`)

2. **[DONE] Created `src/embeddings/` package**
   - `src/embeddings/__init__.py` — exports `get_embedder()` and `get_embedding_dimensions()`; validates `EMBEDDING_PROVIDER` is set
   - `src/embeddings/openai.py` — OpenAI embedder using `OPENAI_API_KEY`
   - `src/embeddings/azure.py` — Azure embedder with `get_azure_token()` (moved from `src/config.py`)
   - `src/embeddings/bedrock.py` — stub that raises `NotImplementedError` (Phase 2)

3. **[DONE] Updated `src/config.py`**
   - `embedding_provider` is a required `str` field on `AgentConfig` (not optional)
   - Added optional `embedding_dimensions` field
   - `get_embedder()` now delegates to `src.embeddings`
   - `get_azure_token()` now delegates to `src.embeddings.azure`
   - `get_llm()` and `connect()` unchanged

4. **[DONE] Updated `src/schema.py`**
   - `create_embedding_indexes()` now reads dimensions from config via `get_embedding_dimensions()` instead of defaulting to 1536
   - Still accepts an explicit `dimensions` parameter for callers that need to override

5. **[DONE] Updated `solution_srcs/config.py`**
   - Removed duplicate `AgentConfig` class — now re-exports from `src.config`
   - `get_embedder()` delegates to `src.embeddings`
   - `_get_azure_token()` delegates to `src.embeddings.azure`
   - `get_llm()`, `get_neo4j_driver()`, `get_agent_config()` kept for solution file compatibility

6. **[DONE] Updated `solution_srcs/01_02_embeddings.py`**
   - `create_index()` now reads dimensions from `src.embeddings.get_embedding_dimensions()` instead of hardcoding 1536

7. **[DONE] Updated `src/pipeline.py`**
   - Print output now shows the resolved provider name instead of assuming Azure

8. **[DONE] Updated `.env` to add `EMBEDDING_PROVIDER=azure`**

### Files changed

| File | Change |
|------|--------|
| `.env.sample` | Added `EMBEDDING_PROVIDER`, `EMBEDDING_DIMENSIONS`, Bedrock placeholders |
| `src/embeddings/__init__.py` | New — provider router, `get_embedder()`, `get_embedding_dimensions()` |
| `src/embeddings/openai.py` | New — OpenAI `create_embedder()` |
| `src/embeddings/azure.py` | New — Azure `create_embedder()` + `get_azure_token()` |
| `src/embeddings/bedrock.py` | New — stub for Phase 2 |
| `src/config.py` | Added `embedding_provider`/`embedding_dimensions` fields; `get_embedder()` delegates to embeddings pkg |
| `src/schema.py` | `create_embedding_indexes()` reads dimensions from config |
| `src/pipeline.py` | Provider-aware print output |
| `solution_srcs/config.py` | Removed duplicated `AgentConfig` and embedder logic; delegates to `src` |
| `solution_srcs/01_02_embeddings.py` | Config-driven dimensions |

---

## Phase 2 — Add Bedrock Nova with boto3

Once Phase 1 is done, this is just adding one new provider file and the env vars.

### TODO

1. **Implement `src/embeddings/bedrock.py`**
   - Use boto3 `bedrock-runtime` client directly
   - Call `invoke_model` with the Nova embedding model
   - Handle auth via standard AWS credential chain (env vars, profile, IAM role)
   - Return embeddings in the same format neo4j-graphrag expects

2. **Add Bedrock env vars to `.env.sample`**
   - `AWS_REGION` (or reuse `REGION` from the project root CONFIG.txt)
   - `EMBEDDING_MODEL_ID` (e.g., `amazon.nova-embed-v1:0`)
   - `EMBEDDING_PROVIDER=bedrock`

3. **Wire up the provider in `src/embeddings/__init__.py`**
   - When `EMBEDDING_PROVIDER=bedrock`, call `bedrock.create_embedder()`
   - (Already wired — just needs the implementation in bedrock.py)

4. **Handle the dimension difference**
   - Nova embeddings are 1024 dimensions (not 1536)
   - The config already carries `EMBEDDING_DIMENSIONS` from Phase 1
   - Backups made with 1536-dim embeddings won't be compatible with 1024-dim index — document this

5. **Test end-to-end**
   - `uv run python main.py load --clear` with Bedrock config
   - `uv run python main.py verify` to confirm vector search works
   - Run the solution demos to confirm they work with the new provider
