"""Simple loader for sample SEC financial filing data."""

import os


def load_financial_data(filepath: str = None) -> str:
    """Load and return the sample financial data text.

    Reads from sample_financial_data.txt in the same directory as this module.
    """
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), "sample_financial_data.txt")
    with open(filepath, "r") as f:
        text = f.read().strip()
    return text


# Keep backward-compatible alias
load_company_data = load_financial_data


def print_info(text: str) -> None:
    """Print basic info about the text."""
    lines = text.split("\n")
    words = text.split()
    print(f"Characters: {len(text)}")
    print(f"Lines: {len(lines)}")
    print(f"Words: {len(words)}")
    print(f"Preview: {text[:100]}...")


if __name__ == "__main__":
    data = load_financial_data()
    print_info(data)
