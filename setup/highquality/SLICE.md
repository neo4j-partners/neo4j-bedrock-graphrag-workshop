# Seed Data Slice Proposal

A proposal for replacing the current `setup/seed-data/` CSVs with a curated, high-quality slice of the financial knowledge graph. The goal is to give workshop participants clean data that loads quickly, visualizes clearly in Neo4j Explore, and supports every query and exercise across Labs 1 and 2.

## What's Wrong With the Current Seed Data

The existing CSVs were exported from the raw LLM extraction pipeline and carry all of its noise forward into participants' databases.

**Scale problems.** 900 risk factors and 364 products overwhelm the Explore canvas. When a participant runs the `AssetManager — OWNS → Company — FACES_RISK → RiskFactor` pattern, they see a dense hairball instead of a readable graph. The visualization loses its teaching value.

**Quality problems.** The CSVs still contain every issue documented in `DATA_QUALITY_ISSUES.md`: self-referencing competitors, duplicate products, non-product entries like "Enterprise Agreement" and "Senior Secured Recovery Bonds," and inconsistent naming. Participants who run "Who does NVIDIA compete with?" get back Cooley LLP (a law firm) and Jabil Inc. (a contract manufacturer) alongside AMD and Intel.

**Missing file.** The Lab 1 load script references `company_partners.csv` but the file does not exist. The LOAD CSV statement silently produces zero rows, which means the `PARTNERS_WITH` relationship type exists in the schema but contains no data. The Explore exercise that asks participants to visualize the partner network returns an empty canvas.

**Stale expected counts.** The Lab 1 README tells participants to expect 76 Company nodes, 274 Products, and 203 RiskFactors. None of these match the actual CSV row counts. Participants who verify their load see different numbers and assume something went wrong.

## What the Slice Needs to Support

Every query and exercise in Labs 1 and 2 must work against the sliced data. The critical paths are:

**Lab 1 Explore patterns:**
- `AssetManager — OWNS → Company — FACES_RISK → RiskFactor` — needs all 15 asset managers, all 6 filing companies, and enough shared risk factors to show cross-company exposure
- `Company — COMPETES_WITH → Company` — needs enough competitive edges for degree centrality to produce a visually meaningful size difference between Microsoft/NVIDIA (many competitors) and PG&E/PayPal (fewer)
- `Company — OFFERS → Product` — needs recognizable products per company
- `Company — PARTNERS_WITH → Company` — needs real partner relationships to populate the canvas

**Lab 1 sample queries:**
- "What products does NVIDIA offer?" — needs NVIDIA products
- "Which risk factors are shared across multiple companies?" — needs risk factors assigned to two or more companies
- "Who are the top asset managers by holdings?" — needs the full asset manager holdings data
- "Who does Microsoft compete with?" — needs clean competitor list
- "Who are NVIDIA's supply chain partners?" — needs PARTNERS_WITH data

**Lab 2 Aura Agent tools:**
- Cypher Templates query Company details, risk factors, products, executives, and asset manager holdings
- Text2Cypher generates ad-hoc queries against whatever the graph contains
- Similarity Search operates on Chunk embeddings (loaded separately from the backup, not from the seed CSVs)

## Proposed Slice

### Companies (keep all 6)

No change. All six filing companies stay: Amazon, Apple, Microsoft, NVIDIA, PG&E, and PayPal. Each with corrected identifiers (PayPal CUSIP fixed, Amazon padded, NVIDIA and PG&E trimmed to 9 characters).

### Asset Managers (keep all 15)

No change. All 15 institutional holders with their share counts. Rename from ALL CAPS and strip SEC filing artifacts ("/DE/", "/MN") so names display cleanly in Explore.

### Products (cut from 364 to roughly 80-100)

The current product list is full of LLM extraction noise: six variants of "Omniverse," sixteen consumer credit sub-products, and licensing terms like "Software Assurance" that aren't products at all. A workshop participant doesn't need to see every line item the LLM pulled from a filing. They need enough recognizable products to make the graph explorable and the agent queries useful.

**Selection criteria for what stays:**
- Flagship, publicly recognizable products that a participant would know (iPhone, Azure, GeForce, PayPal, AWS)
- Products distinct enough to be individually meaningful, not minor variants of the same thing (keep "NVIDIA H100 Tensor Core GPU," drop "H100 Integrated Circuit" and "H100 integrated circuits")
- At least 10-15 products per company so the `Company — OFFERS → Product` pattern has substance
- No licensing agreements, internal programs, or financial instruments

