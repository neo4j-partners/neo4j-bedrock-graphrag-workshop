# Optional: Generate a Data Model with Document Intelligence

Neo4j Aura includes **Document Intelligence**, an agent that reads a raw document and proposes a graph data model (node labels, relationships, and properties) directly from the unstructured text. In this optional exercise you will drag and drop one of the sample SEC 10-K filings and let the agent generate a model, giving you a feel for how the structured knowledge graph used throughout this workshop could be built straight from source documents.

> **Note:** This exercise is optional and self-contained. It generates a model from a single document and does not affect the seed data loaded in Lab 1. Use it to explore the feature, then continue with the main labs.

## Step 1: Open Document Intelligence

Go to the Neo4j Aura console at [console.neo4j.io](https://console.neo4j.io) and make sure your instance is selected.

In the left sidebar, click the **Document Intelligence** icon. You will see the **Document Intelligence Agent** panel with a drop zone that accepts `.pdf`, `.txt`, `.md`, `.docx`, and `.epub` files.

## Step 2: Drag and Drop a Sample 10-K

The workshop ships eight sample 10-K filings in [`financial_data_load/financial-data/form10k-sample/`](../financial_data_load/financial-data/form10k-sample/):

| File | Company |
| --- | --- |
| `0000320193-23-000106.pdf` | Apple |
| `0000950170-23-035122.pdf` | Microsoft |
| `0001045810-23-000017.pdf` | NVIDIA |
| `0001652044-16-000012.pdf` | Alphabet (Google) |
| `0001018724-23-000004.pdf` | Amazon |
| `0001633917-23-000033.pdf` | PayPal |
| `0001004980-23-000029.pdf` | PG&E |
| `0001096906-23-001489.pdf` | Verde Bio Holdings |

Drag one of these PDFs (for example the Apple filing, `0000320193-23-000106.pdf`) from your file browser onto the drop zone, or click **browse** and select it. Wait for the data source status to change to **Ready**.

## Step 3: Add Context for Model Generation

When you generate a model, the agent asks you to **Add context for model generation** so it can produce a graph that fits your domain rather than a generic one. Describe the data domain and what the generated model should focus on.

Paste the following suggested prompt into the **Context** box:

```
This data is from SEC 10-K annual financial filings. Focus on companies (the filing
entity), the products and services they offer, the risk factors they disclose, their
executives, and their financial metrics. Also capture relationships between companies
such as competitors and strategic partners, and the institutional asset managers that
own shares in them.
```

This mirrors the schema you use throughout the rest of the workshop, so the generated model is a useful point of comparison.

## Step 4: Generate and Review the Model

Click **Generate model**. The agent reads the filing and proposes a graph model in the canvas: node labels with properties, and the relationships connecting them.

Review the result and compare it to the workshop schema:

- **Nodes**: Company, Product, RiskFactor, AssetManager, Document, Chunk
- **Relationships**: OFFERS, FACES_RISK, COMPETES_WITH, PARTNERS_WITH, OWNS

Notice how much of the structure the agent infers directly from a single unstructured document. You can refine the model by chatting further with the agent, adjusting node and relationship definitions, or editing properties before running an import.

## Step 5: (Optional) Run the Import

If you want to materialize the model, click **Run import** to load the extracted nodes and relationships from the document into your graph. This is optional. For the rest of the workshop you will use the pre-loaded seed data, so you can stop here without importing.

## Next Steps

Return to the [main lab instructions](README.md) to continue with the workshop.
