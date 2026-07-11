#!/usr/bin/env python3
"""
Basic Strands Agent - AgentCore Runtime Deployment

A simple agent with time and math tools, deployed to AgentCore Runtime.
"""

import logging
import os
from datetime import datetime

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

SYSTEM_PROMPT = "You are a helpful assistant. Use the available tools when needed to answer questions."


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@app.entrypoint
async def invoke(payload: dict = None):
    """AgentCore Runtime handler."""
    if payload is None:
        payload = {}

    prompt = (
        payload.get("prompt")
        or payload.get("message")
        or payload.get("query")
        or payload.get("input")
    )

    if not prompt:
        yield {"type": "error", "error": "No prompt provided. Include 'prompt' in your request."}
        return

    logger.info(f"Query: {prompt[:100]}...")

    try:
        model = BedrockModel(
            model_id=MODEL_ID,
            region_name=AWS_REGION,
            temperature=0,
        )
        agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=[get_current_time, add_numbers],
        )

        response = agent(prompt)
        response_text = str(response)

        yield {"type": "chunk", "data": response_text}
        yield {"type": "complete"}

        logger.info("Request completed successfully")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        yield {"type": "error", "error": f"Error processing request: {str(e)}"}


if __name__ == "__main__":
    app.run(port=8080)
