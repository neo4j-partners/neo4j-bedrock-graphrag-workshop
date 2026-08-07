# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/harness.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""The check harness the lab notebook runs every step through.

One `Harness` owns the boto3 session, one client per service, the list of
results the summary prints, and the list of deletes step 14 replays. Steps call
`check`, `sweep`, `defer`, and the waiters; nothing in the notebook builds a
client or catches a `ClientError` itself.

Three behaviours here are measurements rather than conveniences, and each one
exists because its absence produced a wrong answer:

**A missing resource is a pass.** `check` treats every "there is nothing here"
code as success. Authorization succeeded against something that was not there,
and that is the answer a permission question actually asked.

**A step clears its own name before it creates.** CloudTrail for 2026-08-06 has
`CreateFunction hotel-booking-verify-tool` succeeding at 11:48:28Z and then
failing `ResourceConflictException` at 11:48:50Z, with `CreateGateway
verify-gateway` succeeding at 11:48:29Z and failing `ConflictException` at
11:48:51Z. Step 11 had simply been run twice, so the second run recorded FAIL on
two creates this account plainly allows, and the refused `CreateGateway` then
returned nothing, so `CreateGatewayTarget`, `ListGatewayTargets` and
`InvokeGateway` were skipped rather than measured. One re-run stopped measuring
most of the step. A new session is not a new account either: a gateway created
2026-08-04 00:50:14Z was still there two days later, because the `DeleteGateway`
34 seconds behind its create had failed and nothing else removed it. So `sweep`
runs first and records nothing, because a delete of last run's litter answers no
question that `docs/permissions.md` asks.

**A mutating call that returns is not a mutating call that finished.** Use
`wait_until` and `wait_until_gone`. Skipping this claimed a clean account five
separate times while resources were still in it.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from workshop_lab import guards
from workshop_lab.naming import Names

# Every code a describe can raise to mean "there is nothing here", across the
# services this notebook touches.
GONE_CODES = frozenset(
    {
        "NoSuchEntity",
        "RepositoryNotFoundException",
        "ResourceNotFound",
        "ResourceNotFoundException",
    }
)

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


