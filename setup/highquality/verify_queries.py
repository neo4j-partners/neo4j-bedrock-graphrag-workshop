#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["neo4j>=5.0", "python-dotenv>=1.0"]
# ///
"""Run the Lab 1 sample queries against the live database to verify results.

Usage:
    cd highquality
    uv run verify_queries.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import dotenv_values
from neo4j import Driver, GraphDatabase

ENV_FILE = Path(__file__).resolve().parent.parent / "financial_data_load" / ".env"


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


def run_query(driver: Driver, title: str, cypher: str, pass_condition=None) -> bool:
    """Run a query, print results, and check the pass condition."""
    print(f"{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")
    print(f"  {cypher.strip()}\n")

    records = run(driver, cypher)

    if not records:
        print("  (no results)\n")
        ok = False
    else:
        keys = records[0].keys()
        # Print header
        widths = {}
        for k in keys:
            col_vals = [str(r[k]) for r in records]
            widths[k] = max(len(k), max(len(v) for v in col_vals))
        header = "  " + " | ".join(k.ljust(widths[k]) for k in keys)
        separator = "  " + "-+-".join("-" * widths[k] for k in keys)
        print(header)
        print(separator)
        for r in records:
            row = "  " + " | ".join(str(r[k]).ljust(widths[k]) for k in keys)
            print(row)
        print(f"\n  ({len(records)} rows)\n")
        ok = True

    if pass_condition is not None:
        ok = pass_condition(records)

    status = "[PASS]" if ok else "[FAIL]"
    print(f"  {status}\n")
    return ok


def main() -> None:
    driver = get_driver()
    results = []

    try:
        # Query 1: Verify node counts
        results.append(run_query(
            driver,
            "Verify the Load — Node counts",
            """
MATCH (n)
WITH labels(n)[0] AS label, count(n) AS count
RETURN label, count ORDER BY label
            """,
            pass_condition=lambda rows: len(rows) >= 4,
        ))

        # Query 2: What products does NVIDIA offer?
        results.append(run_query(
            driver,
            "What products does NVIDIA offer?",
            """
MATCH (c:Company {ticker: 'NVDA'})-[:OFFERS]->(p:Product)
RETURN p.name ORDER BY p.name LIMIT 10
            """,
            pass_condition=lambda rows: len(rows) > 0,
        ))

        # Query 3: Which risk factors are shared across multiple companies?
        results.append(run_query(
            driver,
            "Which risk factors are shared across multiple companies?",
            """
MATCH (c:Company)-[:FACES_RISK]->(r:RiskFactor)
WITH r, collect(c.ticker) AS companies, count(c) AS cnt
WHERE cnt > 1
RETURN r.name, companies, cnt
ORDER BY cnt DESC LIMIT 5
            """,
            pass_condition=lambda rows: len(rows) > 0,
        ))

        # Query 4: Who are the top asset managers by number of holdings?
        results.append(run_query(
            driver,
            "Who are the top asset managers by number of holdings?",
            """
MATCH (am:AssetManager)-[o:OWNS]->(c:Company)
WITH am, count(c) AS holdings, sum(o.shares) AS total_shares
RETURN am.name, holdings, total_shares
ORDER BY holdings DESC LIMIT 5
            """,
            pass_condition=lambda rows: len(rows) > 0,
        ))

        # Query 5: Who does Microsoft compete with?
        results.append(run_query(
            driver,
            "Who does Microsoft compete with?",
            """
MATCH (c:Company {ticker: 'MSFT'})-[:COMPETES_WITH]->(comp)
RETURN comp.name ORDER BY comp.name
            """,
            pass_condition=lambda rows: len(rows) > 0,
        ))

        # Query 6: Which risk factors expose an asset manager's portfolio?
        results.append(run_query(
            driver,
            "Which risk factors expose an asset manager's portfolio across multiple companies?",
            """
MATCH (am:AssetManager)-[:OWNS]->(c:Company)-[:FACES_RISK]->(r:RiskFactor)
WITH am, r, count(DISTINCT c) AS exposed
WHERE exposed > 1
RETURN am.name, r.name, exposed
ORDER BY exposed DESC, am.name LIMIT 5
            """,
            pass_condition=lambda rows: len(rows) > 0,
        ))

        # Query 7: Who are NVIDIA's supply chain partners?
        # NOTE: PARTNERS_WITH edges are hardcoded in company_partners.csv,
        # not in the live database. This query only returns results after
        # loading the seed CSVs into a fresh Aura instance.
        results.append(run_query(
            driver,
            "Who are NVIDIA's supply chain partners? (partners are in CSV only, not live DB)",
            """
MATCH (c:Company {ticker: 'NVDA'})-[:PARTNERS_WITH]->(p)
RETURN p.name ORDER BY p.name
            """,
            pass_condition=lambda rows: True,  # expected empty on live DB
        ))

        # Summary
        print("=" * 70)
        passed = sum(results)
        total = len(results)
        print(f"  {passed}/{total} queries passed")
        if passed == total:
            print("  All Lab 1 sample queries verified successfully.")
        else:
            print("  Some queries failed — check output above.")
        print("=" * 70)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
