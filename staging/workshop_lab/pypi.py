# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/pypi.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Step 13. The one check in this notebook that never touches AWS.

Every lab in the workshop opens by installing its own dependencies from PyPI:
`neo4j-graphrag[bedrock]` in labs 2 and 3, `strands-agents` in lab 4,
`neo4j-agent-memory` in lab 5, `bedrock-agentcore-starter-toolkit` in both
deploy notebooks, `mcp` and `httpx` in lab 6. A host that cannot reach PyPI
fails at the first cell of every one of them, as a pip resolver error that names
a package rather than the network.

None of that is an AWS permission, so every other check in this notebook can
pass while this one fails. That is why it is measured here and not inferred.

**This step used to build a Lambda deployment package, and no longer does.** It
was written against a different workshop, one that pre-provisioned a reservation
Lambda through a `uv`-launched script, so it ran a platform-targeted install for
`linux/arm64` and reported a missing `uv` binary as a failure. This workshop
deploys no Lambda at all: AgentCore images are built in CodeBuild, and step 11
already proves the Lambda path end to end with a dependency-free function. The
`uv` half was measuring a prerequisite of a program that is not in this
workshop, and a check that fails on something nothing needs teaches students to
ignore failures. What is left is the half every lab actually depends on.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from typing import TYPE_CHECKING

from workshop_lab.harness import FAIL, PASS

if TYPE_CHECKING:
    from workshop_lab.harness import Harness

# The workshop's own package, at the floor four of its labs ask for, rather than
# a placeholder like `pip download requests`. An index that answers but carries
# only a subset of PyPI passes a placeholder and still breaks every lab, and a
# mirror is exactly what a restricted lab network tends to put in the way.
WORKSHOP_REQUIREMENT = "neo4j-graphrag>=1.18.0"

# A blocked index usually hangs rather than refusing, so the failure this bounds
# is a step that never returns at all.
INSTALL_TIMEOUT_SECONDS = 300

PYPI_CHECK = "PyPI is reachable from this host"

# `python -m pip` on an interpreter that has no pip exits 1 with this on stderr,
# and `failure_detail` would report it as the reason PyPI is unreachable. It is
# the opposite: nothing was asked of the network at all. A uv-managed
# virtualenv is the ordinary way to arrive here, and a Jupyter kernel running
# `%pip install` is not, so telling the two apart is the difference between a
# problem to report and a problem to ignore.
NO_PIP_MARKER = "No module named pip"
NO_PIP_DETAIL = "this interpreter has no pip, so PyPI was never contacted"


def pip_install(target: str) -> list[str]:
    """Return the command that asks PyPI for the workshop's own package.

    `--no-deps` because the question is whether this host reaches PyPI at all,
    not whether the full tree resolves. Resolving the transitive set takes
    minutes, and every lab resolves its own anyway. The cost is that a
    dependency yanked from the index is not caught here; the first lab cell
    catches that. `--target` keeps the wheel out of the kernel's own
    environment, so a step meant to measure cannot change what a later cell
    imports.
    """
    return [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--target",
        target,
        WORKSHOP_REQUIREMENT,
    ]


def failure_detail(done: subprocess.CompletedProcess[str]) -> str:
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
    return f"pip exited {done.returncode}"


def try_install() -> tuple[bool, str]:
    """Run the install into a throwaway directory and report what happened."""
    with tempfile.TemporaryDirectory() as target:
        try:
            done = subprocess.run(
                pip_install(target),
                capture_output=True,
                text=True,
                timeout=INSTALL_TIMEOUT_SECONDS,
            )
        except FileNotFoundError:
            return False, "pip is not on PATH"
        except subprocess.TimeoutExpired:
            return False, f"pip did not finish within {INSTALL_TIMEOUT_SECONDS}s"
    if done.returncode == 0:
        return True, f"resolved {WORKSHOP_REQUIREMENT}"
    if NO_PIP_MARKER in done.stderr + done.stdout:
        return False, NO_PIP_DETAIL
    return False, failure_detail(done)


class PyPIReachable:
    """Asks PyPI for the workshop's own package and reports whether it answered."""

    def __init__(self, lab: Harness) -> None:
        self.lab = lab

    def run(self) -> bool:
        """Do the whole step and report whether the labs can install anything."""
        reached, detail = try_install()
        self.lab.record(PYPI_CHECK, PASS if reached else FAIL, detail)
        if reached:
            return True
        if detail == NO_PIP_DETAIL:
            self.lab.echo("\nThis is the interpreter running this notebook, not PyPI.")
            self.lab.echo(
                "A lab kernel that can run %pip install has pip, so if you are "
                "in the lab, report it."
            )
        else:
            self.lab.echo("\nNo lab in this workshop can install its dependencies.")
            self.lab.echo(
                "Report it: every lab notebook opens with a pip install, "
                "so this stops all of them at the first cell."
            )
        return False
