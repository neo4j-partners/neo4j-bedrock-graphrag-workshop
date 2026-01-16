"""
Bedrock Stack for Neo4j Workshop.

This stack configures IAM roles and policies for Bedrock access.
Bedrock Agents are typically created through the console for workshops,
but this stack ensures the necessary permissions are in place.
"""

from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_iam as iam
from constructs import Construct


class BedrockStack(Stack):
    """
    CDK Stack for Bedrock configuration.

    Creates IAM roles and policies needed for:
    - Invoking Bedrock foundation models
    - Using Bedrock Agents
    - Accessing Bedrock AgentCore (if needed)
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create IAM role for Bedrock access (for use in notebooks/applications)
        self.bedrock_role = iam.Role(
            self,
            "BedrockAccessRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("bedrock.amazonaws.com"),
                iam.ServicePrincipal("lambda.amazonaws.com"),
            ),
            description="Role for accessing Bedrock models in Neo4j workshop",
        )

        # Add Bedrock invoke permissions
        self.bedrock_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockInvokeModels",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    # Claude models
                    f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-*",
                    # Titan models
                    f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-*",
                ],
            )
        )

        # Add Bedrock Converse API permissions
        self.bedrock_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockConverseAPI",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:Converse",
                    "bedrock:ConverseStream",
                ],
                resources=["*"],
            )
        )

        # Add Bedrock Agent permissions (for Lab 3)
        self.bedrock_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockAgentAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeAgent",
                    "bedrock:GetAgent",
                    "bedrock:ListAgents",
                ],
                resources=["*"],
            )
        )

        # Output the role ARN for reference
        CfnOutput(
            self,
            "BedrockRoleArn",
            value=self.bedrock_role.role_arn,
            description="ARN of the Bedrock access role",
            export_name="Neo4jWorkshopBedrockRoleArn",
        )
