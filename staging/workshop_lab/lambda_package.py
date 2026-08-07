# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/lambda_package.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Step 13. The one part of the workshop's deployment that never touches AWS.

The workshop's reservation Lambda imports the Neo4j driver, and the Lambda Python
runtime does not carry it. So `setup/provision_agentcore.py` shells out to `uv
pip install` to fetch the driver, targeted at `aarch64-manylinux2014` so the
wheels match Amazon Linux on arm64 rather than whatever this machine is, and zips
the result into the deployment package.

Two things have to be true for that to work: `uv` has to be on this host, and
this host has to reach PyPI. Neither is an AWS permission, so every other check
in the notebook can pass while this fails. It also fails early, before the
deployment makes its first AWS call, and it fails as a bare `FileNotFoundError`
or a `uv` exit code, neither of which names the cause.

**The two causes are separated on purpose.** When `uv` is missing or fails, this
falls back to `pip` with the same platform target. A `pip` install that succeeds
means PyPI is reachable and only the binary is absent, which is a different
problem with a different fix.

PyPI matters well beyond the Lambda. Every demo folder in the workshop has its
own `requirements.txt`, so a host that cannot reach PyPI installs none of them.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from typing import TYPE_CHECKING

from workshop_lab.harness import FAIL, PASS, SKIP

if TYPE_CHECKING:
    from workshop_lab.harness import Harness

LAMBDA_REQUIREMENT = "neo4j>=6.0.0,<7.0.0"
PYTHON_VERSION = "3.12"

# Lambda runs Amazon Linux on arm64 and this machine is something else, so an
# untargeted install resolves wheels that import here and fail at cold start
# there. uv and pip spell the same platform differently.
UV_PLATFORM = "aarch64-manylinux2014"
PIP_PLATFORM = "manylinux2014_aarch64"

INSTALL_TIMEOUT_SECONDS = 300

UV_PRESENT_CHECK = "uv is on PATH"
BUILD_CHECK = "uv builds the Lambda package for linux/arm64"
PYPI_CHECK = "PyPI is reachable from this host"


def uv_install(target: str) -> list[str]:
    """Return the command `setup/provision_agentcore.py` runs, verbatim."""
    return [
        "uv",
        "pip",
        "install",
        "--python-platform",
        UV_PLATFORM,
        "--python-version",
        PYTHON_VERSION,
        "--only-binary",
        ":all:",
        "--target",
        target,
        LAMBDA_REQUIREMENT,
    ]


def pip_install(target: str) -> list[str]:
    """Return the same install through pip, which tells the two causes apart."""
    return [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--platform",
        PIP_PLATFORM,
        "--python-version",
        PYTHON_VERSION,
        "--only-binary",
        ":all:",
        # A pip older than the version being targeted reads requires-python
        # against the interpreter running it rather than against
        # --python-version, refuses every wheel, and prints a wall of
        # requires-python text. That is indistinguishable from a blocked PyPI
        # unless this flag is here. Measured on 2026-08-06: pip 21.2.4 on
        # Python 3.9 failed this install and succeeded with the flag added,
        # having downloaded the wheels both times.
        "--ignore-requires-python",
        "--target",
        target,
        LAMBDA_REQUIREMENT,
    ]


def failure_detail(tool: str, done: subprocess.CompletedProcess[str]) -> str:
    """Return the line naming the cause, not the last line printed.

    pip prints its own upgrade notice after the error, so the last line of a
    failed install is routinely advice about pip. Reporting that as the reason
    PyPI is unreachable would be worse than reporting nothing.
    """
    lines = [
        line.strip()
        for line in (done.stderr + done.stdout).splitlines()
        if line.strip()
    ]
    errors = [line for line in lines if line.lower().startswith("error")]
    if errors:
        return errors[-1][:160]
    if lines:
        return lines[-1][:160]
    return f"{tool} exited {done.returncode}"


def try_install(tool: str, build: Callable[[str], list[str]]) -> tuple[bool, str]:
    """Run one installer into a throwaway directory and report what happened."""
    with tempfile.TemporaryDirectory() as target:
        try:
            done = subprocess.run(
                build(target),
                capture_output=True,
                text=True,
                timeout=INSTALL_TIMEOUT_SECONDS,
            )
        except FileNotFoundError:
            return False, f"{tool} is not on PATH"
        except subprocess.TimeoutExpired:
            return False, f"{tool} did not finish within {INSTALL_TIMEOUT_SECONDS}s"
    if done.returncode == 0:
        return True, f"resolved {LAMBDA_REQUIREMENT} for linux/arm64"
    return False, failure_detail(tool, done)


class LambdaPackage:
    """Runs provisioning's install on this host, and says which half failed."""

    def __init__(self, lab: Harness) -> None:
        self.lab = lab
        self.built = False

    def check_uv(self) -> bool:
        """Is the binary provisioning shells out to even here?"""
        present = shutil.which("uv") is not None
        self.lab.record(
            UV_PRESENT_CHECK,
            PASS if present else FAIL,
            ""
            if present
            else "provisioning shells out to uv and cannot start without it",
        )
        return present

    def build_with_uv(self, present: bool) -> bool:
        """Run the install the way provisioning runs it."""
        if not present:
            self.lab.record(BUILD_CHECK, SKIP, "uv is not on PATH")
            self.built = False
            return False

        self.built, detail = try_install("uv", uv_install)
        self.lab.record(BUILD_CHECK, PASS if self.built else FAIL, detail)
        return self.built

    def check_pypi(self) -> bool:
        """Separate a missing `uv` from a host that cannot reach PyPI.

        Only reached when `uv` is absent or failed. A pip install that works
        means PyPI is fine and `uv` is the missing piece, which is a one-line
        fix rather than a networking problem to escalate.
        """
        if self.built:
            self.lab.record(PYPI_CHECK, PASS, "uv downloaded the wheel")
            return True

        reached, detail = try_install("pip", pip_install)
        self.lab.record(PYPI_CHECK, PASS if reached else FAIL, detail)
        if reached:
            self.lab.echo("\nPyPI is reachable, so the missing piece is uv itself.")
            self.lab.echo("Install uv on the machine that runs provision_agentcore.py.")
        else:
            self.lab.echo(
                "\nNothing in the workshop installs from this host. Report it:"
            )
            self.lab.echo(
                "every demo folder has a requirements.txt and none of them can run."
            )
        return reached

    def run(self) -> bool:
        """Do the whole step and report whether the package can be built here."""
        self.build_with_uv(self.check_uv())
        self.check_pypi()
        return self.built
