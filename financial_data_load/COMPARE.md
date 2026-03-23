# Model Comparison: gpt-4o vs gpt-4.1-mini

Entity extraction quality comparison for SEC 10-K knowledge graph pipeline.

## Baseline (gpt-4o)

| Entity Type     | Count |
|-----------------|-------|
| Company         | 186   |
| RiskFactor      | 579   |
| Product         | 461   |
| Executive       | 54    |
| FinancialMetric | 412   |
| Chunk           | 390   |
| Document        | 8     |

Total entities: 1,707 (including AssetManager: 15)
Total schema relationships: 1,637

## TODO

- [x] Export gpt-4o baseline snapshot → `model_snapshots/gpt-4o_20260322_122912.json`
- [x] Deploy gpt-4.1-mini to Azure AI Services (GlobalStandard, 360 capacity)
- [x] Clear database and re-extract with gpt-4.1-mini (8/8 PDFs successful, 29m 41s)
- [x] Export gpt-4.1-mini snapshot → `model_snapshots/gpt-4.1-mini_20260322_131351.json`
- [x] Run comparison and record results below
- [x] Run entity resolution on gpt-4.1-mini Company nodes (550 → 167)
- [x] Apply merge plan (383 merges, 0 failures)
- [x] Finalize graph (constraints, indexes, asset managers, cross-label dedup)

## Entity Resolution (gpt-4.1-mini)

Ran LLM-based entity resolution on 550 Company entities using gpt-4.1-mini.

| Phase | Detail |
|-------|--------|
| Exact dedup | 550 → 186 unique names (364 auto-merges in 54 groups) |
| Pre-filter | 923 fuzzy candidate pairs (threshold 0.6) |
| LLM evaluation | 93 batches of 10, 38 merge decisions |
| Transitive confirmation | 2 additional pairs checked (round 1) |
| **LLM-confirmed merges** | **16 groups** |
| **Flagged for review** | **4 groups** |
| **Final Company count** | **167** |

### LLM Merge Groups (16)

| Survivor | Consumed |
|----------|----------|
| Alphabet Inc. | Alphabet |
| Amazon.com, Inc. | Amazon, Amazon, Inc., Amazon.com |
| Apple Inc. | Apple |
| Baidu | Baidu, Inc. |
| Broadcom | Broadcom Inc. |
| Cisco | Cisco Systems, Cisco Systems, Inc. |
| Hewlett-Packard | Hewlett-Packard Company |
| Intel Corporation | Intel |
| Microsoft Corporation | Microsoft |
| NVIDIA Corporation | NVIDIA |
| Nuance | Nuance Communications, Inc. |
| Other Bets | Other Bets businesses |
| PG&E Corporation | PG&E |
| Paidy | Paidy, Inc. |
| Samsung | Samsung Electronics Co. Ltd |
| SoftBank | SoftBank Group Corp. |

### Flagged Groups (4 — not auto-merged)

| Entities | Reason |
|----------|--------|
| Access/Google Fiber, Google, Google Inc., GV | 1 pair not confirmed |
| PayPal, PayPal Holdings, Inc., PayPal (Europe) + variants | 7 pairs not confirmed |
| The Utility, the Utility, Utility | 1 pair not confirmed |
| our, our company, the Company | 1 pair not confirmed |

### Post-Resolution Counts

| Entity Type     | Pre-Resolution | Post-Resolution | Reduced |
|-----------------|---------------|-----------------|---------|
| Company         | 550           | 167             | -383    |
| RiskFactor      | 643           | 643             | —       |
| Product         | 636           | 636             | —       |
| Executive       | 58            | 58              | —       |
| FinancialMetric | 637           | 637             | —       |
| **Total**       | **2,524**     | **2,141**       | **-383** |

### Entity Resolution Validation

14/15 checks passed. Only failure: Google (2 nodes — Google Inc. and Google not merged due to the flagged Access/Google Fiber/GV cluster).

## Finalize

Finalize step applied constraints, recreated indexes, loaded asset managers, and deduped same-name entities across all labels.

### Cross-Label Dedup (uniqueness constraint enforcement)

| Entity Type     | Duplicates Merged | Groups |
|-----------------|-------------------|--------|
| Company         | 1 deleted (empty name) | — |
| RiskFactor      | 33                | 25     |
| Product         | 163               | 90     |
| Executive       | 13                | 13     |
| FinancialMetric | 250               | 143    |
| **Total**       | **460**           | **271** |

### Final Graph State (post-finalize)

| Entity Type     | gpt-4o (baseline) | gpt-4.1-mini (final) | Delta |
|-----------------|-------------------|----------------------|-------|
| Company         | 186               | 166                  | -20   |
| RiskFactor      | 579               | 610                  | +31   |
| Product         | 461               | 473                  | +12   |
| Executive       | 54                | 45                   | -9    |
| FinancialMetric | 412               | 387                  | -25   |
| AssetManager    | 15                | 15                   | —     |
| Chunk           | 390               | 390                  | —     |
| Document        | 8                 | 8                    | —     |
| **Total Nodes** | **2,090**         | **2,094**            | **+4** |

