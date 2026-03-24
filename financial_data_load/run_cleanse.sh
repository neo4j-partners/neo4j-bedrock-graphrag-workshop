#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

latest_plan() {
    ls -t logs/cleanse_plan_*.json 2>/dev/null | head -1
}

echo "=== Step 1: Validation ==="
uv run python main.py cleanse --phase validate

PLAN=$(latest_plan)
if [ -z "$PLAN" ]; then
    echo "ERROR: No cleanse plan found after validation"
    exit 1
fi
echo "Plan after validation: $PLAN"

echo ""
echo "=== Step 2: Dedup (skip RiskFactor) ==="
uv run python main.py cleanse --phase dedup --base-plan "$PLAN" --skip-labels RiskFactor

PLAN=$(latest_plan)
echo "Plan after dedup: $PLAN"

echo ""
echo "=== Step 3: Dedup RiskFactor ==="
uv run python main.py cleanse --phase dedup --base-plan "$PLAN" --only-labels RiskFactor

PLAN=$(latest_plan)
echo ""
echo "=== Done ==="
echo "Final plan: $PLAN"
echo ""
echo "Next: review the plan, then run:"
echo "  uv run python main.py apply-cleanse --plan $PLAN"
echo "  uv run python main.py finalize"
