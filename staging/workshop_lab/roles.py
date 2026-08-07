# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/roles.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""The four execution roles every later step acts through.

CodeBuild, the AgentCore Runtime, the tool Lambda, and the Gateway each assume a
role of their own rather than sharing one. That is not tidiness: a shared role
would hide which grant is actually missing, and the whole point of this notebook
is to find out which one is.

Three things here are load-bearing and each has already cost a debugging session.

**The `workshop-` prefix belongs in the role name, not in the run prefix.**
`lab.template` scopes `iam:CreateRole` and `iam:PutRolePolicy` to
`role/workshop-*`, so `Names.role()` splices it in. Folding "workshop" into the
run prefix instead yields `workshopverify-codebuild-role`, which matches no
granted prefix, and all four roles are then silently denied their policies.

**The delete is registered between the create and the policy, not after both.**
`iam:PutRolePolicy` is the call most likely to be refused in a locked-down
account. Registering the cleanup only after a successful policy attach would
leave a created role behind on exactly the failure this notebook exists to
detect.

**A role cannot be deleted while it still holds an inline policy.** IAM answers
`DeleteConflict`, not a partial success, so the cleanup empties the role first.
Every earlier version of this that skipped the emptying step reported a clean
account with four roles still in it.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

# AgentCore Runtime and Gateway are both fronted by this one service principal.
AGENTCORE_PRINCIPAL = "bedrock-agentcore.amazonaws.com"

DESCRIPTION = "Vocareum environment verification. Safe to delete."


def allow(actions: Iterable[str]) -> str:
    """Return a one-statement inline policy document granting `actions` on `*`.

    `Resource: "*"` is deliberate. These roles exist to find out whether the
    account permits an action at all, and narrowing the resource would turn an
    organization-level refusal into an indistinguishable resource mismatch.
    """
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": list(actions), "Resource": "*"}
            ],
        }
    )


def trust(principal: str) -> str:
    """Return a trust policy letting one AWS service assume the role."""
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": principal},
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    )


@dataclass(frozen=True)
class RoleSpec:
    """One role: what assumes it, and the least it needs to do its job."""

    suffix: str
    principal: str
    actions: tuple[str, ...]

    @property
    def policy(self) -> str:
        return allow(self.actions)


LOGGING = ("logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents")

ROLE_SPECS: tuple[RoleSpec, ...] = (
    RoleSpec(
        "codebuild-role",
        "codebuild.amazonaws.com",
        (
            *LOGGING,
            # A container push is five separate calls, and a build that can
            # authenticate but not complete an upload fails halfway with a
            # message naming none of them.
            "ecr:GetAuthorizationToken",
            "ecr:BatchCheckLayerAvailability",
            "ecr:InitiateLayerUpload",
            "ecr:UploadLayerPart",
            "ecr:CompleteLayerUpload",
            "ecr:PutImage",
            "ecr:BatchGetImage",
            "s3:GetObject",
            "s3:GetObjectVersion",
        ),
    ),
    RoleSpec(
        "runtime-role",
        AGENTCORE_PRINCIPAL,
        (
            "ecr:GetAuthorizationToken",
            "ecr:BatchGetImage",
            "ecr:GetDownloadUrlForLayer",
            *LOGGING,
        ),
    ),
    RoleSpec("lambda-role", "lambda.amazonaws.com", LOGGING),
    RoleSpec("gateway-role", AGENTCORE_PRINCIPAL, ("lambda:InvokeFunction",)),
)


class Roles:
    """Create the notebook's execution roles and hand back their ARNs.

    Every create and every policy attach is one recorded check, so a locked-down
    account produces a row naming the exact role and call that was refused.
    """

    def __init__(self, lab: Any, specs: Sequence[RoleSpec] = ROLE_SPECS) -> None:
        self.lab = lab
        self.specs = tuple(specs)
        self.arns: dict[str, str | None] = {}

    @property
    def iam(self) -> Any:
        return self.lab.client("iam")

    def _deleter(self, name: str):
        """Return a delete that empties the role first, because IAM demands it."""

        def remove() -> None:
            for attached in self.iam.list_role_policies(RoleName=name)["PolicyNames"]:
                self.iam.delete_role_policy(RoleName=name, PolicyName=attached)
            self.iam.delete_role(RoleName=name)

        return remove

    def create(self, spec: RoleSpec) -> str | None:
        """Create one role with its inline policy. Returns the ARN, or None.

        None means the role is unusable, whether the create or the policy attach
        was refused. A role without its policy is not a role a later step can
        act through, and reporting the ARN anyway would push the failure into a
        step that has nothing to do with it.
        """
        name = self.lab.names.role(spec.suffix)
        created = self.lab.check(
            f"iam:CreateRole {name}",
            lambda: self.iam.create_role(
                RoleName=name,
                AssumeRolePolicyDocument=trust(spec.principal),
                Description=DESCRIPTION,
                Tags=self.lab.names.tags_list,
            ),
        )
        if created is None:
            return None

        self.lab.defer(f"iam role {name}", self._deleter(name))

        attached = self.lab.check(
            f"iam:PutRolePolicy {name}",
            lambda: self.iam.put_role_policy(
                RoleName=name, PolicyName="inline", PolicyDocument=spec.policy
            ),
        )
        if attached is None:
            return None
        return created["Role"]["Arn"]

    def create_all(self) -> dict[str, str | None]:
        """Create every role. Returns ARNs keyed by suffix, None where refused."""
        self.arns = {spec.suffix: self.create(spec) for spec in self.specs}
        return self.arns

    def __getitem__(self, suffix: str) -> str | None:
        return self.arns[suffix]

    @property
    def all_created(self) -> bool:
        return bool(self.arns) and all(arn for arn in self.arns.values())
