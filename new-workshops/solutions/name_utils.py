"""
Company name normalization utility.

Provides hardcoded mappings to normalize variant company names
to a canonical form, resolving conflicts between CSV metadata
and LLM entity extraction.
"""

# Canonical company names mapped from CSV uppercase variants
# Maps: CSV_NAME -> LLM_EXPECTED_NAME
COMPANY_NAME_MAPPINGS = {
    # From Company_Filings.csv (10 companies)
    "AMAZON": "Amazon.com, Inc.",
    "NVIDIA CORPORATION": "NVIDIA Corporation",
    "APPLE INC": "Apple Inc.",
    "PAYPAL": "PayPal Holdings, Inc.",
    "INTEL CORP": "Intel Corporation",
    "AMERICAN INTL GROUP": "American International Group, Inc.",
    "PG&E CORP": "PG&E Corporation",
    "MCDONALDS CORP": "McDonald's Corporation",
    "MICROSOFT CORP": "Microsoft Corporation",
}


def normalize_company_name(name: str) -> str:
    """
    Normalize a company name to its canonical form.

    Args:
        name: Raw company name (any casing)

    Returns:
        Canonical company name, or original if no mapping exists
    """
    # Check for exact match first
    if name in COMPANY_NAME_MAPPINGS:
        return COMPANY_NAME_MAPPINGS[name]

    # Check uppercase version for case-insensitive matching
    upper_name = name.upper()
    if upper_name in COMPANY_NAME_MAPPINGS:
        return COMPANY_NAME_MAPPINGS[upper_name]

    # No mapping found - return original
    return name
