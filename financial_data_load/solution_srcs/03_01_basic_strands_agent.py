"""
Basic Strands Agent

This solution demonstrates a ReAct-style agent using the Strands Agents SDK
with BedrockModel and simple tool use.

Run with: uv run python main.py solutions <N>
"""

from datetime import datetime
from pathlib import Path

from strands import Agent, tool
from strands.models import BedrockModel

from config import BedrockConfig


# ---------------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------------

config = BedrockConfig()
MODEL_ID = config.model_id
REGION = config.region

print(f"Model:          {MODEL_ID}")
print(f"Region:         {REGION}")


# ---------------------------------------------------------------------------
# 2. Define Tools
# ---------------------------------------------------------------------------

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


tools = [get_current_time, add_numbers]
print(f"Defined {len(tools)} tools: get_current_time, add_numbers")


# ---------------------------------------------------------------------------
# 3. Initialize the Agent
# ---------------------------------------------------------------------------

bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    region_name=REGION,
    temperature=0,
)

agent = Agent(
    model=bedrock_model,
    system_prompt="You are a helpful assistant. Use tools when needed.",
    tools=tools,
)

print("Agent initialized!")


# ---------------------------------------------------------------------------
# 4. Run the Agent
# ---------------------------------------------------------------------------

def run_agent(question: str):
    """Run the agent with a question and display the response."""
    print(f"Question: {question}")
    print("-" * 50)

    response = agent(question)
    print(f"\nResponse:\n{response}")
    return response


# ---------------------------------------------------------------------------
# 5. Query with Sample Financial Data
# ---------------------------------------------------------------------------

def load_financial_data() -> str:
    """Load sample SEC financial filing data from Lab 3."""
    data_path = (
        Path(__file__).resolve().parent.parent.parent
        / "Lab_3_Intro_to_Bedrock_and_Agents"
        / "sample_financial_data.txt"
    )
    with open(data_path, "r") as f:
        return f.read().strip()


def ask_about_data(question: str, context: str):
    """Ask the agent a question with context."""
    prompt = f"""Based on this SEC 10-K filing information:

{context}

Question: {question}"""
    return run_agent(prompt)


# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------

def main():
    """Run demo queries."""
    # Test: Get current time
    run_agent("What is the current time?")
    print()

    # Test: Math calculation
    run_agent("What is 42 + 17?")
    print()

    # Test: Multiple tools
    run_agent("What time is it and what is 100 + 200?")
    print()

    # Load sample financial data and ask contextual questions
    financial_text = load_financial_data()
    lines = financial_text.split("\n")
    words = financial_text.split()
    print(f"Characters: {len(financial_text)}")
    print(f"Lines: {len(lines)}")
    print(f"Words: {len(words)}")
    print(f"Preview: {financial_text[:100]}...")
    print()

    ask_about_data(
        "What companies are mentioned and what are their key products?",
        financial_text,
    )
    print()

    ask_about_data(
        "What risk factors are mentioned and which companies face them?",
        financial_text,
    )


if __name__ == "__main__":
    main()
