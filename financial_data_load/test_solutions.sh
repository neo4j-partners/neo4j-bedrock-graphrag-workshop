#!/usr/bin/env bash
#
# Test all workshop solution scripts.
#
# Usage:
#   ./test_solutions.sh <env-file>       # Run all safe solutions
#   ./test_solutions.sh .env.gold        # Run with gold credentials
#   ./test_solutions.sh .env.gold 8      # Run only solution 8
#   ./test_solutions.sh .env.gold 8-11   # Run solutions 8 through 11
#
# The env file is sourced into the shell environment (your .env is not modified).
# Data-writing solutions (1 load-and-query, 8 data load, 9 embeddings)
# are skipped by default. Lab 5 solutions (5-7) require MCP_GATEWAY_URL and MCP_ACCESS_TOKEN.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_TXT="$PROJECT_ROOT/CONFIG.txt"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- Usage ---
usage() {
    echo "Usage: $0 <env-file> [solution-number|range]"
    echo ""
    echo "  env-file        Path to .env file (e.g., .env.gold)"
    echo "  solution-number Optional: run only this solution (e.g., 8)"
    echo "  range           Optional: run a range (e.g., 8-11)"
    echo ""
    echo "Examples:"
    echo "  $0 .env.gold          # Run all safe solutions (skips data-writing)"
    echo "  $0 .env.gold 4        # Run only solution 4"
    echo "  $0 .env.gold 4-6      # Run solutions 4 through 6"
    exit 1
}