**Rough target per company:**
- Amazon (~10): AWS, Amazon Prime, Alexa, Kindle, Fire TV, Ring, Blink, eero, Fulfillment by Amazon, Amazon Bedrock
- Apple (~15): iPhone, iPad, Mac, Apple Watch, AirPods, Apple TV+, Apple Pay, Apple Vision Pro, Apple Music, App Store, AppleCare, HomePod, Apple Arcade, iOS, macOS
- Microsoft (~20): Azure, Microsoft 365, Windows, Xbox, LinkedIn, GitHub, GitHub Copilot, Teams, Dynamics 365, Surface, Bing, Microsoft Defender, Office, Power Platform, SharePoint, OneDrive, Visual Studio, Outlook, Microsoft Fabric, HoloLens
- NVIDIA (~20): GeForce GPUs, NVIDIA RTX GPUs, NVIDIA H100 Tensor Core GPU, DGX Systems, CUDA, DRIVE platform, Omniverse, BlueField DPU, A100, Grace CPU, InfiniBand, NVIDIA AI Enterprise, DGX Cloud, GeForce NOW, Jetson, professional visualization products, networking products, NVIDIA DLSS, NVIDIA Spectrum-4
- PG&E (~10): Electric service, gas delivery, gas transmission and storage, Diablo Canyon Nuclear Power Plant, Elkhorn Battery Energy Storage System, geothermal energy, metering services, transmission services, generation stations
- PayPal (~15): PayPal, Venmo, Braintree, Xoom, PayPal Honey, Hyperwallet, Buy Now Pay Later, PayPal Zettle, PayPal Digital Wallet, Venmo Digital Wallet, merchant financing, branded credit and debit cards, cryptocurrency services, consumer credit products, Paidy

### Risk Factors (cut from 900 to roughly 50-80)

This is the most aggressive cut and the most important one for the Explore experience. The current 900 risk factors include company-specific regulatory minutiae (individual wildfire incidents, specific bond series) alongside broadly relevant risks (cybersecurity, AI regulation, climate change). For a workshop, participants need risk factors that tell a story about the companies and their industries.

**Selection criteria for what stays:**
- Risk factors shared by two or more companies (these create the cross-company connections that make the `AssetManager — OWNS → Company — FACES_RISK → RiskFactor` pattern visually interesting)
- A representative set of company-specific risks that are distinctive enough to be conversation starters (PG&E wildfire liability, NVIDIA export controls, PayPal anti-money laundering)
- One entry per concept, not multiple phrasings of the same risk

**Categories to preserve:**
- Cross-cutting: cybersecurity, data privacy, AI regulation, competition, intellectual property, tax, supply chain, macroeconomic conditions, foreign exchange, climate and environmental
- Amazon-specific: AWS growth, platform abuse, fulfillment complexity
- Apple-specific: App Store regulation, consumer device competition, supply chain concentration
- Microsoft-specific: cloud competition, AI development, antitrust
- NVIDIA-specific: export controls, semiconductor supply, AI demand concentration, crypto mining volatility
- PG&E-specific: wildfire liability, aging infrastructure, regulatory rate recovery, nuclear decommissioning
- PayPal-specific: payment fraud, regulatory licensing, account holder default, cryptocurrency risk

### Competitors (use cleaned data, roughly 50-60 edges)

Export directly from the fixed database. Every filing company has a meaningful set of real competitors with no self-references, subsidiaries, acquisitions, suppliers, or duplicate entries.

### Partners (create the missing file, roughly 5-10 edges)

The `company_partners.csv` file needs to exist. Populate it with a small set of real partnerships that make the Explore partner network exercise work. These should be relationships that participants would recognize as genuine strategic or supply chain partnerships.

Candidates: NVIDIA with TSMC (foundry), Amazon with Rivian (investment), Apple with TSMC (chip manufacturing), Microsoft with OpenAI (AI partnership), PG&E with the California ISO (grid operations).

## Expected Counts After Slicing

These become the new "Verify the Load" numbers in the Lab 1 README.

| Label | Current CSV | Proposed Slice |
|-------|------------|----------------|
| Company | 6 filing + ~70 mentioned | 6 filing + ~40-50 mentioned |
| Product | 364 | ~80-100 |
| RiskFactor | 900 | ~50-80 |
| AssetManager | 15 | 15 |
| COMPETES_WITH edges | 129 | ~50-60 |
| PARTNERS_WITH edges | 0 (file missing) | ~5-10 |
| OFFERS edges | 366 | ~80-100 |
| FACES_RISK edges | 978 | ~150-250 |
| OWNS edges | 72 | 72 |

## Implementation Approach

The cleanest path is to export the slice from the fixed live database rather than manually editing the existing CSVs. The live database already has the quality fixes applied (merged duplicates, removed non-products, corrected CUSIPs, cleaned competitors, normalized names). A script would query the database for each entity type, apply the selection criteria above, and write new CSVs.

The risk factor selection is the one step that benefits from human judgment. A first pass could select all risk factors connected to two or more filing companies, then supplement with the most distinctive single-company risks. The result should be reviewed before publishing to make sure the cross-company overlap produces an interesting Explore visualization.

After generating the new CSVs, upload them to the S3 bucket via the existing `setup_s3_seed_data.sh` script, update the expected counts in the Lab 1 README, and verify that every Lab 1 query and Lab 2 agent tool returns reasonable results against the sliced data.
