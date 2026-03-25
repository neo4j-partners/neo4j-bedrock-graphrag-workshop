#!/usr/bin/env bash
# ==============================================================================
# Grant SageMaker Roles Access to AgentCore Deployment
#
# Attaches the BedrockAgentCoreLabDeployPolicy managed policy to all
# AmazonSageMaker-ExecutionRole-* roles in the account.
#
# Run this AFTER participants have created their SageMaker domains.
# Safe to re-run — idempotent.
#
# Usage:
#   ./grant_sagemaker_access.sh                    # auto-detect region from CONFIG.txt
#   ./grant_sagemaker_access.sh --region us-west-2 # specify region
# ==============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
REGION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --region) REGION="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Auto-detect region from CONFIG.txt if not specified
if [[ -z "$REGION" ]]; then
    CONFIG_FILE="$(dirname "$0")/../CONFIG.txt"
    if [[ -f "$CONFIG_FILE" ]]; then
        REGION=$(grep -E '^REGION=' "$CONFIG_FILE" | cut -d= -f2 | tr -d '[:space:]')
    fi
    REGION="${REGION:-us-east-1}"
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
POLICY_NAME="BedrockAgentCoreLabDeployPolicy"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

echo "=============================================="
echo "Grant SageMaker Roles — AgentCore Access"
echo "=============================================="
echo "Account:  ${ACCOUNT_ID}"
echo "Region:   ${REGION}"
echo "Policy:   ${POLICY_NAME}"
echo "=============================================="

# ---------------------------------------------------------------------------
# Verify the managed policy exists
# ---------------------------------------------------------------------------
if ! aws iam get-policy --policy-arn "$POLICY_ARN" &>/dev/null; then
    echo ""
    echo "ERROR: Managed policy not found: ${POLICY_ARN}"
    echo "Run ./setup_agentcore.sh first to create it."
    exit 1
fi

# ---------------------------------------------------------------------------
# Find and grant access to all SageMaker execution roles
# ---------------------------------------------------------------------------
echo ""
SAGEMAKER_ROLES=$(aws iam list-roles \
    --query "Roles[?starts_with(RoleName, 'AmazonSageMaker-ExecutionRole')].RoleName" \
    --output text)

if [[ -z "$SAGEMAKER_ROLES" ]]; then
    echo "WARNING: No AmazonSageMaker-ExecutionRole-* roles found."
    echo "Participants may not have created their SageMaker domains yet."
    exit 0
fi

ATTACHED=0
SKIPPED=0

for role in $SAGEMAKER_ROLES; do
    # Check if already attached
    if aws iam list-attached-role-policies \
        --role-name "$role" \
        --query "AttachedPolicies[?PolicyArn=='${POLICY_ARN}'].PolicyName" \
        --output text | grep -q "$POLICY_NAME"; then
        echo "  Already attached: ${role}"
        SKIPPED=$((SKIPPED + 1))
    else
        aws iam attach-role-policy \
            --role-name "$role" \
            --policy-arn "$POLICY_ARN"
        echo "  Attached policy:  ${role}"
        ATTACHED=$((ATTACHED + 1))
    fi
done

echo ""
echo "=============================================="
echo "Done. Attached: ${ATTACHED}  Already had it: ${SKIPPED}"
echo "=============================================="