if [[ $# -lt 1 ]]; then
    usage
fi

ENV_FILE="$1"
RANGE="${2:-}"

# Resolve relative path
if [[ ! "$ENV_FILE" = /* ]]; then
    ENV_FILE="$SCRIPT_DIR/$ENV_FILE"
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}Error: env file not found: $ENV_FILE${NC}"
    exit 1
fi

# --- Determine which solutions to run ---
# Total solutions (from main.py SOLUTIONS list)
TOTAL=10

# Solutions skipped by default (data-writing):
#   1 Load Data and Query
#   8 Data Loading (deletes all)  9 Embeddings
DEFAULT_SKIP=(1 8 9)

if [[ -n "$RANGE" ]]; then
    RANGE_GIVEN=true
    if [[ "$RANGE" =~ ^([0-9]+)-([0-9]+)$ ]]; then
        START="${BASH_REMATCH[1]}"
        END="${BASH_REMATCH[2]}"
    elif [[ "$RANGE" =~ ^[0-9]+$ ]]; then
        START="$RANGE"
        END="$RANGE"
    else
        echo -e "${RED}Error: invalid range '$RANGE'. Use N or N-M.${NC}"
        exit 1
    fi
else
    RANGE_GIVEN=false
    START=1
    END=$TOTAL
fi

# --- Load env vars from file (no .env copy) ---
set -a
source "$ENV_FILE"
set +a

echo -e "${BOLD}Testing solutions with: $(basename "$ENV_FILE")${NC}"
echo -e "Range: ${START}-${END}"
echo ""

# --- Check MCP configuration for Lab 4 solutions ---
MCP_AVAILABLE=false
if [[ -n "${MCP_GATEWAY_URL:-}" && "$MCP_GATEWAY_URL" != "your-gateway-url-here" ]]; then
    MCP_AVAILABLE=true
fi

# --- Solution metadata (matches main.py SOLUTIONS list) ---
NAMES=(
    "Load Data and Query (Lab 4)"            #  1
    "Vector Retriever (Lab 4)"               #  2
    "VectorCypher Retriever (Lab 4)"         #  3
    "Strands GraphRAG Agent (Lab 4)"         #  4
    "Intro to Strands + MCP (Lab 5)"         #  5
    "Graph-Enriched Search via MCP (Lab 5)"  #  6
    "Text2Cypher Agent (Lab 5)"              #  7
    "Data Loading (Lab 6)"                   #  8
    "Embeddings (Lab 6)"                     #  9
    "VectorCypher Retriever (Lab 6)"         # 10
)

# Solutions that require MCP
MCP_SOLUTIONS=(5 6 7)

# --- Run solutions ---
PASS=0
FAIL=0
SKIP=0
RESULTS=()

for i in $(seq "$START" "$END"); do
    idx=$((i - 1))
    name="${NAMES[$idx]:-Solution $i}"

    # Skip data-writing solutions unless an explicit number/range was given
    if [[ "$RANGE_GIVEN" == "false" ]]; then
        for skip in "${DEFAULT_SKIP[@]}"; do
            if [[ "$i" -eq "$skip" ]]; then
                echo -e "${YELLOW}[SKIP]${NC} ${BOLD}#${i}${NC} ${name} (data-writing; pass the number explicitly to run)"
                RESULTS+=("SKIP|$i|$name|data-writing")
                SKIP=$((SKIP + 1))
                continue 2
            fi
        done
    fi

    # Check if this solution needs MCP
    needs_mcp=false
    for mcp_sol in "${MCP_SOLUTIONS[@]}"; do
        if [[ "$i" -eq "$mcp_sol" ]]; then
            needs_mcp=true
            break
        fi
    done

    if [[ "$needs_mcp" == "true" && "$MCP_AVAILABLE" == "false" ]]; then
        echo -e "${YELLOW}[SKIP]${NC} ${BOLD}#${i}${NC} ${name} (MCP not configured in $(basename "$ENV_FILE"))"
        RESULTS+=("SKIP|$i|$name|MCP not configured")
        SKIP=$((SKIP + 1))
        continue
    fi

    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}Running #${i}: ${name}${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    LOG_FILE="$SCRIPT_DIR/.test-solution-${i}.log"

    set +e
    (
        cd "$SCRIPT_DIR"
        timeout 300 uv run python main.py solutions "$i"
    ) > "$LOG_FILE" 2>&1
    EXIT_CODE=$?
    set -e

    if [[ $EXIT_CODE -eq 0 ]]; then
        echo -e "${GREEN}[PASS]${NC} ${BOLD}#${i}${NC} ${name}"
        RESULTS+=("PASS|$i|$name|")
        PASS=$((PASS + 1))
        rm -f "$LOG_FILE"
    elif [[ $EXIT_CODE -eq 124 ]]; then
        echo -e "${RED}[FAIL]${NC} ${BOLD}#${i}${NC} ${name} (timeout after 5 min)"
        RESULTS+=("FAIL|$i|$name|timeout")
        FAIL=$((FAIL + 1))
        echo -e "  Log: ${LOG_FILE}"
    else
        echo -e "${RED}[FAIL]${NC} ${BOLD}#${i}${NC} ${name} (exit code: ${EXIT_CODE})"
        RESULTS+=("FAIL|$i|$name|exit $EXIT_CODE")
        FAIL=$((FAIL + 1))
        # Show last 10 lines of error
        echo -e "  ${RED}Last 10 lines:${NC}"
        tail -10 "$LOG_FILE" | sed 's/^/    /'
        echo -e "  Full log: ${LOG_FILE}"
    fi
done

# --- Summary ---
TOTAL_RUN=$((PASS + FAIL + SKIP))

echo -e "\n${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}Results${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

for result in "${RESULTS[@]}"; do
    IFS='|' read -r status num name reason <<< "$result"
    case "$status" in
        PASS) echo -e "  ${GREEN}PASS${NC}  #${num}  ${name}" ;;
        FAIL) echo -e "  ${RED}FAIL${NC}  #${num}  ${name}  (${reason})" ;;
        SKIP) echo -e "  ${YELLOW}SKIP${NC}  #${num}  ${name}  (${reason})" ;;
    esac
done

echo ""
echo -e "  ${GREEN}Passed: ${PASS}${NC}  ${RED}Failed: ${FAIL}${NC}  ${YELLOW}Skipped: ${SKIP}${NC}  Total: ${TOTAL_RUN}"
echo ""

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
