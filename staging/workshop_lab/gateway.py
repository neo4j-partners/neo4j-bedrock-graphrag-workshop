# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/gateway.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Step 11. A Lambda behind an AgentCore Gateway, and a signed call through it.

The workshop exposes its one write operation as a Lambda behind a Gateway, so the
agent discovers a tool rather than being handed database access. This builds that
shape end to end: a Lambda, a Gateway, a target joining them, and a request that
proves the joint works.

Five things here are not obvious and each one has cost a debugging session.

**`credentialProviderConfigurations` is required.** The SDK does not list it as
required and the service rejects a `CreateGatewayTarget` without it.

**`InvokeGateway` has no SDK operation.** The only way to exercise it is a
hand-signed SigV4 request to the Gateway's MCP endpoint, which is what
`call_gateway` is.

**`tools/list` proves nothing about the Lambda.** It is answered from the
Gateway's own configuration and never reaches the function, so it passes on a
Gateway that could not invoke anything. The workshop's agent only ever calls a
tool, so this calls one, and it passes only when the handler's own output comes
back. A refused invoke arrives as HTTP 200 with a JSON-RPC error in the body, so
the status code is not the answer.

**`lambda:AddPermission` is fatal to provisioning.** `provision_agentcore.py`
catches only `ResourceConflictException`, so an `AccessDenied` there stops the
deployment even in an account whose gateway role already carries
`lambda:InvokeFunction` and would not have needed the resource policy. It gets
its own check for that reason.

**`ListGatewayTargets` is measured here rather than in step 5.** Against a
made-up gateway identifier, a policy scoped to the resources you own and a policy
denying the call outright both answer `AccessDeniedException`, so the result
would be unreadable. Against a real gateway it is not. The workshop's cleanup
cannot empty a gateway without this call, and a gateway that cannot be emptied
cannot be deleted and survives the end of the lab.
"""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
import zipfile
from typing import TYPE_CHECKING, Any

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.exceptions import BotoCoreError, ClientError

from workshop_lab.harness import FAIL, PASS, SKIP
from workshop_lab.runtime import READY_STATES

if TYPE_CHECKING:
    from workshop_lab.harness import Harness

# The smallest function the Gateway can call. `HANDLER_MARKER` is the string the
# tool call looks for: it comes out of the Lambda and nowhere else, so finding it
# in the reply is the only proof the call went the whole way.
HANDLER_MARKER = "verification tool"
HANDLER_SOURCE = (
    "def handler(event, context):\n"
    f"    return {{'result': '{HANDLER_MARKER}', 'event': event}}\n"
)

TOOL_NAME = "verify_tool"
TOOL_SCHEMA = {
    "inlinePayload": [
        {
            "name": TOOL_NAME,
            "description": "Returns a fixed string.",
            "inputSchema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        }
    ]
}

# A gateway that has not settled refuses a delete. The leftover from 2026-08-04
# was deleted 34 seconds after its create, the call failed with
# ValidationException, and the gateway was still in the account on 2026-08-06.
GATEWAY_FAILED_STATES = frozenset({"FAILED"})

CREATE_FUNCTION_CHECK = "lambda:CreateFunction"
ADD_PERMISSION_CHECK = "lambda:AddPermission"
CREATE_GATEWAY_CHECK = "agentcore:CreateGateway"
CREATE_TARGET_CHECK = "agentcore:CreateGatewayTarget"
LIST_TARGETS_CHECK = "agentcore:ListGatewayTargets"
INVOKE_CHECK = "agentcore:InvokeGateway"
DISCOVERABLE_CHECK = "gateway targets are discoverable"
TOOL_CALL_CHECK = "gateway tool call reaches the Lambda"


def package() -> bytes:
    """Zip the handler the way CreateFunction's `ZipFile` expects it."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("index.py", HANDLER_SOURCE)
    return buffer.getvalue()


