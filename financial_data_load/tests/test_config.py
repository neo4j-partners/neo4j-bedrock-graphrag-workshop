"""Regression tests for Bedrock LLM configuration."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from src import config


class BedrockLlmFactoryTests(TestCase):
    """Ensure configured model IDs reach BedrockLLM's model_name argument."""

    model_id = "us.anthropic.claude-sonnet-4-6"
    region = "us-east-1"

    def _agent_config(self) -> SimpleNamespace:
        return SimpleNamespace(
            llm_model_id=self.model_id,
            aws_region=self.region,
        )

    def test_get_llm_uses_configured_model_name(self) -> None:
        with (
            patch("src.config.AgentConfig", return_value=self._agent_config()),
            patch(
                "neo4j_graphrag.llm.bedrock_llm.boto3.client",
                return_value=Mock(),
            ) as boto_client,
        ):
            llm = config.get_llm()

        self.assertEqual(llm.model_name, self.model_id)
        boto_client.assert_called_once_with(
            "bedrock-runtime", region_name=self.region
        )

    def test_deterministic_llm_uses_configured_model_name(self) -> None:
        with (
            patch("src.config.AgentConfig", return_value=self._agent_config()),
            patch(
                "neo4j_graphrag.llm.bedrock_llm.boto3.client",
                return_value=Mock(),
            ) as boto_client,
        ):
            llm = config.get_llm_deterministic()

        self.assertEqual(llm.model_name, self.model_id)
        self.assertEqual(llm.model_params, {"temperature": 0})
        boto_client.assert_called_once_with(
            "bedrock-runtime", region_name=self.region
        )
