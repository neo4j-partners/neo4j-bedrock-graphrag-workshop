"""Export a curated seed-data slice from the live (quality-fixed) Neo4j database.

Two modes:
    --discover   Print all products and risk factors for human review.
    (default)    Export curated CSVs to setup/seed-data/.

Usage:
    cd highquality
    uv run export_slice.py --discover   # first pass: review candidates
    uv run export_slice.py              # export curated slice
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from dotenv import dotenv_values
from neo4j import Driver, GraphDatabase

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
EXPORT_DIR = ROOT / "setup" / "seed-data"
ENV_FILE = ROOT / "financial_data_load" / ".env"

FILING_COMPANIES = [
    "Amazon.com, Inc.",
    "Apple Inc.",
    "Microsoft Corporation",
    "NVIDIA Corporation",
    "PG&E Corporation",
    "PayPal Holdings, Inc.",
]

# ---------------------------------------------------------------------------
# Curated product lists (populated after --discover review)
# ---------------------------------------------------------------------------

CURATED_PRODUCTS: dict[str, list[str]] = {
    "Amazon.com, Inc.": [
        "AWS",
        "Amazon Prime",
        "Amazon Stores",
        "Blink",
        "Fire TV",
        "Fire Tablet",
        "Fulfillment by Amazon",
        "Kindle",
        "Ring",
        "eero",
    ],
    "Apple Inc.": [
        "AirPods",
        "App Store",
        "Apple Arcade",
        "Apple Music",
        "Apple Pay",
        "Apple TV+",
        "Apple Vision Pro",
        "Apple Watch",
        "AppleCare",
        "HomePod",
        "Mac",
        "Wearables, Home and Accessories",
        "iOS 17",
        "iPad",
        "iPhone",
        "macOS Sonoma",
    ],
    "Microsoft Corporation": [
        "Azure",
        "Bing",
        "Dynamics 365",
        "GitHub",
        "GitHub Copilot",
        "HoloLens",
        "LinkedIn",
        "Microsoft 365",
        "Microsoft 365 Copilot",
        "Microsoft Defender for Endpoint",
        "Microsoft Edge",
        "Microsoft Fabric",
        "Microsoft Office",
        "Microsoft Power Platform",
        "Microsoft Teams",
        "OneDrive",
        "Outlook",
        "SharePoint",
        "Surface",
        "Visual Studio",
        "Windows",
        "Xbox",
    ],
    "NVIDIA Corporation": [
        "CUDA",
        "DGX Systems",
        "DRIVE",
        "GeForce GPU",
        "GeForce NOW",
        "GeForce RTX GPUs",
        "Grace CPU",
        "InfiniBand Network Adapters and Switches",
        "Jetson for robotics and embedded platforms",
        "NVIDIA AI Enterprise",
        "NVIDIA BlueField DPU",
        "NVIDIA DGX Cloud",
        "NVIDIA DLSS",
        "NVIDIA H100 Tensor Core GPU",
        "NVIDIA Omniverse",
        "NVIDIA RTX GPUs",
        "NVIDIA Spectrum-4 Networking Platform",
        "Networking Products",
        "Professional Visualization Products",
    ],
    "PG&E Corporation": [
        "Bundled Electric Service",
        "Bundled Gas Sales",
        "Diablo Canyon Nuclear Power Plant",
        "Elkhorn Battery Energy Storage System",
        "Enhanced Powerline Safety Settings (EPSS)",
        "Gas Delivery Service",
        "Gas Transmission and Storage",
        "Geothermal Energy",
        "Metering Services",
        "Transmission Services",
    ],
    "PayPal Holdings, Inc.": [
        "Braintree",
        "Buy Now, Pay Later",
        "Consumer Credit Products",
        "Cryptocurrency Services",
        "Hyperwallet",
        "Merchant Financing",
        "Paidy",
        "PayPal",
        "PayPal Digital Wallet",
        "PayPal Honey",
        "PayPal Zettle",
        "Venmo",
        "Venmo Digital Wallet",
        "Xoom International Money Transfer",
    ],
}

# ---------------------------------------------------------------------------
# Curated risk factor list (populated after --discover review)
# ---------------------------------------------------------------------------

CURATED_RISKS: list[str] = [
    # --- Shared across 4-6 companies (cross-cutting) ---
    "Interest Rate Risk",
    "Foreign Currency Exchange Rate Risk",
    "Intense Competition",
    "Climate Change Risk",
    "International Operations Risk",
    "Regulatory Risk",
    # --- Shared across 3 companies ---
    "Additional Tax Liabilities and Collection Obligations",
    "COVID-19 Pandemic Impact",
    "Competition Risk",
    "Cybersecurity Threats",
    "Data Protection and Privacy Law Compliance Risk",
    "Indebtedness Risk",
    "Insufficient Insurance Coverage",
    "Regulatory Compliance Risk",
    "Supply Chain Constraints",
    "Supply Chain Disruption",
    "Uncertain Tax Positions",
    # --- Shared across 2 companies ---
    "AI Regulation Risk",
    "Acquisition and Investment Risk",
    "Adverse Economic Conditions",
    "Cyberattacks and Security Vulnerabilities",
    "Demand Forecasting Risk",
    "ESG Reporting and Compliance Risk",
    "GDPR and CCPA Compliance Risk",
    "Geopolitical Risk",
    "Intellectual Property Protection Risk",
    "Intellectual Property Rights Risk",
    "Key Personnel Retention Risk",
    "Macroeconomic Conditions",
    "Nation-State Cyber Attack Risk",
    "Reputation and Brand Damage Risk",
    "Talent Attraction and Retention",
    "Third-Party Developer Dependency",
    # --- Distinctive: Amazon ---
    "AWS Revenue Growth Impact",
    "Fulfillment Network Expansion Costs",
    # --- Distinctive: Apple ---
    "App Store Regulatory Risk",
    "Supply Chain Concentration Risk",
    "Single Product Concentration Risk",
    # --- Distinctive: Microsoft ---
    "AI Development and Use Risk",
    "Cloud Execution and Competitive Risk",
    "Datacenter Capacity Constraints",
    "Open Source Competition",
    # --- Distinctive: NVIDIA ---
    "Export Control Restrictions",
    "China Export Restrictions on Semiconductors",
    "Cryptocurrency Mining Demand Volatility",
    "Fabless Manufacturing Dependency",
    "Customer Concentration Risk",
    # --- Distinctive: PG&E ---
    "Wildfire Liability Risk",
    "Aging Infrastructure Risk",
    "Nuclear Decommissioning Cost Risk",
    "Inverse Condemnation Liability",
    "Diablo Canyon Extended Operations Risk",
    # --- Distinctive: PayPal ---
    "Fraud Risk",
    "Anti-Money Laundering Compliance Risk",
    "Cryptocurrency Regulation Risk",
    "Account Holder Default Risk",
    "Transaction and Credit Losses",
]

# ---------------------------------------------------------------------------
# Hardcoded partner relationships
# ---------------------------------------------------------------------------

PARTNER_EDGES: list[tuple[str, str]] = [
    ("NVIDIA Corporation", "TSMC"),
    ("Amazon.com, Inc.", "Rivian"),
    ("Apple Inc.", "TSMC"),
    ("Microsoft Corporation", "OpenAI"),
    ("PG&E Corporation", "California ISO"),
]

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------


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
# Helpers
# ---------------------------------------------------------------------------


def write_csv(filename: str, headers: list[str], rows: list[dict]) -> None:
    path = EXPORT_DIR / filename
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {filename}: {len(rows)} rows")


# ---------------------------------------------------------------------------
# Discover mode
# ---------------------------------------------------------------------------


def discover_products(driver: Driver) -> None:
    """Print all products per filing company for human review."""
    print("=" * 70)
    print("PRODUCTS BY COMPANY")
    print("=" * 70)

    records = run(driver, """
        MATCH (c:Company)-[:OFFERS]->(p:Product)
        WHERE c.name IN $companies
        RETURN c.name AS company, p.name AS product
        ORDER BY c.name, p.name
    """, companies=FILING_COMPANIES)

    current_company = None
    count = 0
    for r in records:
        if r["company"] != current_company:
            if current_company:
                print(f"    ({count} products)\n")
            current_company = r["company"]
            count = 0
            print(f"\n  {current_company}:")
        print(f"    - {r['product']}")
        count += 1
    if current_company:
        print(f"    ({count} products)\n")


def discover_risk_factors(driver: Driver) -> None:
    """Print risk factors grouped by shared (2+ companies) vs single-company."""
    print("=" * 70)
    print("RISK FACTORS — SHARED (2+ companies)")
    print("=" * 70)

    records = run(driver, """
        MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
        WHERE c.name IN $companies
        WITH r, collect(c.name) AS companies, count(c) AS cnt
        WHERE cnt >= 2
        RETURN r.name AS name, companies, cnt
        ORDER BY cnt DESC, r.name
    """, companies=FILING_COMPANIES)

    for r in records:
        companies_str = ", ".join(sorted(r["companies"]))
        print(f"  [{r['cnt']}] {r['name']}")
        print(f"      -> {companies_str}")
    print(f"\n  Total shared: {len(records)}\n")

    print("=" * 70)
    print("RISK FACTORS — SINGLE COMPANY")
    print("=" * 70)

    records = run(driver, """
        MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
        WHERE c.name IN $companies
        WITH r, collect(c.name) AS companies, count(c) AS cnt
        WHERE cnt = 1
        RETURN r.name AS name, companies[0] AS company
        ORDER BY company, r.name
    """, companies=FILING_COMPANIES)

    current_company = None
    count = 0
    for r in records:
        if r["company"] != current_company:
            if current_company:
                print(f"    ({count} risk factors)\n")
            current_company = r["company"]
            count = 0
            print(f"\n  {current_company}:")
        print(f"    - {r['name']}")
        count += 1
    if current_company:
        print(f"    ({count} risk factors)\n")


def discover_competitors(driver: Driver) -> None:
    """Print current competitor edges per filing company."""
    print("=" * 70)
    print("COMPETITORS BY COMPANY")
    print("=" * 70)

    records = run(driver, """
        MATCH (a:Company)-[:COMPETES_WITH]->(b:Company)
        WHERE a.name IN $companies
        RETURN a.name AS source, b.name AS target
        ORDER BY a.name, b.name
    """, companies=FILING_COMPANIES)

    current_company = None
    count = 0
    for r in records:
        if r["source"] != current_company:
            if current_company:
                print(f"    ({count} competitors)\n")
            current_company = r["source"]
            count = 0
            print(f"\n  {current_company}:")
        print(f"    - {r['target']}")
        count += 1
    if current_company:
        print(f"    ({count} competitors)\n")


def discover_partners(driver: Driver) -> None:
    """Print current partner edges (if any)."""
    print("=" * 70)
    print("PARTNERS BY COMPANY")
    print("=" * 70)

    records = run(driver, """
        MATCH (a:Company)-[:PARTNERS_WITH]->(b:Company)
        WHERE a.name IN $companies
        RETURN a.name AS source, b.name AS target
        ORDER BY a.name, b.name
    """, companies=FILING_COMPANIES)

    if not records:
        print("  (no PARTNERS_WITH edges found)\n")
        return

    current_company = None
    for r in records:
        if r["source"] != current_company:
            current_company = r["source"]
            print(f"\n  {current_company}:")
        print(f"    - {r['target']}")
    print()


def discover(driver: Driver) -> None:
    discover_products(driver)
    discover_risk_factors(driver)
    discover_competitors(driver)
    discover_partners(driver)


# ---------------------------------------------------------------------------
# Export mode
# ---------------------------------------------------------------------------


def export(driver: Driver) -> None:
    if not CURATED_PRODUCTS:
        print("[ERROR] CURATED_PRODUCTS is empty. Run --discover first and populate the lists.")
        sys.exit(1)
    if not CURATED_RISKS:
        print("[ERROR] CURATED_RISKS is empty. Run --discover first and populate the lists.")
        sys.exit(1)

    params = {"companies": FILING_COMPANIES}

    # ── Companies ─────────────────────────────────────────────────────────
    records = run(driver, """
        MATCH (c:Company)
        WHERE c.name IN $companies
        RETURN c.name AS name,
               coalesce(c.ticker, '') AS ticker,
               coalesce(c.cik, '') AS cik,
               coalesce(c.cusip, '') AS cusip
        ORDER BY c.name
    """, **params)

    companies = [dict(r) for r in records]
    company_id_map: dict[str, str] = {}
    for i, c in enumerate(companies, 1):
        cid = f"C{i:03d}"
        company_id_map[c["name"]] = cid
        c["company_id"] = cid

    write_csv("companies.csv", ["company_id", "name", "ticker", "cik", "cusip"], companies)

    # ── Asset Managers ────────────────────────────────────────────────────
    records = run(driver, """
        MATCH (am:AssetManager)-[:OWNS]->(c:Company)
        WHERE c.name IN $companies
        RETURN DISTINCT am.name AS name
        ORDER BY am.name
    """, **params)

    managers = [dict(r) for r in records]
    manager_id_map: dict[str, str] = {}
    for i, m in enumerate(managers, 1):
        mid = f"AM{i:03d}"
        manager_id_map[m["name"]] = mid
        m["manager_id"] = mid

    write_csv("asset_managers.csv", ["manager_id", "name"], managers)

    # ── Products (curated) ────────────────────────────────────────────────
    all_product_names = []
    for names in CURATED_PRODUCTS.values():
        all_product_names.extend(names)

    records = run(driver, """
        MATCH (p:Product)
        WHERE p.name IN $names
        RETURN p.name AS name, coalesce(p.description, '') AS description
        ORDER BY p.name
    """, names=all_product_names)

    products = [dict(r) for r in records]
    product_id_map: dict[str, str] = {}
    for i, p in enumerate(products, 1):
        pid = f"P{i:03d}"
        product_id_map[p["name"]] = pid
        p["product_id"] = pid

    write_csv("products.csv", ["product_id", "name", "description"], products)

    # Report any curated products not found in DB
    found_names = {p["name"] for p in products}
    missing = [n for n in all_product_names if n not in found_names]
    if missing:
        print(f"\n  [WARN] {len(missing)} curated products NOT found in database:")
        for m in missing:
            print(f"    - {m}")
        print()

    # ── Risk Factors (curated) ────────────────────────────────────────────
    records = run(driver, """
        MATCH (r:RiskFactor)
        WHERE r.name IN $names
        RETURN r.name AS name, coalesce(r.description, '') AS description
        ORDER BY r.name
    """, names=CURATED_RISKS)

    risks = [dict(r) for r in records]
    risk_id_map: dict[str, str] = {}
    for i, r in enumerate(risks, 1):
        rid = f"R{i:03d}"
        risk_id_map[r["name"]] = rid
        r["risk_id"] = rid

    write_csv("risk_factors.csv", ["risk_id", "name", "description"], risks)

    # Report any curated risks not found in DB
    found_risk_names = {r["name"] for r in risks}
    missing_risks = [n for n in CURATED_RISKS if n not in found_risk_names]
    if missing_risks:
        print(f"\n  [WARN] {len(missing_risks)} curated risks NOT found in database:")
        for m in missing_risks:
            print(f"    - {m}")
        print()

    # ── Junction: OFFERS ──────────────────────────────────────────────────
    records = run(driver, """
        MATCH (c:Company)-[:OFFERS]->(p:Product)
        WHERE c.name IN $companies AND p.name IN $products
        RETURN c.name AS company_name, p.name AS product_name
        ORDER BY c.name, p.name
    """, companies=FILING_COMPANIES, products=list(found_names))

    rows = []
    for r in records:
        cid = company_id_map.get(r["company_name"])
        pid = product_id_map.get(r["product_name"])
        if cid and pid:
            rows.append({"company_id": cid, "product_id": pid})
    write_csv("company_products.csv", ["company_id", "product_id"], rows)

    # ── Junction: FACES_RISK ──────────────────────────────────────────────
    records = run(driver, """
        MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
        WHERE c.name IN $companies AND r.name IN $risks
        RETURN c.name AS company_name, r.name AS risk_name
        ORDER BY c.name, r.name
    """, companies=FILING_COMPANIES, risks=list(found_risk_names))

    rows = []
    for r in records:
        cid = company_id_map.get(r["company_name"])
        rid = risk_id_map.get(r["risk_name"])
        if cid and rid:
            rows.append({"company_id": cid, "risk_id": rid})
    write_csv("company_risk_factors.csv", ["company_id", "risk_id"], rows)

    # ── Junction: OWNS ────────────────────────────────────────────────────
    records = run(driver, """
        MATCH (am:AssetManager)-[o:OWNS]->(c:Company)
        WHERE c.name IN $companies AND am.name IS NOT NULL
        RETURN am.name AS manager_name, c.name AS company_name,
               coalesce(o.shares, 0) AS shares
        ORDER BY am.name, c.name
    """, **params)

    rows = []
    for r in records:
        mid = manager_id_map.get(r["manager_name"])
        cid = company_id_map.get(r["company_name"])
        if mid and cid:
            rows.append({"manager_id": mid, "company_id": cid, "shares": r["shares"]})
    write_csv("asset_manager_companies.csv", ["manager_id", "company_id", "shares"], rows)

    # ── Junction: COMPETES_WITH ───────────────────────────────────────────
    records = run(driver, """
        MATCH (a:Company)-[:COMPETES_WITH]->(b:Company)
        WHERE a.name IN $companies
          AND a.name IS NOT NULL AND b.name IS NOT NULL
        RETURN a.name AS source, b.name AS target
        ORDER BY a.name, b.name
    """, **params)

    rows = []
    for r in records:
        sid = company_id_map.get(r["source"])
        if sid:
            tid = company_id_map.get(r["target"])
            rows.append({
                "source_company_id": sid,
                "target_company_id": tid or "",
                "target_company_name": r["target"],
            })
    write_csv(
        "company_competitors.csv",
        ["source_company_id", "target_company_id", "target_company_name"],
        rows,
    )

    # ── Junction: PARTNERS_WITH (hardcoded) ───────────────────────────────
    rows = []
    for source_name, target_name in PARTNER_EDGES:
        sid = company_id_map.get(source_name)
        if sid:
            tid = company_id_map.get(target_name)
            rows.append({
                "source_company_id": sid,
                "target_company_id": tid or "",
                "target_company_name": target_name,
            })
    write_csv(
        "company_partners.csv",
        ["source_company_id", "target_company_id", "target_company_name"],
        rows,
    )

    # ── Documents (FILED) ──────────────────────────────────────────────
    records = run(driver, """
        MATCH (c:Company)-[:FILED]->(d:Document)
        WHERE c.name IN $companies
        RETURN c.name AS company_name, d.source AS source
        ORDER BY c.name, d.source
    """, **params)

    documents: list[dict] = []
    doc_junctions: list[dict] = []
    document_id_map: dict[str, str] = {}
    for r in records:
        # Extract accession number from the source path filename
        source = r["source"]
        accession = source.rsplit("/", 1)[-1].replace(".pdf", "")
        did = f"D{len(documents) + 1:03d}"
        documents.append({
            "document_id": did,
            "accession_number": accession,
            "filing_type": "10-K",
        })
        document_id_map[source] = did
        cid = company_id_map.get(r["company_name"])
        if cid:
            doc_junctions.append({"company_id": cid, "document_id": did})

    write_csv("documents.csv", ["document_id", "accession_number", "filing_type"], documents)
    write_csv("company_documents.csv", ["company_id", "document_id"], doc_junctions)

    # ── Verification ──────────────────────────────────────────────────────
    verify(company_id_map, product_id_map, risk_id_map, manager_id_map, document_id_map, rows)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def verify(
    company_id_map: dict[str, str],
    product_id_map: dict[str, str],
    risk_id_map: dict[str, str],
    manager_id_map: dict[str, str],
    document_id_map: dict[str, str],
    partner_rows: list[dict],
) -> None:
    """Print summary counts and run integrity checks."""
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    # Read back all CSVs and count
    csv_counts = {}
    for fname in [
        "companies.csv", "products.csv", "risk_factors.csv",
        "asset_managers.csv", "documents.csv", "company_products.csv",
        "company_risk_factors.csv", "company_competitors.csv",
        "company_partners.csv", "asset_manager_companies.csv",
        "company_documents.csv",
    ]:
        path = EXPORT_DIR / fname
        if path.exists():
            with open(path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                csv_counts[fname] = len(rows)
        else:
            csv_counts[fname] = 0

    # Count mentioned companies (non-filing companies from competitors + partners)
    mentioned = set()
    for fname in ["company_competitors.csv", "company_partners.csv"]:
        path = EXPORT_DIR / fname
        if path.exists():
            with open(path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("target_company_name", "")
                    if name and name not in FILING_COMPANIES:
                        mentioned.add(name)

    total_companies = csv_counts["companies.csv"] + len(mentioned)

    print(f"\n  Count Summary:")
    print(f"  {'Entity':<30} {'Count':>6}")
    print(f"  {'-'*30} {'-'*6}")
    print(f"  {'Company (filing)':<30} {csv_counts['companies.csv']:>6}")
    print(f"  {'Company (mentioned)':<30} {len(mentioned):>6}")
    print(f"  {'Company (total after load)':<30} {total_companies:>6}")
    print(f"  {'Product':<30} {csv_counts['products.csv']:>6}")
    print(f"  {'RiskFactor':<30} {csv_counts['risk_factors.csv']:>6}")
    print(f"  {'AssetManager':<30} {csv_counts['asset_managers.csv']:>6}")
    print(f"  {'Document':<30} {csv_counts['documents.csv']:>6}")
    print(f"  {'OFFERS edges':<30} {csv_counts['company_products.csv']:>6}")
    print(f"  {'FACES_RISK edges':<30} {csv_counts['company_risk_factors.csv']:>6}")
    print(f"  {'COMPETES_WITH edges':<30} {csv_counts['company_competitors.csv']:>6}")
    print(f"  {'PARTNERS_WITH edges':<30} {csv_counts['company_partners.csv']:>6}")
    print(f"  {'OWNS edges':<30} {csv_counts['asset_manager_companies.csv']:>6}")
    print(f"  {'FILED edges':<30} {csv_counts['company_documents.csv']:>6}")

    # Lab 1 query checks
    print(f"\n  Lab 1 Query Checks:")

    # NVIDIA products
    nvidia_products = _read_junction("company_products.csv", "company_id",
                                      company_id_map.get("NVIDIA Corporation", ""))
    print(f"    NVIDIA products: {len(nvidia_products)} (need > 0)")

    # Shared risk factors
    risk_companies = {}
    path = EXPORT_DIR / "company_risk_factors.csv"
    if path.exists():
        with open(path) as f:
            for row in csv.DictReader(f):
                rid = row["risk_id"]
                risk_companies.setdefault(rid, set()).add(row["company_id"])
    shared = sum(1 for cids in risk_companies.values() if len(cids) >= 2)
    print(f"    Shared risk factors (2+ companies): {shared} (need > 0)")

    # Microsoft competitors
    msft_competitors = _read_junction("company_competitors.csv", "source_company_id",
                                       company_id_map.get("Microsoft Corporation", ""))
    print(f"    Microsoft competitors: {len(msft_competitors)} (need > 0)")

    # NVIDIA partners
    nvidia_partners = [r for r in partner_rows
                       if r["source_company_id"] == company_id_map.get("NVIDIA Corporation", "")]
    print(f"    NVIDIA partners: {len(nvidia_partners)} (need > 0)")

    # Asset manager holdings
    print(f"    Asset manager holdings: {csv_counts['asset_manager_companies.csv']} (need > 0)")

    # Filed documents
    print(f"    Filed documents: {csv_counts['company_documents.csv']} (need > 0)")

    # Referential integrity
    print(f"\n  Referential Integrity:")
    _check_refs("company_products.csv", "product_id", "products.csv", "product_id")
    _check_refs("company_products.csv", "company_id", "companies.csv", "company_id")
    _check_refs("company_risk_factors.csv", "risk_id", "risk_factors.csv", "risk_id")
    _check_refs("company_risk_factors.csv", "company_id", "companies.csv", "company_id")
    _check_refs("asset_manager_companies.csv", "manager_id", "asset_managers.csv", "manager_id")
    _check_refs("asset_manager_companies.csv", "company_id", "companies.csv", "company_id")
    _check_refs("company_competitors.csv", "source_company_id", "companies.csv", "company_id")
    _check_refs("company_documents.csv", "document_id", "documents.csv", "document_id")
    _check_refs("company_documents.csv", "company_id", "companies.csv", "company_id")

    # Expected counts for Lab 1 README
    print(f"\n  Values for Lab 1 README verification table:")
    print(f"    AssetManager: {csv_counts['asset_managers.csv']}")
    print(f"    Company: ~{total_companies}")
    print(f"    Document: {csv_counts['documents.csv']}")
    print(f"    Product: {csv_counts['products.csv']}")
    print(f"    RiskFactor: {csv_counts['risk_factors.csv']}")
    print()


def _read_junction(filename: str, key: str, value: str) -> list[dict]:
    path = EXPORT_DIR / filename
    if not path.exists():
        return []
    with open(path) as f:
        return [row for row in csv.DictReader(f) if row.get(key) == value]


def _check_refs(junction_file: str, fk_col: str, entity_file: str, pk_col: str) -> None:
    entity_path = EXPORT_DIR / entity_file
    junction_path = EXPORT_DIR / junction_file
    if not entity_path.exists() or not junction_path.exists():
        print(f"    [SKIP] {junction_file}.{fk_col} -> {entity_file}.{pk_col}")
        return

    with open(entity_path) as f:
        valid_ids = {row[pk_col] for row in csv.DictReader(f)}
    with open(junction_path) as f:
        fk_values = {row[fk_col] for row in csv.DictReader(f) if row[fk_col]}

    orphans = fk_values - valid_ids
    if orphans:
        print(f"    [FAIL] {junction_file}.{fk_col} -> {entity_file}.{pk_col}: "
              f"{len(orphans)} orphaned refs: {sorted(orphans)[:5]}")
    else:
        print(f"    [OK]   {junction_file}.{fk_col} -> {entity_file}.{pk_col}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Export curated seed-data slice")
    parser.add_argument("--discover", action="store_true",
                        help="Print products and risk factors for human review")
    args = parser.parse_args()

    driver = get_driver()
    try:
        if args.discover:
            discover(driver)
        else:
            print(f"Exporting curated slice to {EXPORT_DIR}/ ...\n")
            export(driver)
            print("[DONE] Curated seed data exported.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