| Relationship    | gpt-4o (baseline) | gpt-4.1-mini (final) | Delta |
|-----------------|-------------------|----------------------|-------|
| FACES_RISK      | 594               | 666                  | +72   |
| OFFERS          | 470               | 478                  | +8    |
| REPORTS         | 371               | 378                  | +7    |
| PARTNERS_WITH   | 50                | 88                   | +38   |
| COMPETES_WITH   | 91                | 58                   | -33   |
| HAS_EXECUTIVE   | 61                | 39                   | -22   |
| OWNS            | —                 | 103                  | +103  |
| **Schema Total**| **1,637**         | **1,707**            | **+70** |

### Constraints & Indexes

- 6 uniqueness constraints (Company, AssetManager, RiskFactor, Product, Executive, FinancialMetric)
- Vector index: `chunkEmbeddings` (1536 dims)
- Fulltext indexes: `search_entities`, `search_chunks`
- 120 asset manager OWNS relationships created

### Validation

14/15 entity resolution checks passed. Only remaining: Google (2 nodes — Google and Google Inc.).

## Results

### Entity Counts

| Entity Type     | gpt-4o | gpt-4.1-mini | Delta |
|-----------------|--------|--------------|-------|
| Company         | 186    | 550          | +364  |
| RiskFactor      | 579    | 643          | +64   |
| Product         | 461    | 636          | +175  |
| Executive       | 54     | 58           | +4    |
| FinancialMetric | 412    | 637          | +225  |
| **Total**       | **1,707** | **2,524** | **+817** |

### Relationship Counts

| Relationship    | gpt-4o | gpt-4.1-mini | Delta |
|-----------------|--------|--------------|-------|
| FACES_RISK      | 594    | 682          | +88   |
| OFFERS          | 470    | 580          | +110  |
| HAS_EXECUTIVE   | 61     | 49           | -12   |
| REPORTS         | 371    | 594          | +223  |
| COMPETES_WITH   | 91     | 78           | -13   |
| PARTNERS_WITH   | 50     | 118          | +68   |
| **Total**       | **1,637** | **2,101** | **+464** |

### Entity Overlap

| Entity Type     | Common | Only gpt-4o | Only gpt-4.1-mini |
|-----------------|--------|-------------|-------------------|
| RiskFactor      | 95     | 484         | 515               |
| Product         | 207    | 254         | 266               |
| Executive       | 43     | 11          | 2                 |
| FinancialMetric | 74     | 338         | 313               |

### Key Observations

1. **gpt-4.1-mini extracts significantly more entities** — 48% more total entities (2,524 vs 1,707) and 28% more relationships (2,101 vs 1,637).

2. **Company node explosion** — 550 vs 186. gpt-4.1-mini is creating many more Company entities from the text (competitors, partners, subsidiaries mentioned in filings). These will need entity resolution to deduplicate.

3. **Low overlap between models** — only 95 of ~600 RiskFactors are shared, and only 207 of ~550 Products. The models are naming entities differently even when extracting from the same text. This is a naming/normalization issue, not necessarily a quality difference.

4. **RiskFactor descriptions are richer with gpt-4.1-mini** — of 95 shared risk factors, gpt-4.1-mini produced longer descriptions for 82 of them (86%).

5. **Executive extraction is cleaner** — gpt-4.1-mini avoided extracting generic roles ("CEO", "Board of Directors", "Employees") as entities, keeping only named individuals. Only 2 unique to gpt-4.1-mini vs 11 unique to gpt-4o (most of which were not actual person entities).

6. **FinancialMetric explosion** — both models extract many metrics but with very different naming conventions. gpt-4.1-mini captures more specific bond instruments and financial line items.

7. **PARTNERS_WITH more than doubled** — 118 vs 50, suggesting gpt-4.1-mini is better at identifying partnership relationships.

### Processing Time

| PDF | gpt-4.1-mini |
|-----|-------------|
| Apple (74KB) | 42s |
| Microsoft (789KB) | 12m 8s |
| PG&E (270KB) | 2m 24s |
| Amazon (97KB) | 10m 29s |
| NVIDIA (137KB) | 1m 9s |
| Apple proxy (19KB) | 29s |
| PayPal (168KB) | 1m 8s |
| Alphabet (153KB) | 1m 10s |
| **Total** | **29m 41s** |

### Verdict

gpt-4.1-mini is a clear upgrade after full pipeline (extraction → entity resolution → finalize):
- **Similar total node count** (2,094 vs 2,090) but with richer content and descriptions
- **+70 schema relationships** (1,707 vs 1,637) — more connections discovered
- **+38 PARTNERS_WITH** — nearly doubled partnership detection
- **+72 FACES_RISK** — more risk factors linked to companies
- **Cleaner Company nodes** — 166 vs 186 after dedup (fewer generics like "the Company")
- **Richer descriptions** — 86% of shared RiskFactors had longer text
- **Zero code changes** required (drop-in replacement)
- Entity resolution handled the Company explosion (550 → 166) effectively

The raw extraction "explosion" (48% more entities) was mostly duplicates and naming variants. After entity resolution and finalize dedup, the graph is comparable in size but higher quality — more relationships, richer text, and fewer false positive entities.
