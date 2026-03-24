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
# Solutions 1-3 are skipped by default because they are destructive (delete data).
# Lab 4 solutions (9-11) require MCP_GATEWAY_URL and MCP_ACCESS_TOKEN in the env file.

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
    echo "  $0 .env.gold          # Run all safe solutions (4+)"
    echo "  $0 .env.gold 8        # Run only solution 8"
    echo "  $0 .env.gold 8-11     # Run solutions 8 through 11"
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
TOTAL=22

# Default: skip destructive solutions 1-3
DEFAULT_START=4
DEFAULT_END=$TOTAL

if [[ -n "$RANGE" ]]; then
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
    START=$DEFAULT_START
    END=$DEFAULT_END
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
    "Data Loading Fundamentals"              #  1
    "Embeddings"                             #  2
    "Entity Extraction"                      #  3
    "Full Dataset Queries"                   #  4
    "Vector Retriever"                       #  5
    "Vector Cypher Retriever"                #  6
    "Text2Cypher Retriever"                  #  7
    "Basic Strands Agent (Lab 3)"            #  8
    "Vector Search via MCP (Lab 4)"          #  9
    "Graph-Enriched Search via MCP (Lab 4)"  # 10
    "Fulltext & Hybrid Search (Lab 4)"       # 11
    "Simple Agent"                           # 12
    "Context Provider Intro"                 # 13
    "Fulltext Search"                        # 14
    "Hybrid Search"                          # 15
    "Fulltext Context Provider"              # 16
    "Vector Context Provider"                # 17
    "Graph-Enriched Provider"                # 18
    "Memory Context Provider"                # 19
    "Entity Extraction Pipeline"             # 20
    "Memory Tools Agent"                     # 21
    "Reasoning Memory"                       # 22
)

# Solutions that require MCP
MCP_SOLUTIONS=(9 10 11)

# --- Run solutions ---
PASS=0
FAIL=0
SKIP=0
RESULTS=()

for i in $(seq "$START" "$END"); do
    idx=$((i - 1))
    name="${NAMES[$idx]:-Solution $i}"

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