class Harness:
    """Session, clients, results, and cleanups for one run of the lab notebook."""

    def __init__(
        self,
        prefix: str = "verify",
        session: Any = None,
        echo: Callable[[str], None] = print,
    ) -> None:
        self.session = session if session is not None else boto3.session.Session()
        self.region = self.session.region_name or guards.REQUIRED_REGION
        self.prefix = prefix
        self.echo = echo
        self.account_id: str = ""
        self.results: list[tuple[str, str, str]] = []
        self.cleanups: list[tuple[str, Callable[[], Any]]] = []
        self._clients: dict[str, Any] = {}
        # Names needs the account id, which costs an STS call, so it is built in
        # verify_identity rather than here. Touching `names` before then is a
        # bug in the notebook, and the property says so instead of returning
        # names with an empty account id spliced into them.
        self._names: Names | None = None

    # --- setup ---------------------------------------------------------------
    @property
    def names(self) -> Names:
        if self._names is None:
            raise RuntimeError(
                "Resource names are not available until verify_identity() has run, "
                "because they contain the account id. Run step 2 first."
            )
        return self._names

    def client(self, name: str) -> Any:
        """Return one cached client per service."""
        if name not in self._clients:
            self._clients[name] = self.session.client(name, region_name=self.region)
        return self._clients[name]

    def verify_credentials(self) -> None:
        """Step 1. Raises unless all three credential fields carry a value."""
        guards.verify_credentials(self.session, echo=self.echo)

    def verify_identity(self, required_region: str = guards.REQUIRED_REGION) -> str:
        """Step 2. Raises on the wrong region. Names the account and unlocks `names`."""
        self.account_id = guards.verify_identity(
            self.client("sts"), self.region, required_region, echo=self.echo
        )
        self._names = Names(
            prefix=self.prefix, account_id=self.account_id, region=self.region
        )
        return self.account_id

    # --- recording -----------------------------------------------------------
    def record(self, name: str, verdict: str, detail: str = "") -> None:
        """File one check result and print it as it happens."""
        self.results.append((name, verdict, detail))
        self.echo(f"{verdict:<4}  {name}" + (f"  {detail}" if detail else ""))

    def check(self, name: str, call: Callable[[], Any], detail: str = "") -> Any:
        """Run one AWS call, record PASS or FAIL, and return its response or None.

        A missing resource counts as a pass: authorization succeeded on something
        that was not there, which is the answer a permission question wants.
        """
        try:
            response = call()
        except ClientError as error:
            code = error.response["Error"]["Code"]
            message = error.response["Error"].get("Message", "")
            if code in GONE_CODES:
                self.record(name, PASS, f"{code} on an absent resource")
                return None
            self.record(name, FAIL, f"{code}: {message[:160]}")
            return None
        except BotoCoreError as error:
            self.record(name, FAIL, str(error)[:160])
            return None
        self.record(name, PASS, detail)
        return response if response is not None else True

    def skip(self, name: str, reason: str) -> None:
        """Record a check that could not run, so the summary counts it as skipped."""
        self.record(name, SKIP, reason)

    # --- setup that is not a measurement --------------------------------------
    def sweep(self, label: str, delete: Callable[[], Any]) -> None:
        """Delete a leftover carrying a name this notebook is about to create.

        Records nothing. An absent resource is the ordinary case and stays quiet.
        """
        try:
            delete()
        except ClientError as error:
            if error.response["Error"]["Code"] not in GONE_CODES:
                self.echo(
                    f"      could not sweep {label}: {error.response['Error']['Code']}"
                )
            return
        except BotoCoreError as error:
            self.echo(f"      could not sweep {label}: {error}")
            return
        self.echo(f"      swept a leftover {label}")

    def defer(self, label: str, delete: Callable[[], Any]) -> None:
        """Register a delete to run in step 14, newest first."""
        self.cleanups.append((label, delete))

    # --- waiting --------------------------------------------------------------
    def wait_until(
        self,
        describe: Callable[[], str],
        done: Iterable[str],
        failed: Iterable[str],
        label: str,
        timeout: int = 420,
        interval: int = 10,
    ) -> str:
        """Poll a status until it settles, and report the state it settled in."""
        done, failed = set(done), set(failed)
        deadline = time.monotonic() + timeout
        state = ""
        while time.monotonic() < deadline:
            try:
                state = describe()
            except ClientError as error:
                return f"describe failed: {error.response['Error']['Code']}"
            except BotoCoreError as error:
                return f"describe failed: {error}"
            if state in done or state in failed:
                self.echo(f"      {label} settled in {state}")
                return state
            time.sleep(interval)
        self.echo(f"      {label} still {state} after {timeout}s")
        return state

    def wait_until_gone(
        self,
        describe: Callable[[], Any],
        label: str,
        timeout: int = 300,
        interval: int = 10,
    ) -> bool:
        """Poll until a describe reports the resource missing."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                describe()
            except ClientError as error:
                if error.response["Error"]["Code"] in GONE_CODES:
                    return True
            except BotoCoreError:
                return True
            time.sleep(interval)
        return False

    def retry_while(
        self,
        call: Callable[[], Any],
        codes: Iterable[str],
        label: str,
        timeout: int = 120,
        interval: int = 6,
    ) -> Any:
        """Retry a call while it fails with a code known to be transient.

        A role that CreateRole just returned is not yet a role every service will
        accept in PassRole. That is eventual consistency, not a refusal, so it is
        waited out rather than recorded as a failure.
        """
        codes = set(codes)
        deadline = time.monotonic() + timeout
        while True:
            try:
                return call()
            except ClientError as error:
                code = error.response["Error"]["Code"]
                if code not in codes or time.monotonic() >= deadline:
                    raise
                self.echo(f"      {label}: {code}, retrying")
                time.sleep(interval)

    # --- reporting -------------------------------------------------------------
    def summary(self, extra: Iterable[tuple[str, str, str]] = ()) -> dict[str, int]:
        """Step 15. Print every result and return the counts.

        `extra` carries results produced outside the harness, which today means
        the Neo4j probe: it talks to Aura rather than to AWS, so it never went
        through `check`, but a student reading the summary needs it in the list.

        **A SKIP does not block "ready", but a skipped `extra` does.** Steps 8,
        9, 11, 12 and 13 record SKIP as their ordinary outcome: every CodeBuild
        build in a Vocareum account is stopped a few seconds in, so the image
        never exists and everything downstream of it is skipped by design.
        Gating readiness on a zero SKIP count would mean the notebook never once
        told a student their environment was fine. The `extra` rows are
        different: Neo4j is a hard prerequisite for the rest of the workshop, and
        a student who has not filled in the constants has not verified it.
        """
        extra = list(extra)
        counts = {PASS: 0, FAIL: 0, SKIP: 0}
        for name, verdict, detail in [*self.results, *extra]:
            counts[verdict] = counts.get(verdict, 0) + 1
            self.echo(f"{verdict:<4}  {name}")
            if verdict != PASS and detail:
                self.echo(f"        {detail}")

        self.echo(
            f"\n{counts[PASS]} passed, {counts[FAIL]} failed, {counts[SKIP]} skipped"
        )
        self.echo(
            "\nNot checked here: Bedrock foundation model access. No cell above "
            "calls a\nmodel. Model access is granted separately and the workshop's "
            "Claude and\nNova calls need it, but nothing in this notebook does."
        )
        prerequisites_met = all(verdict == PASS for _, verdict, _ in extra)
        if counts[FAIL] == 0 and prerequisites_met:
            self.echo("\nEnvironment is ready. Continue to the next lab.")
        else:
            self.echo(
                "\nSomething needs attention. See the troubleshooting notes below."
            )
        return counts
