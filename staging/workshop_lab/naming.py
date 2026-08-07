# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/naming.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Every name the lab notebook creates, derived from one prefix.

The names are here rather than spread across the steps because two of them are
load-bearing in ways that are invisible at the call site, and both have already
cost a debugging session.

**A runtime name must not begin with "ws".** InvokeAgentRuntime percent-decodes
the request path, so a runtime named `ws...` puts the substring `/ws` into it.
The AgentCore front door routes the call to its WebSocket handler and answers
"Not a WebSocket Upgrade Request" without the request ever reaching the
container.

**Role names must begin with `workshop-` or `AmazonBedrockAgentCoreSDK`.**
`lab.template` scopes `iam:PutRolePolicy` to `role/workshop-*`, so the prefix
belongs in the role name and nowhere else. Folding "workshop" into the prefix
itself instead produces `workshopverify-codebuild-role`, which matches neither
granted prefix, and every role is then denied its policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from workshop_lab.selection import (
    WORKSHOP_TAG_KEY,
    WORKSHOP_TAG_VALUE,
    source_bucket_name,
)

# The image the workshop publishes, already built for linux/arm64. Step 8 copies
# it into `image_uri` when CodeBuild produces nothing, which was every time in a
# Vocareum account until 2026-08-07 and is now the exception rather than the
# rule. It is a public source and a private destination: AgentCore Runtime pulls
# only from an ECR repository in the same account.
PREBUILT_IMAGE = "public.ecr.aws/h6l4p0n8/agentcore-verify:verify"


@dataclass(frozen=True)
class Names:
    """Resource names for one run of the notebook, all derived from `prefix`."""

    prefix: str
    account_id: str
    region: str

    def __post_init__(self) -> None:
        if self.prefix.startswith("ws"):
            raise ValueError(
                f"prefix {self.prefix!r} starts with 'ws'. InvokeAgentRuntime "
                "routes any runtime whose name starts with 'ws' to the WebSocket "
                "handler and the call never reaches the container."
            )
        if not self.prefix.isalnum():
            raise ValueError(
                f"prefix {self.prefix!r} must be alphanumeric. It is spliced into "
                "role, repository, and runtime names with different separator "
                "rules, and only an alphanumeric prefix is legal in all of them."
            )

    # --- tags -------------------------------------------------------------
    @property
    def tags_map(self) -> dict[str, str]:
        """Tag form for services that take a dict (IAM, Lambda, AgentCore)."""
        return {WORKSHOP_TAG_KEY: WORKSHOP_TAG_VALUE}

    @property
    def tags_list(self) -> list[dict[str, str]]:
        """Tag form for services that take a list of Key/Value pairs (ECR, DynamoDB)."""
        return [{"Key": WORKSHOP_TAG_KEY, "Value": WORKSHOP_TAG_VALUE}]

    @property
    def tags_query(self) -> str:
        """Tag form for S3 PutObject, which takes a URL-encoded query string.

        S3 is the only service here that does not take a structure. `Tagging` on
        PutObject is the literal `key=value&key=value` form, and it is quoted
        because a value containing `&` or `=` would otherwise be read as another
        pair. The current value needs no quoting; a future one might.
        """
        return urlencode({WORKSHOP_TAG_KEY: WORKSHOP_TAG_VALUE})

    # --- IAM --------------------------------------------------------------
    def role(self, suffix: str) -> str:
        """Role name under the `workshop-` prefix `lab.template` grants against."""
        return f"workshop-{self.prefix}-{suffix}"

    # --- container ---------------------------------------------------------
    @property
    def registry(self) -> str:
        return f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com"

    @property
    def ecr_repository(self) -> str:
        return f"bedrock-agentcore-{self.prefix}"

    @property
    def image_uri(self) -> str:
        return f"{self.registry}/{self.ecr_repository}:{self.prefix}"

    @property
    def source_bucket(self) -> str:
        """The AgentCore toolkit's own bucket name, not one this workshop chose.

        Built by `selection.source_bucket_name` rather than spelled out here,
        because `vocareum_tools.sweep` has to name the same bucket from outside
        the notebook and two spellings of one name is one sweeper walking past
        it.
        """
        return source_bucket_name(self.account_id, self.region)

    @property
    def source_key(self) -> str:
        return f"{self.prefix}/source.zip"

    @property
    def codebuild_project(self) -> str:
        return f"bedrock-agentcore-{self.prefix}-builder"

    # --- AgentCore ----------------------------------------------------------
    @property
    def runtime(self) -> str:
        """Underscore-separated: AgentCore runtime names reject hyphens."""
        return f"{self.prefix}_runtime"

    @property
    def runtime_endpoint(self) -> str:
        return f"{self.prefix}endpoint"

    @property
    def memory(self) -> str:
        return f"{self.prefix}_memory"

    @property
    def gateway(self) -> str:
        return f"{self.prefix}-gateway"

    @property
    def gateway_target(self) -> str:
        return f"{self.prefix}-target"

    # --- other services -----------------------------------------------------
    @property
    def tool_function(self) -> str:
        return f"hotel-booking-{self.prefix}-tool"

    @property
    def secret(self) -> str:
        return f"{self.prefix}/neo4j-command"

    @property
    def table(self) -> str:
        return f"workshop-{self.prefix}-bookings"