class GatewayBoundary:
    """Builds the Lambda, the Gateway, the target, and calls a tool through them."""

    def __init__(
        self, lab: Harness, lambda_role: str | None, gateway_role: str | None
    ) -> None:
        self.lab = lab
        self.lambda_role = lambda_role
        self.gateway_role = gateway_role
        self.lambda_arn: str | None = None
        self.gateway_id: str | None = None
        self.gateway_url = ""
        self.target_id: str | None = None

    @property
    def awslambda(self) -> Any:
        return self.lab.client("lambda")

    @property
    def control(self) -> Any:
        return self.lab.client("bedrock-agentcore-control")

    # --- Lambda ---------------------------------------------------------------
    def create_function(self) -> str | None:
        """Clear the name, create the function, and register its delete.

        The name is swept first because a re-run of this step against a function
        it already created records `ResourceConflictException` as a FAIL on a
        create the account plainly allows.
        """
        if self.lambda_role is None:
            self.lab.skip(CREATE_FUNCTION_CHECK, "no Lambda role from step 6")
            return None

        name = self.lab.names.tool_function
        self.lab.sweep(
            f"lambda {name}",
            lambda: self.awslambda.delete_function(FunctionName=name),
        )
        self.lab.wait_until_gone(
            lambda: self.awslambda.get_function(FunctionName=name),
            f"lambda {name}",
            timeout=60,
            interval=5,
        )
        zipped = package()
        function = self.lab.check(
            f"{CREATE_FUNCTION_CHECK} {name}",
            lambda: self.lab.retry_while(
                lambda: self.awslambda.create_function(
                    FunctionName=name,
                    Runtime="python3.12",
                    Role=self.lambda_role,
                    Handler="index.handler",
                    Code={"ZipFile": zipped},
                    Timeout=10,
                    Tags=self.lab.names.tags_map,
                ),
                codes={"InvalidParameterValueException"},
                label="create_function",
            ),
        )
        if function is None:
            return None

        self.lambda_arn = function["FunctionArn"]
        self.lab.defer(
            f"lambda {name}",
            lambda: self.awslambda.delete_function(FunctionName=name),
        )
        return self.lambda_arn

    def add_permission(self) -> None:
        """Let the Gateway role invoke the function, the way provisioning does.

        Nothing registers a delete: a resource policy lives on the function and
        goes when the function goes.
        """
        if self.lambda_arn is None or self.gateway_role is None:
            self.lab.skip(
                ADD_PERMISSION_CHECK, "needs both the Lambda and the Gateway role"
            )
            return

        self.lab.check(
            ADD_PERMISSION_CHECK,
            lambda: self.awslambda.add_permission(
                FunctionName=self.lab.names.tool_function,
                StatementId=f"{self.lab.prefix}-gateway-invoke",
                Action="lambda:InvokeFunction",
                Principal=self.gateway_role,
            ),
            "the resource policy provisioning writes before the first tool call",
        )

    # --- Gateway --------------------------------------------------------------
    def sweep_gateway(self) -> None:
        """Empty and delete any gateway already holding this run's name.

        Two things refuse a `DeleteGateway`: a gateway still holding targets, and
        a gateway that has not settled. So wait for the status, empty the
        targets, and only then delete the gateway itself.
        """
        name = self.lab.names.gateway
        try:
            stale = [
                item
                for item in self.control.list_gateways().get("items", [])
                if item.get("name") == name
            ]
            for item in stale:
                self._sweep_one_gateway(item["gatewayId"])
        except ClientError as error:
            code = error.response["Error"]["Code"]
            self.lab.echo(f"      could not sweep gateway {name}: {code}")
        except BotoCoreError as error:
            self.lab.echo(f"      could not sweep gateway {name}: {error}")

    def _sweep_one_gateway(self, leftover: str) -> None:
        self.lab.wait_until(
            lambda: self.control.get_gateway(gatewayIdentifier=leftover)["status"],
            done=READY_STATES,
            failed=GATEWAY_FAILED_STATES,
            label=f"leftover gateway {leftover}",
            timeout=180,
        )
        targets = self.control.list_gateway_targets(gatewayIdentifier=leftover)
        for entry in targets.get("items", []):
            self._sweep_one_target(leftover, entry["targetId"])
        self.lab.sweep(
            f"gateway {leftover}",
            lambda: self.control.delete_gateway(gatewayIdentifier=leftover),
        )
        self.lab.wait_until_gone(
            lambda: self.control.get_gateway(gatewayIdentifier=leftover),
            f"gateway {leftover}",
            timeout=180,
        )

    def _sweep_one_target(self, leftover: str, stale: str) -> None:
        """Its own method so the two closures capture arguments, not a loop name."""
        self.lab.sweep(
            f"gateway target {stale}",
            lambda: self.control.delete_gateway_target(
                gatewayIdentifier=leftover, targetId=stale
            ),
        )
        self.lab.wait_until_gone(
            lambda: self.control.get_gateway_target(
                gatewayIdentifier=leftover, targetId=stale
            ),
            f"gateway target {stale}",
            timeout=120,
        )

    def create_gateway(self) -> str | None:
        """Create the Gateway with the IAM authorizer the signed call needs."""
        if self.gateway_role is None:
            self.lab.skip(CREATE_GATEWAY_CHECK, "no Gateway role from step 6")
            return None

        self.sweep_gateway()
        gateway = self.lab.check(
            CREATE_GATEWAY_CHECK,
            lambda: self.lab.retry_while(
                lambda: self.control.create_gateway(
                    name=self.lab.names.gateway,
                    roleArn=self.gateway_role,
                    protocolType="MCP",
                    authorizerType="AWS_IAM",
                    description="Vocareum environment verification.",
                ),
                codes={"ValidationException"},
                label="create_gateway",
            ),
            "AWS_IAM authorizer, so the signed request below is measurable",
        )
        if gateway is None:
            return None

        self.gateway_id = gateway["gatewayId"]
        self.gateway_url = gateway.get("gatewayUrl", "")
        gateway_id = self.gateway_id
        self.lab.defer(
            f"gateway {gateway_id}",
            lambda: self.control.delete_gateway(gatewayIdentifier=gateway_id),
        )
        self.lab.wait_until(
            lambda: self.control.get_gateway(gatewayIdentifier=gateway_id)["status"],
            done=READY_STATES,
            failed=GATEWAY_FAILED_STATES,
            label=f"gateway {gateway_id}",
        )
        return self.gateway_id

    def create_target(self) -> str | None:
        """Join the Lambda to the Gateway."""
        gateway_id = self.gateway_id
        name = self.lab.names.gateway_target
        target = self.lab.check(
            CREATE_TARGET_CHECK,
            lambda: self.control.create_gateway_target(
                gatewayIdentifier=gateway_id,
                name=name,
                credentialProviderConfigurations=[
                    {"credentialProviderType": "GATEWAY_IAM_ROLE"}
                ],
                targetConfiguration={
                    "mcp": {
                        "lambda": {
                            "lambdaArn": self.lambda_arn,
                            "toolSchema": TOOL_SCHEMA,
                        }
                    }
                },
            ),
            "credentialProviderConfigurations supplied, which the SDK omits",
        )
        if target is None:
            return None

        self.target_id = target["targetId"]
        target_id = self.target_id
        self.lab.defer(
            f"gateway target {target_id}",
            lambda: self.control.delete_gateway_target(
                gatewayIdentifier=gateway_id, targetId=target_id
            ),
        )
        self.lab.wait_until(
            lambda: self.control.get_gateway_target(
                gatewayIdentifier=gateway_id, targetId=target_id
            )["status"],
            done=READY_STATES,
            failed=GATEWAY_FAILED_STATES,
            label=f"target {target_id}",
        )
        return self.target_id

    def list_targets(self) -> None:
        """Ask the gateway for its targets, the way the workshop's cleanup does."""
        gateway_id = self.gateway_id
        listed = self.lab.check(
            LIST_TARGETS_CHECK,
            lambda: self.control.list_gateway_targets(gatewayIdentifier=gateway_id),
            "against a real gateway, the way the workshop's cleanup calls it",
        )
        if listed is None:
            self.lab.record(
                DISCOVERABLE_CHECK,
                FAIL,
                "without this, the cleanup module cannot empty a gateway",
            )
            return
        if self.target_id is None:
            return

        expected = self.lab.names.gateway_target
        names = [item.get("name") for item in listed.get("items", [])]
        if expected in names:
            self.lab.record(DISCOVERABLE_CHECK, PASS, expected)
        else:
            self.lab.record(
                DISCOVERABLE_CHECK,
                FAIL,
                f"created {expected} but the list returned {names}",
            )

    # --- the signed call ------------------------------------------------------
    def call_gateway(self, message: dict[str, Any]) -> tuple[int, str]:
        """Send one signed MCP message to the gateway and return the reply.

        The status is returned rather than raised because the useful answer is in
        the body either way.
        """
        body = json.dumps(message).encode()
        signed = AWSRequest(
            method="POST",
            url=self.gateway_url,
            data=body,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        frozen = self.lab.session.get_credentials().get_frozen_credentials()
        SigV4Auth(frozen, "bedrock-agentcore", self.lab.region).add_auth(signed)
        call = urllib.request.Request(
            self.gateway_url, data=body, headers=dict(signed.headers), method="POST"
        )
        try:
            with urllib.request.urlopen(call, timeout=30) as response:
                return response.status, response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            return error.code, error.read().decode("utf-8", "replace")
        except (TimeoutError, urllib.error.URLError) as error:
            return 0, str(error)

    def list_tools(self) -> None:
        """The cheap half of the invoke check: does the endpoint answer at all?"""
        status, text = self.call_gateway(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        )
        if 200 <= status < 400:
            self.lab.record(INVOKE_CHECK, PASS, f"HTTP {status}")
        else:
            self.lab.record(INVOKE_CHECK, FAIL, f"HTTP {status}: {text[:160]}")

    def call_tool(self) -> None:
        """The half that proves the Lambda is reachable through the Gateway.

        The tool name is the Gateway's own spelling: the target name, three
        underscores, then the name from the tool schema.
        """
        if self.target_id is None:
            self.lab.record(TOOL_CALL_CHECK, SKIP, "no gateway target was created")
            return

        status, text = self.call_gateway(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": f"{self.lab.names.gateway_target}___{TOOL_NAME}",
                    "arguments": {"text": "ping"},
                },
            }
        )
        if not 200 <= status < 400:
            self.lab.record(TOOL_CALL_CHECK, FAIL, f"HTTP {status}: {text[:160]}")
        elif HANDLER_MARKER in text:
            self.lab.record(
                TOOL_CALL_CHECK,
                PASS,
                "the Lambda's own output came back through the Gateway",
            )
        else:
            self.lab.record(
                TOOL_CALL_CHECK,
                FAIL,
                f"HTTP {status} without the Lambda's output: {text[:160]}",
            )

    # --- the step -------------------------------------------------------------
    def run(self) -> str | None:
        """Do the whole step and return the gateway id, or None if none exists."""
        self.create_function()
        self.add_permission()
        if self.create_gateway() is None:
            return None

        if self.lambda_arn is not None:
            self.create_target()
        self.list_targets()

        if not self.gateway_url:
            self.lab.skip(INVOKE_CHECK, "the gateway reported no URL")
            return self.gateway_id

        self.list_tools()
        self.call_tool()
        return self.gateway_id
