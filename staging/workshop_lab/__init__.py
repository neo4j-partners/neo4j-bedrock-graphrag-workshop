# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/__init__.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Utility classes the Vocareum lab notebook installs from GitHub.

The notebook cannot rely on files shipped beside it. Vocareum's documentation
says everything in `/voc/startercode` is copied into each student's `/voc/work`
and that Jupyter puts the notebook's directory on `sys.path`, so a sibling
module should import. Measured 2026-08-06 in a live session: it does not. What
does work, measured the same day, is fetching Python over HTTPS from a public
GitHub repository, so this package is installed rather than shipped:

    %pip install "https://github.com/neo4j-partners/neo4j-bedrock-graphrag-workshop/archive/refs/heads/main.zip#subdirectory=staging"

**This directory is the source of truth, and it is not the copy the notebook
installs.** `aws-vocareum` is private, and a private repository answers
`raw.githubusercontent.com` and the archive endpoint with 404 rather than 403,
so the notebook cannot install from here. `scripts/sync_workshop_lab.py`
publishes this package into the public workshop repository's `staging/`
directory, and `tests/test_workshop_lab_drift.py` fails when the two disagree.
Edit here, never there.

The version below is what the notebook prints in step 0. Bump it whenever the
published copy changes, so a student's output names the code they actually ran
rather than the code that was current when the notebook was written.
"""

from workshop_lab.build import ContainerBuild
from workshop_lab.build_source import BuildSource
from workshop_lab.datastores import DataStores
from workshop_lab.gateway import GatewayBoundary
from workshop_lab.harness import FAIL, GONE_CODES, PASS, SKIP, Harness
from workshop_lab.lambda_package import LambdaPackage
from workshop_lab.memory import Memory
from workshop_lab.naming import PREBUILT_IMAGE, Names
from workshop_lab.neo4j_probe import Neo4jProbe
from workshop_lab.roles import AGENTCORE_PRINCIPAL, ROLE_SPECS, Roles, RoleSpec
from workshop_lab.runtime import AgentRuntime
from workshop_lab.selection import WORKSHOP_TAG_KEY, WORKSHOP_TAG_VALUE
from workshop_lab.teardown import Teardown

__version__ = "0.11.0"

__all__ = [
    "AGENTCORE_PRINCIPAL",
    "FAIL",
    "GONE_CODES",
    "PASS",
    "PREBUILT_IMAGE",
    "ROLE_SPECS",
    "SKIP",
    "WORKSHOP_TAG_KEY",
    "WORKSHOP_TAG_VALUE",
    "AgentRuntime",
    "BuildSource",
    "ContainerBuild",
    "DataStores",
    "GatewayBoundary",
    "Harness",
    "LambdaPackage",
    "Memory",
    "Names",
    "Neo4jProbe",
    "RoleSpec",
    "Roles",
    "Teardown",
    "__version__",
]
