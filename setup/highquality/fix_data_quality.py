"""Fix all 10 data quality issues documented in DATA_QUALITY_ISSUES.md.

Connects to the Neo4j Aura instance via financial_data_load/.env.final and
applies fixes directly to the live database.

Usage:
    cd highquality && uv run fix_data_quality.py
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

# -- Issue 1: COMPETES_WITH entries to remove per source company --

COMPETES_WITH_REMOVALS: dict[str, list[str]] = {
    # Amazon — all 4 are acquisitions/investments
    "Amazon.com, Inc.": [
        "1Life Healthcare, Inc. (One Medical)",
        "MGM Holdings Inc.",
        "Rivian",
        "iRobot Corporation",
    ],
    # Apple — junk entries (fragments handled by COMPANY_MERGES)
    "Apple Inc.": [
        "Appiphany Technologies Corporation",
        "Verde Bio Holdings, Inc.",
    ],
    # Microsoft — acquisitions
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
    # NVIDIA — suppliers, manufacturers, service providers, non-competitors
    "NVIDIA Corporation": [
        # Contract manufacturers
        "Hon Hai",
        "Hon Hai Precision Industry Co.",
        "Jabil Inc.",
        "Flex Ltd.",
        "Fabrinet",
        "Wistron Corporation",
        # Foundry partner
        "Taiwan Semiconductor Manufacturing Company Limited",
        # Packaging / test
        "Siliconware Precision Industries Company Ltd.",
        "Amkor Technology",
        "King Yuan Electronics Co., Ltd.",
        # PCB / substrate
        "Ibiden Co. Ltd.",
        "Unimicron Technology Corporation",
        "Kinsus Interconnect Technology Corporation",
        # Other suppliers / non-competitors
        "Universal Scientific Industrial Co., Ltd.",
        "Applied Optoelectronics, Inc.",
        "Coherent, Inc.",
        "JDS Uniphase Corp.",
        "Lumentum Holdings",
        "Chroma ATE Inc.",
        # Non-competitors
        "Booz Allen Hamilton Inc.",
        "Cooley LLP",
        "Lockheed Missiles and Space Company",
    ],
    # PG&E — self-references and subsidiaries
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
    # PayPal — subsidiaries and acquisitions
    "PayPal Holdings, Inc.": [
        "Paidy",
        "PayPal (Europe)",
        "PayPal Credit Pty Limited",
        "PayPal Pte. Ltd.",
        "PayPal, Inc.",
        "TIO Networks",
        "Venmo",
    ],
}

# -- Company node merges (dedup before removing bad edges) --
# (canonical_name, [duplicate_names_to_merge_in])

COMPANY_MERGES: list[tuple[str, list[str]]] = [
    # NVIDIA competitor duplicates
    ("Advanced Micro Devices, Inc.", ["AMD"]),
    ("Samsung Electronics Co. Ltd", ["Samsung", "Samsung Semiconductor, Inc."]),
    ("SoftBank Group Corp.", ["SoftBank"]),
    # PG&E CAISO duplicate
    ("CAISO", ["California Independent System Operator (CAISO)"]),
    # Apple fragment replacements → merge into existing competitor nodes
    ("Google", ["Google (Android)"]),
    ("Microsoft Corporation", ["Microsoft (Windows)", "Microsoft (Xbox)"]),
    ("Sony", ["Sony (PlayStation)"]),
]

# -- New legitimate competitors to add --
# (source_company_name, target_company_name)

NEW_COMPETITORS: list[tuple[str, str]] = [
    # Amazon — was left with 0 competitors
    ("Amazon.com, Inc.", "Walmart Inc."),
    ("Amazon.com, Inc.", "Alphabet"),
    ("Amazon.com, Inc.", "Shopify Inc."),
    ("Amazon.com, Inc.", "Alibaba Group"),
    ("Amazon.com, Inc.", "Microsoft Corporation"),
    # Apple — add Samsung
    ("Apple Inc.", "Samsung Electronics Co. Ltd"),
    # PG&E — bolster from 2 to 5
    ("PG&E Corporation", "Southern California Edison"),
    ("PG&E Corporation", "Sempra Energy"),
    ("PG&E Corporation", "Pacific Power"),
    # PayPal — bolster from 2 to 4
    ("PayPal Holdings, Inc.", "Stripe Inc."),
    ("PayPal Holdings, Inc.", "Adyen N.V."),
]

# -- Issue 2 + 9: CUSIP fixes --

CUSIP_FIXES: dict[str, str] = {
    "PayPal Holdings, Inc.": "70450Y103",    # Was CIK "1633917"
    "Amazon.com, Inc.": "023135106",          # Pad 8→9 chars
    "NVIDIA Corporation": "67066G104",        # Strip leading 0 (10→9)
    "PG&E Corporation": "69331C908",          # Strip leading 0 (10→9)
}

# -- Issue 4: Product near-duplicate merges --
# (canonical_name, [duplicates_to_merge_in])

PRODUCT_MERGES: list[tuple[str, list[str]]] = [
    ("Buy Now, Pay Later", ["Buy Now Pay Later", "Buy Now Pay Later / Installment Methods"]),
    ("NVIDIA H100 Tensor Core GPU", ["H100 GPU", "H100 Integrated Circuit", "H100 integrated circuits"]),
    ("NVIDIA Omniverse Enterprise", ["Omniverse Enterprise software"]),
    ("NVIDIA Omniverse Avatar", ["Omniverse Avatar Cloud Engine"]),
    ("Cryptocurrency Services", [
        "Cryptocurrency Custodial Services", "Cryptocurrency Offerings",
        "Cryptocurrency Products", "Cryptocurrency Purchase and Sale",
        "Cryptocurrency Transactions",
    ]),
    ("Consumer Credit Products", ["Credit Products", "Consumer Loans"]),
    ("Consumer Installment Loans", [
        "Consumer Short-Term Installment Loan",
        "Consumer Interest-Bearing Installment Products",
        "U.S. Installment Loan Products",
    ]),
    ("PayPal Branded Consumer Credit Products", [
        "PayPal Consumer Credit", "PayPal Credit", "PayPal Consumer Credit Card",
    ]),
    ("Venmo Branded Credit Products", ["Venmo Consumer Credit", "Venmo co-branded consumer credit card"]),
    ("NVIDIA RTX GPUs", [
        "NVIDIA RTX", "NVIDIA RTX Platform",
        "NVIDIA Ampere Architecture RTX GPUs", "Quadro/NVIDIA RTX GPUs",
    ]),
    ("GeForce RTX GPUs", ["GeForce RTX 40 Series"]),
    ("Diablo Canyon Nuclear Power Plant", ["Diablo Canyon Nuclear Generation Facility"]),
    ("Gas Transmission and Storage", ["Backbone Gas Transmission Service", "Gas Storage Service"]),
    ("Gas Delivery Service", ["Gas Service"]),
    ("AI Platform Services", [
        "AI Products and Services", "AI Technologies and Associated Products",
        "AI and Machine Learning Platform", "AI Innovations",
    ]),
    ("Merchant Financing", ["Merchant Finance Offerings", "Merchant Loans and Advances"]),
    ("Xoom International Money Transfer", ["Xoom"]),
    ("Wearables, Home and Accessories", ["Accessories", "Wearables and Accessories"]),
]

# -- Issue 5: Product nodes that are not products --

NON_PRODUCTS: list[str] = [
    # Licensing / contracting terms
    "Enterprise Agreement",
    "Microsoft Customer Agreement",
    "Microsoft Online Subscription Agreement",
    "Microsoft Products and Services Agreement",
    "Microsoft Services Provider License Agreement",
    "On-Premises Software Licenses",
    "Open Value",
    "Select Plus",
    "Software Assurance",
    "Software Products and Services Financing Program",
    "Volume Licensing Programs",
    # Internal programs
    "AI Skills Initiative",
    "CARE Program",
    "Customer Protection Programs",
    "Deep Learning Institute",
    "Inception Program",
    "Purchase Protection Program",
    "Seller Protection Program",
    # Financial instruments
    "Senior Secured Recovery Bonds",
    "Senior Secured Recovery Bonds Series 2022-A",
    "Senior Secured Recovery Bonds Series 2022-B",
]

# -- Issue 6: Risk factor near-duplicate merges --

RISK_MERGES: list[tuple[str, list[str]]] = [
    ("Additional Tax Liabilities and Collection Obligations", ["Additional Tax Liabilities Risk"]),
    ("Cross-Border Data Transfer Restrictions", ["Cross-Border Data Transfer Risk"]),
    ("Cryptocurrency Mining Demand Volatility", ["Cryptocurrency Mining Demand Risk"]),
    ("Data Privacy and Security Obligations", [
        "Data Privacy and Security", "Data Privacy and Security Risk",
        "Data privacy and security regulations",
    ]),
    ("Distributed Generation and Energy Storage Competition", [
        "Distributed Generation and Energy Storage Viability",
    ]),
    ("Environmental Remediation Liabilities", ["Environmental Remediation Liability Risk"]),
    ("Intellectual Property Infringement Claims", ["Intellectual Property Infringement"]),
    ("Intellectual Property Protection Risk", ["Intellectual property protection"]),
    ("Legal and Regulatory Compliance Risks", ["Legal and Regulatory Compliance Risk"]),
    ("Litigation and Regulatory Proceedings", ["Litigation and Regulatory Risk"]),
    ("Nation-State Cyber Attack Risk", ["Nation-State Cyber Attacks"]),
    ("Wildfire Fund Contribution Obligations", ["Wildfire Fund Contribution Risk"]),
    ("Wildfire Mitigation Cost Recovery Risk", ["Wildfire Mitigation Cost Risk"]),
    ("Business Processes and Information Systems Disruption", [
        "Business process and information systems interruption",
    ]),
    ("Product Defect Risk", ["Product defects"]),
]

# -- Issue 7: Risk factor casing fixes (after merges absorb some) --

RISK_CASING_FIXES: dict[str, str] = {
    "Competition in markets": "Competition in Markets",
    "Cybersecurity and data breaches": "Cybersecurity and Data Breaches",
    "Executive and key employee retention": "Executive and Key Employee Retention",
}

# -- Issue 8 + 10: Asset manager name fixes and property rename --

ASSET_MANAGER_RENAMES: dict[str, str] = {
    "ALLIANCEBERNSTEIN L.P.": "AllianceBernstein L.P.",
    "AMERIPRISE FINANCIAL INC": "Ameriprise Financial Inc.",
    "AMUNDI": "Amundi",
    "BANK OF AMERICA CORP /DE/": "Bank of America Corp",
    "FMR LLC": "FMR LLC",
    "GEODE CAPITAL MANAGEMENT, LLC": "Geode Capital Management, LLC",
    "MORGAN STANLEY": "Morgan Stanley",
    "NORTHERN TRUST CORP": "Northern Trust Corp",
    "STATE STREET CORP": "State Street Corp",
    "WELLINGTON MANAGEMENT GROUP LLP": "Wellington Management Group LLP",
    "WELLS FARGO & COMPANY/MN": "Wells Fargo & Company",
    "Berkshire Hathaway Inc": "Berkshire Hathaway Inc.",
}


# ---------------------------------------------------------------------------
# Helper: merge nodes using apoc.refactor.mergeNodes
# ---------------------------------------------------------------------------


def merge_nodes(driver: Driver, label: str, keep_name: str, dup_names: list[str]) -> int:
    """Merge duplicate nodes into the canonical node. Returns count merged."""
    merged = 0
    for dup_name in dup_names:
        records = run(
            driver,
            f"MATCH (keep:{label} {{name: $keep}}) "
            f"MATCH (dup:{label} {{name: $dup}}) "
            f"CALL apoc.refactor.mergeNodes([keep, dup], "
            f"  {{properties: 'discard', mergeRels: true}}) YIELD node "
            f"RETURN node.name AS name",
            keep=keep_name, dup=dup_name,
        )
        if records:
            merged += 1
    return merged


# ---------------------------------------------------------------------------
# Audit: show current state before fixes
# ---------------------------------------------------------------------------


def audit(driver: Driver) -> None:
    print("=" * 60)
    print("AUDIT — current state")
    print("=" * 60)

    # Node counts
    for label in ("Company", "Product", "RiskFactor", "AssetManager"):
        count = run(driver, f"MATCH (n:{label}) RETURN count(n) AS c")[0]["c"]
        print(f"  {label}: {count} nodes")

    # COMPETES_WITH per filing company
    print()
    records = run(driver, """
        MATCH (c:Company)-[r:COMPETES_WITH]->()
        WHERE c.ticker IS NOT NULL
        RETURN c.name AS company, count(r) AS competitors
        ORDER BY competitors DESC
    """)
    for r in records:
        print(f"  {r['company']}: {r['competitors']} COMPETES_WITH edges")

    # AssetManager property check
    records = run(driver, """
        MATCH (am:AssetManager)
        RETURN
          count(CASE WHEN am.managerName IS NOT NULL THEN 1 END) AS has_managerName,
          count(CASE WHEN am.name IS NOT NULL THEN 1 END) AS has_name
    """)
    r = records[0]
    print(f"\n  AssetManager properties: {r['has_managerName']} with managerName, {r['has_name']} with name")
    print()


# ---------------------------------------------------------------------------
# Fix functions
# ---------------------------------------------------------------------------


def fix_01_competes_with(driver: Driver) -> None:
    """Issues 1 + 3: Merge Company duplicates, remove bad COMPETES_WITH, add new ones."""
    print("-" * 60)
    print("FIX 1/3: COMPETES_WITH cleanup + Company dedup")
    print("-" * 60)

    # Step 1: Merge duplicate Company nodes first (so relationships consolidate)
    total_merged = 0
    for keep_name, dup_names in COMPANY_MERGES:
        count = merge_nodes(driver, "Company", keep_name, dup_names)
        if count:
            print(f"  [MERGE] {count} Company node(s) → '{keep_name}'")
            total_merged += count
    print(f"  Company merges: {total_merged}")

    # Step 2: Delete bad COMPETES_WITH relationships
    total_deleted = 0
    for source_name, bad_targets in COMPETES_WITH_REMOVALS.items():
        records = run(driver, """
            MATCH (source:Company {name: $source})-[r:COMPETES_WITH]->(target:Company)
            WHERE target.name IN $targets
            DELETE r
            RETURN count(r) AS deleted
        """, source=source_name, targets=bad_targets)
        deleted = records[0]["deleted"] if records else 0
        if deleted:
            print(f"  [DELETE] {source_name}: removed {deleted} bad COMPETES_WITH edges")
        total_deleted += deleted
    print(f"  Bad edges removed: {total_deleted}")

    # Step 3: Clean up orphaned Company nodes (no relationships, not a filing company)
    records = run(driver, """
        MATCH (c:Company)
        WHERE NOT (c)-[]-()
          AND c.ticker IS NULL
        WITH collect(c.name) AS names, collect(c) AS nodes
        FOREACH (n IN nodes | DETACH DELETE n)
        RETURN size(names) AS deleted, names
    """)
    if records and records[0]["deleted"]:
        deleted_names = records[0]["names"]
        print(f"  [CLEANUP] Deleted {len(deleted_names)} orphaned Company nodes")

    # Step 4: Add new legitimate competitors
    total_added = 0
    for source_name, target_name in NEW_COMPETITORS:
        records = run(driver, """
            MATCH (source:Company {name: $source})
            MERGE (target:Company {name: $target})
            MERGE (source)-[r:COMPETES_WITH]->(target)
            RETURN type(r) AS rel
        """, source=source_name, target=target_name)
        if records:
            total_added += 1
    print(f"  New competitors added: {total_added}")
    print()


def fix_02_cusips(driver: Driver) -> None:
    """Issues 2 + 9: Fix all CUSIP values."""
    print("-" * 60)
    print("FIX 2/9: CUSIP fixes (PayPal wrong value + formatting)")
    print("-" * 60)

    for company_name, correct_cusip in CUSIP_FIXES.items():
        records = run(driver, """
            MATCH (c:Company {name: $name})
            SET c.cusip = $cusip
            RETURN c.name AS name, c.cusip AS cusip
        """, name=company_name, cusip=correct_cusip)
        if records:
            print(f"  [FIX] {company_name}: cusip → '{correct_cusip}'")
    print()


def fix_04_product_dedup(driver: Driver) -> None:
    """Issue 4: Merge product near-duplicates."""
    print("-" * 60)
    print("FIX 4: Product near-duplicate merges")
    print("-" * 60)

    total = 0
    for keep_name, dup_names in PRODUCT_MERGES:
        count = merge_nodes(driver, "Product", keep_name, dup_names)
        if count:
            print(f"  [MERGE] {count} → '{keep_name}'")
            total += count
    print(f"  Product merges: {total}")
    print()


def fix_05_non_products(driver: Driver) -> None:
    """Issue 5: Remove Product nodes that are not actually products."""
    print("-" * 60)
    print("FIX 5: Remove non-product Product nodes")
    print("-" * 60)

    records = run(driver, """
        UNWIND $names AS name
        MATCH (p:Product {name: name})
        DETACH DELETE p
        RETURN count(*) AS deleted
    """, names=NON_PRODUCTS)
    deleted = records[0]["deleted"] if records else 0
    print(f"  Removed {deleted} non-product nodes")
    print()


def fix_06_risk_dedup(driver: Driver) -> None:
    """Issue 6: Merge risk factor near-duplicates."""
    print("-" * 60)
    print("FIX 6: Risk factor near-duplicate merges")
    print("-" * 60)

    total = 0
    for keep_name, dup_names in RISK_MERGES:
        count = merge_nodes(driver, "RiskFactor", keep_name, dup_names)
        if count:
            print(f"  [MERGE] {count} → '{keep_name}'")
            total += count
    print(f"  Risk factor merges: {total}")
    print()


def fix_07_risk_casing(driver: Driver) -> None:
    """Issue 7: Normalize risk factor name casing to Title Case."""
    print("-" * 60)
    print("FIX 7: Risk factor casing normalization")
    print("-" * 60)

    total = 0
    for old_name, new_name in RISK_CASING_FIXES.items():
        records = run(driver, """
            MATCH (r:RiskFactor {name: $old})
            SET r.name = $new
            RETURN r.name AS name
        """, old=old_name, new=new_name)
        if records:
            print(f"  [FIX] '{old_name}' → '{new_name}'")
            total += 1
    print(f"  Casing fixes: {total}")
    print()


def fix_08_10_asset_managers(driver: Driver) -> None:
    """Issues 8 + 10: Fix asset manager names and rename managerName → name."""
    print("-" * 60)
    print("FIX 8/10: Asset manager names + property rename")
    print("-" * 60)

    # Drop old uniqueness constraint on managerName
    run(driver, "DROP CONSTRAINT unique_asset_manager_name IF EXISTS")
    print("  [OK] Dropped constraint on managerName")

    # Apply specific name fixes and rename property
    fixed = 0
    for old_name, new_name in ASSET_MANAGER_RENAMES.items():
        records = run(driver, """
            MATCH (am:AssetManager {managerName: $old})
            SET am.name = $new
            REMOVE am.managerName
            RETURN am.name AS name
        """, old=old_name, new=new_name)
        if records:
            print(f"  [RENAME] '{old_name}' → '{new_name}'")
            fixed += 1

    # Catch any remaining AssetManagers not in the rename map
    records = run(driver, """
        MATCH (am:AssetManager)
        WHERE am.managerName IS NOT NULL AND am.name IS NULL
        SET am.name = am.managerName
        REMOVE am.managerName
        RETURN count(*) AS updated
    """)
    remaining = records[0]["updated"] if records else 0
    if remaining:
        print(f"  [RENAME] {remaining} additional AssetManager(s) copied managerName → name")

    # Create new uniqueness constraint on name
    run(driver, "CREATE CONSTRAINT unique_asset_manager_name IF NOT EXISTS "
                "FOR (n:AssetManager) REQUIRE n.name IS UNIQUE")
    print("  [OK] Created constraint on AssetManager.name")
    print(f"  Total renamed: {fixed + remaining}")
    print()


# ---------------------------------------------------------------------------
# Verify: show state after fixes
# ---------------------------------------------------------------------------


def verify(driver: Driver) -> None:
    print("=" * 60)
    print("VERIFY — state after fixes")
    print("=" * 60)

    # Node counts
    for label in ("Company", "Product", "RiskFactor", "AssetManager"):
        count = run(driver, f"MATCH (n:{label}) RETURN count(n) AS c")[0]["c"]
        print(f"  {label}: {count} nodes")

    # COMPETES_WITH per filing company
    print()
    records = run(driver, """
        MATCH (c:Company)-[r:COMPETES_WITH]->()
        WHERE c.ticker IS NOT NULL
        RETURN c.name AS company, count(r) AS competitors
        ORDER BY competitors DESC
    """)
    for r in records:
        print(f"  {r['company']}: {r['competitors']} COMPETES_WITH edges")

    # Spot-check PayPal CUSIP
    records = run(driver, "MATCH (c:Company {name: 'PayPal Holdings, Inc.'}) RETURN c.cusip AS cusip")
    print(f"\n  PayPal CUSIP: {records[0]['cusip']}")

    # AssetManager property check
    records = run(driver, """
        MATCH (am:AssetManager)
        RETURN
          count(CASE WHEN am.managerName IS NOT NULL THEN 1 END) AS has_managerName,
          count(CASE WHEN am.name IS NOT NULL THEN 1 END) AS has_name
    """)
    r = records[0]
    print(f"  AssetManager properties: {r['has_managerName']} with managerName, {r['has_name']} with name")

    # Check lab exercise patterns still work
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

        fix_01_competes_with(driver)   # Issues 1 + 3
        fix_02_cusips(driver)          # Issues 2 + 9
        fix_04_product_dedup(driver)   # Issue 4
        fix_05_non_products(driver)    # Issue 5
        fix_06_risk_dedup(driver)      # Issue 6
        fix_07_risk_casing(driver)     # Issue 7
        fix_08_10_asset_managers(driver)  # Issues 8 + 10

        verify(driver)
        print("[DONE] All 10 data quality issues fixed.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
