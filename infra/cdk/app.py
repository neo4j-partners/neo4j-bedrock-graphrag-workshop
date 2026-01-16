#!/usr/bin/env python3
"""
AWS CDK Application for Neo4j and Bedrock Workshop.

This CDK app deploys the infrastructure needed for the workshop:
- Bedrock agent configuration and IAM roles
- CloudWatch monitoring and log groups
"""

import os

import aws_cdk as cdk

from stacks.bedrock_stack import BedrockStack
from stacks.monitoring_stack import MonitoringStack

# Get environment configuration
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("AWS_REGION", "us-east-1"),
)

app = cdk.App()

# Deploy monitoring stack first (other stacks may depend on it)
monitoring_stack = MonitoringStack(
    app,
    "Neo4jWorkshopMonitoring",
    env=env,
    description="CloudWatch monitoring for Neo4j and Bedrock workshop",
)

# Deploy Bedrock stack for agent configuration
bedrock_stack = BedrockStack(
    app,
    "Neo4jWorkshopBedrock",
    env=env,
    description="Bedrock agent configuration for Neo4j workshop",
)

# Add dependencies
bedrock_stack.add_dependency(monitoring_stack)

app.synth()
