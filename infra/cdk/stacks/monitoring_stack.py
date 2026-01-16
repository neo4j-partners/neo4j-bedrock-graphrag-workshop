"""
Monitoring Stack for Neo4j Workshop.

This stack creates CloudWatch resources for observability:
- Log groups for application logs
- Dashboard for monitoring workshop activity
"""

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_logs as logs
from constructs import Construct


class MonitoringStack(Stack):
    """
    CDK Stack for CloudWatch monitoring.

    Creates log groups and optional dashboard for workshop observability.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create log group for workshop application logs
        self.app_log_group = logs.LogGroup(
            self,
            "WorkshopAppLogs",
            log_group_name="/neo4j-workshop/application",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create log group for Bedrock agent logs
        self.agent_log_group = logs.LogGroup(
            self,
            "WorkshopAgentLogs",
            log_group_name="/neo4j-workshop/bedrock-agents",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create a simple dashboard for workshop monitoring
        self.dashboard = cloudwatch.Dashboard(
            self,
            "WorkshopDashboard",
            dashboard_name="Neo4j-Workshop-Dashboard",
        )

        # Add a text widget with workshop info
        self.dashboard.add_widgets(
            cloudwatch.TextWidget(
                markdown="# Neo4j and AWS Bedrock Workshop\n\nMonitoring dashboard for workshop activities.",
                width=24,
                height=2,
            )
        )

        # Add log insights widget for application logs
        self.dashboard.add_widgets(
            cloudwatch.LogQueryWidget(
                title="Recent Application Logs",
                log_group_names=[self.app_log_group.log_group_name],
                query_lines=[
                    "fields @timestamp, @message",
                    "sort @timestamp desc",
                    "limit 20",
                ],
                width=12,
                height=6,
            ),
            cloudwatch.LogQueryWidget(
                title="Recent Agent Logs",
                log_group_names=[self.agent_log_group.log_group_name],
                query_lines=[
                    "fields @timestamp, @message",
                    "sort @timestamp desc",
                    "limit 20",
                ],
                width=12,
                height=6,
            ),
        )

        # Output log group names
        CfnOutput(
            self,
            "AppLogGroupName",
            value=self.app_log_group.log_group_name,
            description="CloudWatch log group for application logs",
            export_name="Neo4jWorkshopAppLogGroup",
        )

        CfnOutput(
            self,
            "AgentLogGroupName",
            value=self.agent_log_group.log_group_name,
            description="CloudWatch log group for Bedrock agent logs",
            export_name="Neo4jWorkshopAgentLogGroup",
        )

        CfnOutput(
            self,
            "DashboardUrl",
            value=f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.dashboard.dashboard_name}",
            description="URL to the CloudWatch dashboard",
        )
