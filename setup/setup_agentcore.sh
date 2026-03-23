#!/usr/bin/env bash
# ==============================================================================
# AgentCore Lab Setup — Run ONCE per AWS account before the workshop
#
# Creates:
#   1. AgentCore Runtime execution role (used by deployed agents)
#   2. S3 bucket for code deployment
#   3. Adds AgentCore deployment permissions to the SageMaker execution role
#
# Usage:
#   ./setup_agentcore.sh                          # auto-detect region from CONFIG.txt
#   ./setup_agentcore.sh --region us-west-2       # specify region
#   ./setup_agentcore.sh --cleanup                # remove all created resources
# ==============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
CLEANUP=false
REGION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --region) REGION="$2"; shift 2 ;;
        --cleanup) CLEANUP=true; shift ;;
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

# Resource names
EXECUTION_ROLE_NAME="AmazonBedrockAgentCoreLabRuntime-${REGION}"
EXECUTION_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${EXECUTION_ROLE_NAME}"
DEPLOYMENT_POLICY_NAME="BedrockAgentCoreLabDeployPolicy"
S3_BUCKET="bedrock-agentcore-codebuild-sources-${ACCOUNT_ID}-${REGION}"

echo "=============================================="
echo "AgentCore Lab Setup"
echo "=============================================="
echo "Account:  ${ACCOUNT_ID}"
echo "Region:   ${REGION}"
echo "Role:     ${EXECUTION_ROLE_NAME}"
echo "S3:       ${S3_BUCKET}"
echo "=============================================="

# ---------------------------------------------------------------------------
# Cleanup mode
# ---------------------------------------------------------------------------
if [[ "$CLEANUP" == "true" ]]; then
    echo ""
    echo "Cleaning up AgentCore lab resources..."

    # Delete inline policy from execution role
    echo "  Removing execution role policy..."
    aws iam delete-role-policy \
        --role-name "$EXECUTION_ROLE_NAME" \
        --policy-name "AgentCoreRuntimePermissions" 2>/dev/null || true

    # Delete execution role
    echo "  Deleting execution role..."
    aws iam delete-role --role-name "$EXECUTION_ROLE_NAME" 2>/dev/null || true

    # Find and clean up SageMaker role policy
    echo "  Removing deployment policy from SageMaker roles..."
    for role in $(aws iam list-roles --query "Roles[?starts_with(RoleName, 'AmazonSageMaker-ExecutionRole')].RoleName" --output text); do
        aws iam delete-role-policy \
            --role-name "$role" \
            --policy-name "$DEPLOYMENT_POLICY_NAME" 2>/dev/null || true
        echo "    Removed from: $role"
    done

    # Empty and delete S3 bucket
    echo "  Deleting S3 bucket..."
    aws s3 rb "s3://${S3_BUCKET}" --force 2>/dev/null || true

    echo ""
    echo "Cleanup complete."
    exit 0
fi

# ---------------------------------------------------------------------------
# 1. Create the AgentCore Runtime execution role
# ---------------------------------------------------------------------------
echo ""
echo "1. Creating AgentCore Runtime execution role..."

TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AssumeRolePolicy",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "${ACCOUNT_ID}"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock-agentcore:${REGION}:${ACCOUNT_ID}:*"
        }
      }
    }
  ]
}
EOF
)

# Create role (skip if exists)
if aws iam get-role --role-name "$EXECUTION_ROLE_NAME" &>/dev/null; then
    echo "   Role already exists: ${EXECUTION_ROLE_NAME}"
else
    aws iam create-role \
        --role-name "$EXECUTION_ROLE_NAME" \
        --assume-role-policy-document "$TRUST_POLICY" \
        --tags Key=Purpose,Value=BedrockAgentCoreLab \
        --output text --query 'Role.Arn'
    echo "   Created role: ${EXECUTION_ROLE_NAME}"
fi

