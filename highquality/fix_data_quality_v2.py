"""Fix remaining data quality issues found during post-v1 audit.

Addresses:
  A. Fragment Company nodes still alive via FROM_CHUNK/FACES_RISK/REPORTS/OFFERS
  B. Non-filing companies with ticker/cusip/cik properties from pipeline
  C. Junk PARTNERS_WITH relationships
  D. Two more questionable NVIDIA competitors

Usage:
    cd highquality && uv run fix_data_quality_v2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import dotenv_values
from neo4j import Driver, GraphDatabase

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

ENV_FILE = Path(__file__).resolve().parent.parent / "financial_data_load" / ".env.final"

FILING_COMPANIES = {
    "Amazon.com, Inc.",
    "Apple Inc.",
    "Microsoft Corporation",
    "NVIDIA Corporation",
    "PG&E Corporation",
    "PayPal Holdings, Inc.",
}


def get_driver() -> Driver:
    if not ENV_FILE.exists():
        print(f"[FAIL] {ENV_FILE} not found")
        sys.exit(1)
    env = dotenv_values(ENV_FILE)
    uri = env["NEO4J_URI"]
    driver = GraphDatabase.driver(uri, auth=(env["NEO4J_USERNAME"], env["NEO4J_PASSWORD"]))
    driver.verify_connectivity()
    print(f"[OK] Connected to {uri}\n")
    return driver


def run(driver: Driver, cypher: str, **params) -> list:
    result = driver.execute_query(cypher, parameters_=params)
    return result.records


# ---------------------------------------------------------------------------
# Data definitions
# ---------------------------------------------------------------------------

# -- A. Fragment Company nodes to merge into their parent filing company --
# The pipeline created these as separate entities; their FACES_RISK, REPORTS,
# OFFERS relationships actually belong to the parent.

COMPANY_MERGE_INTO_PARENT: dict[str, list[str]] = {
    # PG&E variants → PG&E Corporation
    "PG&E Corporation": [
        "PG&E",
        "PG&E Recovery Funding LLC",
        "PG&E Utility",
        "PG&E Wildfire Recovery Funding LLC",
        "Pacific Gas and Electric (PG&E Utility)",
        "Pacific Gas and Electric (PG&E)",
        "Pacific Gas and Electric (PG&E) Utility",
        "Pacific Gas and Electric (The Utility)",
        "Pacific Gas and Electric (Utility)",
        "Pacific Gas and Electric Company",
        "Pacific Generation LLC",
    ],
    # PayPal subsidiaries → PayPal Holdings, Inc.
    "PayPal Holdings, Inc.": [
        "Paidy",
        "PayPal (Europe)",
        "PayPal Credit Pty Limited",
        "PayPal Pte. Ltd.",
        "PayPal, Inc.",
        "TIO Networks",
        "Venmo",
    ],
    # Microsoft acquisitions → Microsoft Corporation
    # Their FACES_RISK/OFFERS extracted from MSFT's 10-K belong to MSFT
    "Microsoft Corporation": [
        "Activision Blizzard, Inc.",
        "Bethesda Softworks LLC",
        "GitHub",
        "LinkedIn",
        "Microsoft Mobile Oy",
        "Nuance",
        "Nuance Communications, Inc.",
        "ZeniMax Media Inc.",
    ],
}

# -- A (cont). Company nodes to DETACH DELETE (noise, no value to merge) --

COMPANY_NODES_TO_DELETE: list[str] = [
    # Amazon acquisitions/investments (FROM_CHUNK only, except Rivian)
    "1Life Healthcare, Inc. (One Medical)",
    "MGM Holdings Inc.",
    "iRobot Corporation",
    # Apple junk
    "Appiphany Technologies Corporation",
    "Verde Bio Holdings, Inc.",
    # NVIDIA suppliers/manufacturers — all only have FROM_CHUNK
    "Amkor Technology",
    "Applied Optoelectronics, Inc.",
    "Booz Allen Hamilton Inc.",
    "Chroma ATE Inc.",
    "Coherent, Inc.",
    "Cooley LLP",
    "Fabrinet",
    "Flex Ltd.",
    "Hon Hai",
    "Hon Hai Precision Industry Co.",
    "Ibiden Co. Ltd.",
    "JDS Uniphase Corp.",
    "Jabil Inc.",
    "King Yuan Electronics Co., Ltd.",
    "Kinsus Interconnect Technology Corporation",
    "Lockheed Missiles and Space Company",
    "Lumentum Holdings",
    "Siliconware Precision Industries Company Ltd.",
    "Taiwan Semiconductor Manufacturing Company Limited",
    "Unimicron Technology Corporation",
    "Universal Scientific Industrial Co., Ltd.",
    "Wistron Corporation",
    # Other pipeline noise
    "Motorola Mobile",
    "McDonald's Corporation",
    "American International Group, Inc.",
]

# -- C. Junk PARTNERS_WITH relationships to delete --
# (source_name, target_name)

PARTNERS_WITH_TO_DELETE: list[tuple[str, str]] = [
    ("Alphabet", "Google"),                                          # self-reference
    ("Verde Bio Holdings, Inc.", "Appiphany Technologies Corporation"),  # junk
    ("Pacific Gas and Electric (PG&E)", "PG&E Recovery Funding LLC"),    # internal sub (will be merged)
    ("Pacific Gas and Electric (Utility)", "Pacific Generation LLC"),    # internal sub (will be merged)
    ("ZeniMax Media Inc.", "Bethesda Softworks LLC"),                    # both MS acquisitions (will be merged)
]

# -- D. Additional questionable NVIDIA competitors to remove --

NVIDIA_COMPETITORS_TO_REMOVE: list[str] = [
    "Omni Logistics, LLC",       # logistics company, not a chip competitor
    "Sun Microsystems, Inc.",    # defunct since 2010 (acquired by Oracle)
]


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def audit(driver: Driver) -> None:
    print("=" * 60)
    print("AUDIT — current state (pre-v2)")
    print("=" * 60)

    for label in ("Company", "Product", "RiskFactor", "AssetManager"):
        count = run(driver, f"MATCH (n:{label}) RETURN count(n) AS c")[0]["c"]
        print(f"  {label}: {count} nodes")

    print()
    records = run(driver, """
        MATCH (c:Company)-[r:COMPETES_WITH]->()
        WHERE c.ticker IS NOT NULL AND c.name IN $filing
        RETURN c.name AS company, count(r) AS competitors
        ORDER BY competitors DESC
    """, filing=list(FILING_COMPANIES))
    for r in records:
        print(f"  {r['company']}: {r['competitors']} COMPETES_WITH edges")

    records = run(driver, """
        MATCH (c:Company)
        WHERE c.ticker IS NOT NULL AND NOT c.name IN $filing
        RETURN count(c) AS c
    """, filing=list(FILING_COMPANIES))
    print(f"\n  Non-filing companies with ticker: {records[0]['c']}")

    records = run(driver, "MATCH ()-[r:PARTNERS_WITH]->() RETURN count(r) AS c")
    print(f"  PARTNERS_WITH edges: {records[0]['c']}")
    print()


# ---------------------------------------------------------------------------
# Fix functions
# ---------------------------------------------------------------------------


def fix_a_merge_fragments(driver: Driver) -> None:
    """Merge fragment Company nodes into their parent filing company."""
    print("-" * 60)
    print("FIX A: Merge fragment Company nodes into parents")
    print("-" * 60)

    for parent_name, fragments in COMPANY_MERGE_INTO_PARENT.items():
        merged = 0
        for frag_name in fragments:
            records = run(driver, """
                MATCH (parent:Company {name: $parent})
                MATCH (frag:Company {name: $frag})
                CALL apoc.refactor.mergeNodes([parent, frag],
                    {properties: 'discard', mergeRels: true}) YIELD node
                RETURN node.name AS name
            """, parent=parent_name, frag=frag_name)
            if records:
                merged += 1
        if merged:
            print(f"  [MERGE] {merged} fragment(s) → '{parent_name}'")
    print()


def fix_a_delete_noise(driver: Driver) -> None:
    """DETACH DELETE Company nodes that are pure noise."""
    print("-" * 60)
    print("FIX A (cont): Delete noise Company nodes")
    print("-" * 60)

    records = run(driver, """
        UNWIND $names AS name
        MATCH (c:Company {name: name})
        DETACH DELETE c
        RETURN count(*) AS deleted
    """, names=COMPANY_NODES_TO_DELETE)
    deleted = records[0]["deleted"] if records else 0
    print(f"  Deleted {deleted} noise Company nodes")
    print()


def fix_b_strip_tickers(driver: Driver) -> None:
    """Remove ticker/cusip/cik from non-filing Company nodes."""
    print("-" * 60)
    print("FIX B: Strip pipeline-assigned ticker/cusip/cik from non-filing companies")
    print("-" * 60)

    records = run(driver, """
        MATCH (c:Company)
        WHERE c.ticker IS NOT NULL
          AND NOT c.name IN $filing
        REMOVE c.ticker, c.cusip, c.cik
        RETURN count(c) AS updated
    """, filing=list(FILING_COMPANIES))
    updated = records[0]["updated"] if records else 0
    print(f"  Stripped ticker from {updated} non-filing Company nodes")
    print()


def fix_c_partners_with(driver: Driver) -> None:
    """Delete junk PARTNERS_WITH relationships."""
    print("-" * 60)
    print("FIX C: Clean up PARTNERS_WITH noise")
    print("-" * 60)

    total = 0
    for source, target in PARTNERS_WITH_TO_DELETE:
        records = run(driver, """
            MATCH (s:Company {name: $source})-[r:PARTNERS_WITH]->(t:Company {name: $target})
            DELETE r
            RETURN count(r) AS deleted
        """, source=source, target=target)
        deleted = records[0]["deleted"] if records else 0
        if deleted:
            print(f"  [DELETE] {source} -> {target}")
            total += deleted

    # Also delete PARTNERS_WITH from Amazon to Rivian? No — that's legitimate.
    print(f"  Deleted {total} junk PARTNERS_WITH edges")

    # Clean up Rivian: keep PARTNERS_WITH from Amazon, but it's not a competitor
    # (already not in COMPETES_WITH, so nothing to do)
    print()


def fix_d_nvidia_competitors(driver: Driver) -> None:
    """Remove remaining questionable NVIDIA competitors."""
    print("-" * 60)
    print("FIX D: Remove questionable NVIDIA competitors")
    print("-" * 60)

    records = run(driver, """
        MATCH (nvidia:Company {name: "NVIDIA Corporation"})-[r:COMPETES_WITH]->(t:Company)
        WHERE t.name IN $targets
        DELETE r
        RETURN collect(t.name) AS removed
    """, targets=NVIDIA_COMPETITORS_TO_REMOVE)
    removed = records[0]["removed"] if records else []
    for name in removed:
        print(f"  [DELETE] NVIDIA -> {name}")
    print(f"  Removed {len(removed)} edges")
    print()


def fix_e_cleanup_orphans(driver: Driver) -> None:
    """Final pass: delete any Company nodes with no remaining relationships."""
    print("-" * 60)
    print("FIX E: Final orphan cleanup")
    print("-" * 60)

    records = run(driver, """
        MATCH (c:Company)
        WHERE NOT (c)-[]-()
          AND NOT c.name IN $filing
        WITH collect(c.name) AS names, collect(c) AS nodes
        FOREACH (n IN nodes | DETACH DELETE n)
        RETURN names
    """, filing=list(FILING_COMPANIES))
    names = records[0]["names"] if records and records[0]["names"] else []
    if names:
        for n in sorted(names):
            print(f"  [DELETE] {n}")
    print(f"  Deleted {len(names)} orphaned Company nodes")
    print()


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------


def verify(driver: Driver) -> None:
    print("=" * 60)
    print("VERIFY — state after v2 fixes")
    print("=" * 60)

    for label in ("Company", "Product", "RiskFactor", "AssetManager"):
        count = run(driver, f"MATCH (n:{label}) RETURN count(n) AS c")[0]["c"]
        print(f"  {label}: {count} nodes")

    print()
    records = run(driver, """
        MATCH (c:Company)-[r:COMPETES_WITH]->()
        WHERE c.name IN $filing
        RETURN c.name AS company, count(r) AS competitors
        ORDER BY competitors DESC
    """, filing=list(FILING_COMPANIES))
    for r in records:
        print(f"  {r['company']}: {r['competitors']} COMPETES_WITH edges")

    # No more non-filing companies with tickers
    records = run(driver, """
        MATCH (c:Company)
        WHERE c.ticker IS NOT NULL AND NOT c.name IN $filing
        RETURN count(c) AS c
    """, filing=list(FILING_COMPANIES))
    print(f"\n  Non-filing companies with ticker: {records[0]['c']}")

    # PARTNERS_WITH
    records = run(driver, """
        MATCH (s:Company)-[:PARTNERS_WITH]->(t:Company)
        RETURN s.name AS source, t.name AS target
    """)
    print(f"  PARTNERS_WITH edges: {len(records)}")
    for r in records:
        print(f"    {r['source']} -> {r['target']}")

    # Company count breakdown
    records = run(driver, """
        MATCH (c:Company)
        RETURN
          count(CASE WHEN c.name IN $filing THEN 1 END) AS filing,
          count(CASE WHEN NOT c.name IN $filing THEN 1 END) AS mentioned
    """, filing=list(FILING_COMPANIES))
    r = records[0]
    print(f"\n  Companies: {r['filing']} filing + {r['mentioned']} mentioned = {r['filing'] + r['mentioned']} total")

    # Lab exercise checks
    print("\n  Lab exercise pattern checks:")
    records = run(driver, """
        MATCH (am:AssetManager)-[:OWNS]->(c:Company)-[:FACES_RISK]->(rf:RiskFactor)
        RETURN count(*) AS paths
    """)
    print(f"    AssetManager-OWNS->Company-FACES_RISK->RiskFactor: {records[0]['paths']} paths")

    records = run(driver, """
        MATCH (c:Company)-[:COMPETES_WITH]->(c2:Company)
        RETURN count(*) AS edges
    """)
    print(f"    Company-COMPETES_WITH->Company: {records[0]['edges']} edges")

    records = run(driver, """
        MATCH (c:Company)-[:OFFERS]->(p:Product)
        RETURN count(*) AS edges
    """)
    print(f"    Company-OFFERS->Product: {records[0]['edges']} edges")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    driver = get_driver()
    try:
        audit(driver)

        fix_c_partners_with(driver)      # C: before merges so we don't carry noise
        fix_a_merge_fragments(driver)     # A: merge fragments into parents
        fix_a_delete_noise(driver)        # A: delete pure-noise nodes
        fix_b_strip_tickers(driver)       # B: strip tickers from non-filing companies
        fix_d_nvidia_competitors(driver)  # D: remove questionable competitors
        fix_e_cleanup_orphans(driver)     # E: final orphan sweep

        verify(driver)
        print("[DONE] All v2 fixes applied.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
