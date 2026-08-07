# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/runtime.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Step 9. Create an AgentCore Runtime, give it an endpoint, and invoke it.

This is the resource the workshop's deployment produces, so it is the one step
whose success means the account can actually run the workshop rather than merely
allow its API calls.

Three things here are measurements rather than plumbing:

**READY is not the same as working.** A Runtime settles in `READY` once the
service has accepted the image. Whether the container inside it starts and
answers its health check is a separate question, and the only way to ask it is to
send a payload and look for it in the answer. So `runtime reached READY` and
`runtime echoed the payload` are two rows, not one. A READY runtime that echoes
nothing is a broken container, which is a different problem from a refusal and
has to read as one.

**CreateAgentRuntime is retried on ValidationException.** The role step 6 created
is not yet a role AgentCore will accept in PassRole, and the refusal arrives as a
validation error rather than as anything that names consistency. Recording that
as FAIL would report a permission the account has as one it does not.

**The endpoint is waited on separately.** Creating it returns immediately and
leaves it `CREATING`; invoking through a qualifier that is not ready yet fails in
a way that looks like a data-plane denial.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from workshop_lab.harness import Harness

# AgentCore has used both names for the same settled state across API versions,
# and a wait that knows only one of them times out on an already-working runtime.
READY_STATES = frozenset({"ACTIVE", "READY"})
FAILED_STATES = frozenset({"CREATE_FAILED", "FAILED"})

CREATE_CHECK = "agentcore:CreateAgentRuntime"
ENDPOINT_CHECK = "agentcore:CreateAgentRuntimeEndpoint"
INVOKE_CHECK = "agentcore:InvokeAgentRuntime"
READY_CHECK = "runtime reached READY"
ECHO_CHECK = "runtime echoed the payload"


class AgentRuntime:
    """Creates the Runtime and its endpoint, then proves the container answers."""

    def __init__(
        self, lab: Harness, image_pushed: bool, runtime_role: str | None
    ) -> None:
        self.lab = lab
        self.image_pushed = image_pushed
        self.runtime_role = runtime_role
        self.runtime_id: str | None = None
        self.runtime_arn: str | None = None

    @property
    def control(self) -> Any:
        return self.lab.client("bedrock-agentcore-control")

    @property
    def dataplane(self) -> Any:
        return self.lab.client("bedrock-agentcore")

    def create(self) -> dict[str, Any] | None:
        """Create the Runtime and register its delete, or record why it could not."""
        if not self.image_pushed:
            self.lab.skip(CREATE_CHECK, "no image in ECR from step 8")
            return None
        if self.runtime_role is None:
            self.lab.skip(CREATE_CHECK, "no Runtime role from step 6")
            return None

        name = self.lab.names.runtime
        runtime = self.lab.check(
            CREATE_CHECK,
            lambda: self.lab.retry_while(
                lambda: self.control.create_agent_runtime(
                    agentRuntimeName=name,
                    agentRuntimeArtifact={
                        "containerConfiguration": {
                            "containerUri": self.lab.names.image_uri
                        }
                    },
                    roleArn=self.runtime_role,
                    networkConfiguration={"networkMode": "PUBLIC"},
                    description="Vocareum environment verification.",
                    tags=self.lab.names.tags_map,
                ),
                codes={"ValidationException"},
                label="create_agent_runtime",
            ),
        )
        if runtime is None:
            return None

        self.runtime_id = runtime["agentRuntimeId"]
        self.runtime_arn = runtime["agentRuntimeArn"]
        runtime_id = self.runtime_id
        self.lab.defer(
            f"agent runtime {runtime_id}",
            lambda: self.control.delete_agent_runtime(agentRuntimeId=runtime_id),
        )
        return runtime

    def wait_for_ready(self) -> str:
        """Poll the Runtime to a settled state and record which one it reached."""
        runtime_id = self.runtime_id
        state = self.lab.wait_until(
            lambda: self.control.get_agent_runtime(agentRuntimeId=runtime_id)["status"],
            done=READY_STATES,
            failed=FAILED_STATES,
            label=f"runtime {runtime_id}",
        )
        if state in READY_STATES:
            self.lab.record(READY_CHECK, "PASS", state)
        else:
            self.lab.record(READY_CHECK, "FAIL", f"settled in {state}")
        return state

    def create_endpoint(self) -> str | None:
        """Create the endpoint and wait for it, returning its settled state.

        `None` means there is no endpoint at all, which is a different outcome
        from an endpoint that exists and did not come up, and the caller records
        a different reason for each.
        """
        runtime_id = self.runtime_id
        name = self.lab.names.runtime_endpoint
        endpoint = self.lab.check(
            ENDPOINT_CHECK,
            lambda: self.control.create_agent_runtime_endpoint(
                agentRuntimeId=runtime_id, name=name, tags=self.lab.names.tags_map
            ),
        )
        if endpoint is None:
            return None

        self.lab.defer(
            f"runtime endpoint {name}",
            lambda: self.control.delete_agent_runtime_endpoint(
                agentRuntimeId=runtime_id, endpointName=name
            ),
        )
        return self.lab.wait_until(
            lambda: self.control.get_agent_runtime_endpoint(
                agentRuntimeId=runtime_id, endpointName=name
            )["status"],
            done=READY_STATES,
            failed=FAILED_STATES,
            label=f"endpoint {name}",
        )

    def invoke(self) -> None:
        """Send a payload through the data plane and look for it in the answer."""
        answer = self.lab.check(
            INVOKE_CHECK,
            lambda: self.dataplane.invoke_agent_runtime(
                agentRuntimeArn=self.runtime_arn,
                qualifier=self.lab.names.runtime_endpoint,
                payload=json.dumps({"ping": self.lab.prefix}).encode(),
            ),
        )
        if answer is None:
            return

        body = answer["response"].read().decode("utf-8", "replace")
        if self.lab.prefix in body:
            self.lab.record(ECHO_CHECK, "PASS", body[:120])
        else:
            self.lab.record(ECHO_CHECK, "FAIL", body[:200])

    def run(self) -> str | None:
        """Do the whole step and return the Runtime id, or None if none exists."""
        if self.create() is None:
            return None

        self.wait_for_ready()
        state = self.create_endpoint()
        if state is None:
            self.lab.skip(INVOKE_CHECK, "no endpoint to invoke")
        elif state not in READY_STATES:
            self.lab.skip(INVOKE_CHECK, f"the endpoint settled in {state}")
        else:
            self.invoke()
        return self.runtime_id