# Attach permissions policy
RUNTIME_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogStreams",
        "logs:CreateLogGroup"
      ],
      "Resource": [
        "arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:/aws/bedrock-agentcore/runtimes/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["logs:DescribeLogGroups"],
      "Resource": ["arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:${REGION}:${ACCOUNT_ID}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords",
        "xray:GetSamplingRules",
        "xray:GetSamplingTargets"
      ],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Resource": "*",
      "Action": "cloudwatch:PutMetricData",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "bedrock-agentcore"
        }
      }
    },
    {
      "Sid": "BedrockModelInvocation",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/*",
        "arn:aws:bedrock:${REGION}:${ACCOUNT_ID}:*"
      ]
    }
  ]
}
EOF
)

aws iam put-role-policy \
    --role-name "$EXECUTION_ROLE_NAME" \
    --policy-name "AgentCoreRuntimePermissions" \
    --policy-document "$RUNTIME_POLICY"
echo "   Attached runtime permissions policy"

# ---------------------------------------------------------------------------
# 2. Create S3 bucket for code deployment
# ---------------------------------------------------------------------------
echo ""
echo "2. Creating S3 bucket for code deployment..."

if aws s3 ls "s3://${S3_BUCKET}" &>/dev/null; then
    echo "   Bucket already exists: ${S3_BUCKET}"
else
    if [[ "$REGION" == "us-east-1" ]]; then
        aws s3api create-bucket --bucket "$S3_BUCKET"
    else
        aws s3api create-bucket --bucket "$S3_BUCKET" \
            --create-bucket-configuration LocationConstraint="$REGION"
    fi
    echo "   Created bucket: ${S3_BUCKET}"
fi

# ---------------------------------------------------------------------------
# 3. Add deployment permissions to SageMaker execution role(s)
# ---------------------------------------------------------------------------
echo ""
echo "3. Adding deployment permissions to SageMaker execution role(s)..."

DEPLOY_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AgentCoreRuntimeAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMRoleManagement",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:TagRole",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies"
      ],
      "Resource": [
        "arn:aws:iam::${ACCOUNT_ID}:role/*BedrockAgentCore*",
        "arn:aws:iam::${ACCOUNT_ID}:role/service-role/*BedrockAgentCore*"
      ]
    },
    {
      "Sid": "PassExecutionRole",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "arn:aws:iam::${ACCOUNT_ID}:role/AmazonBedrockAgentCore*",
        "arn:aws:iam::${ACCOUNT_ID}:role/service-role/AmazonBedrockAgentCore*"
      ]
    },
    {
      "Sid": "S3CodeDeployAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "s3:CreateBucket",
        "s3:PutLifecycleConfiguration"
      ],
      "Resource": [
        "arn:aws:s3:::bedrock-agentcore-*",
        "arn:aws:s3:::bedrock-agentcore-*/*"
      ]
    },
    {
      "Sid": "CloudWatchLogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:GetLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/bedrock-agentcore/*"
      ]
    }
  ]
}
EOF
)

# Find all SageMaker execution roles and add the policy
SAGEMAKER_ROLES=$(aws iam list-roles \
    --query "Roles[?starts_with(RoleName, 'AmazonSageMaker-ExecutionRole')].RoleName" \
    --output text)

if [[ -z "$SAGEMAKER_ROLES" ]]; then
    echo "   WARNING: No SageMaker execution roles found."
    echo "   You may need to manually attach the deployment policy to your role."
else
    for role in $SAGEMAKER_ROLES; do
        aws iam put-role-policy \
            --role-name "$role" \
            --policy-name "$DEPLOYMENT_POLICY_NAME" \
            --policy-document "$DEPLOY_POLICY"
        echo "   Added deployment policy to: ${role}"
    done
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "Setup complete!"
echo "=============================================="
echo ""
echo "Add the following to CONFIG.txt:"
echo ""
echo "AGENTCORE_EXECUTION_ROLE=${EXECUTION_ROLE_ARN}"
echo ""
echo "To clean up later:  ./setup_agentcore.sh --cleanup"
