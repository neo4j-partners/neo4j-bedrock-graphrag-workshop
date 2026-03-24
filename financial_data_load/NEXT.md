# Next Steps: Cleanse Pipeline

## Workflow (after killing current run)

```bash
# 1. Validation only (fast, ~30-50 LLM calls)
uv run python main.py cleanse --phase validate

# 2. Dedup everything except RiskFactor, building on the validation plan
uv run python main.py cleanse --phase dedup --base-plan logs/cleanse_plan_XXX.json --skip-labels RiskFactor

# 3. Later, dedup just RiskFactor (after tuning threshold — current 0.6 generates 40k+ pairs)
uv run python main.py cleanse --phase dedup --base-plan logs/cleanse_plan_YYY.json --only-labels RiskFactor
```

## Notes

- Each step checkpoints after every completed label
- `--base-plan` carries forward removals and dedup sections from a previous run
- RiskFactor needs threshold tuned (0.85+) and/or batch_size increased before running
- Remaining dedup labels after RiskFactor: FinancialMetric, Company
- Company is fast (9 entities, proven prefix-0.3 config)
- FinancialMetric at threshold 0.7 should be manageable
