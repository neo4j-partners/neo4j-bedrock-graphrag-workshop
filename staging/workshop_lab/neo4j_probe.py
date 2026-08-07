# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/neo4j_probe.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Step 3: prove the Aura instance is reachable, writable, and left clean.

This is the one check in the notebook that does not touch AWS, so it does not go
through `Harness.check` and its result reaches the summary through the `extra`
argument instead. It also carries the workshop's only credentials a student
types by hand, which is why the placeholder test is a separate state from the
failure state: a student who has not filled in the constants yet has not failed
anything, and telling them they have sends them debugging a connection they
never attempted.

The probe writes a node, reads it back, deletes it, and then counts what is
left. Counting afterwards is the point. A delete that returns is not a delete
that removed anything, and an Aura instance carrying leftover
`:VocareumVerifyProbe` nodes from a previous run is a dirty instance the student
should be told about rather than one the next lab quietly inherits.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

PLACEHOLDER = "REPLACE-ME"
PROBE_LABEL = "VocareumVerifyProbe"
PROBE_ID = "vocareum-verify-probe"


class Neo4jProbe:
    """Connect to Aura, round-trip one node, and confirm nothing is left behind."""

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        database: str = "neo4j",
        echo: Callable[[str], None] = print,
    ) -> None:
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.echo = echo
        self.ready = False

    @property
    def configured(self) -> bool:
        """False while the constants in the notebook still hold placeholders."""
        return PLACEHOLDER not in f"{self.uri}{self.password}"

    def run(self) -> bool:
        """Run the probe. Returns True only if Neo4j is reachable and writable."""
        if not self.configured:
            self.echo("SKIP  The Neo4j constants in step 3 still hold placeholders.")
            self.echo("      Replace NEO4J_URI and NEO4J_PASSWORD, then re-run.")
            self.ready = False
            return False
        self.ready = self._probe()
        return self.ready

    def result(self) -> tuple[str, str, str]:
        """The summary row for this probe, in `Harness.results` shape."""
        if self.ready:
            return ("Neo4j is reachable and writable", "PASS", "")
        if not self.configured:
            return ("Neo4j", "SKIP", "the constants in step 3 still hold placeholders")
        return ("Neo4j", "FAIL", "see step 3")

    # --- internals ------------------------------------------------------------
    def _probe(self) -> bool:
        try:
            from neo4j import GraphDatabase
            from neo4j.exceptions import DriverError, Neo4jError
        except ImportError:
            self.echo("SKIP  The neo4j driver is not installed.")
            self.echo("      Run this in a cell, then re-run this one:")
            self.echo("          %pip install 'neo4j>=6.0.0,<7.0.0'")
            return False

        try:
            with GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            ) as driver:
                driver.verify_connectivity()
                self.echo("PASS  Connected to Neo4j.")
                with driver.session(database=self.database) as graph:
                    if not self._round_trip(graph):
                        return False
                    left = self._remaining(graph)
        except Neo4jError as error:
            self.echo(f"FAIL  Neo4j refused the request: {error.code}")
            self.echo(f"      {error.message}")
            return False
        except DriverError as error:
            self.echo(f"FAIL  Could not reach Neo4j: {error}")
            self.echo("      Check NEO4J_URI. Aura URIs start with neo4j+s://")
            return False

        if left:
            self.echo(
                f"FAIL  {left} probe nodes remain. Delete :{PROBE_LABEL} by hand."
            )
            return False
        self.echo("PASS  Deleted the probe node. Neo4j is ready.")
        return True

    def _round_trip(self, graph: Any) -> bool:
        written = graph.run(
            f"CREATE (n:{PROBE_LABEL} {{id: $id}}) RETURN n.id AS id", id=PROBE_ID
        ).single()
        if written is None or written["id"] != PROBE_ID:
            self.echo("FAIL  The write returned no node.")
            return False
        self.echo("PASS  Wrote and read back one node.")
        graph.run(f"MATCH (n:{PROBE_LABEL} {{id: $id}}) DELETE n", id=PROBE_ID)
        return True

    def _remaining(self, graph: Any) -> int:
        return graph.run(
            f"MATCH (n:{PROBE_LABEL} {{id: $id}}) RETURN count(n) AS n", id=PROBE_ID
        ).single()["n"]
