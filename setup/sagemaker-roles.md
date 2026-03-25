# AgentCore Setup — SageMaker Role Timing Issue

## The Problem

The current `setup_agentcore.sh` script creates an **inline IAM policy** on all existing `AmazonSageMaker-ExecutionRole-*` roles. This policy grants the permissions needed for Lab 3's AgentCore deployment (creating runtime roles, S3 access, etc.).

SageMaker execution roles are created automatically when a participant creates their SageMaker domain. The role name includes a timestamp (e.g., `AmazonSageMaker-ExecutionRole-20260324T183042`) and cannot be pre-created by the admin. If the setup script runs **before** participants create their domains, their roles don't exist yet, and the policy is never attached. Participants then hit this error:

```
AccessDenied: iam:CreateRole on resource AmazonBedrockAgentCoreSDKRuntime-...
because no identity-based policy allows the iam:CreateRole action
```

## The Fix

Split the setup into two phases and switch from inline policies to a **customer-managed IAM policy**.

### Phase 1 — Admin runs `setup_agentcore.sh` (before the workshop)

This script runs once, before any participants join. It creates:

1. **AgentCore Runtime execution role** — the IAM role deployed agents assume at runtime (unchanged)
2. **S3 bucket** — for code deployment (unchanged)
3. **Customer-managed IAM policy** — `BedrockAgentCoreLabDeployPolicy` with all the deployment permissions (bedrock-agentcore, scoped IAM, S3, CloudWatch). This is a standalone IAM resource that exists independent of any roles.

The script no longer searches for or attaches to SageMaker roles.

### Phase 2 — Admin runs `grant_sagemaker_access.sh` (after participants create domains)

This is a separate, lightweight script that:

1. Finds all `AmazonSageMaker-ExecutionRole-*` roles in the account
2. Attaches the managed policy created in Phase 1 to each role
3. Reports which roles were updated

**This script is idempotent and must be re-run** whenever new participants create SageMaker domains. If a participant joins late, the admin runs it again to pick up the new role.

### Phase 3 — Participant notebook verification

The top of the Lab 3 deployment notebook (`02_deploy_to_agentcore.ipynb`) includes a cell that:

1. Detects the participant's current SageMaker execution role
2. Checks if the managed policy is attached
3. If not attached, **stops the notebook** with a clear message asking the participant to contact the admin

The participant does not need any special IAM permissions — the admin handles all policy attachment.

## Admin Workflow

```
1. Admin runs:    ./setup_agentcore.sh              (creates policy, role, bucket)
2. Participants:  Create SageMaker domains           (creates execution roles)
3. Admin runs:    ./grant_sagemaker_access.sh        (attaches policy to all roles)
4. Participants:  Run Lab 3 notebook                 (verification cell passes)

If a late participant joins:
5. Admin re-runs: ./grant_sagemaker_access.sh        (picks up new role)
```

## Cleanup

```bash
./setup_agentcore.sh --cleanup       # removes policy, role, bucket, detaches from all roles
```
