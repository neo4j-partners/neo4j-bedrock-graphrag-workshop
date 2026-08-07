# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/models.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Step 13b. Call the Claude models the workshop's agents run on.

Every agent in the workshop is a Strands agent, and a Strands agent reaches
Bedrock through `Converse` and `ConverseStream`. Nothing else in this notebook
calls a foundation model at all, so an account can pass every other check here
and still stop lab 4 at its first agent call. That was the state of this notebook
until Vocareum confirmed the Claude 4 series is subscribed for the student
accounts, which made the question worth asking from inside a session.

Two answers arrive as the same failure and belong to different people:

**An IAM or SCP refusal is a permissions gap.** `lab.template` grants
`bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on
`inference-profile/us.anthropic.*`, so a refusal on that path names something the
template, or the organization policy above it, has to fix.

**An entitlement refusal is not.** Anthropic models are gated per account by a
subscription and a use-case submission, Vocareum distributes that entitlement to
the pooled accounts through License Manager, and nothing in this repository
changes the answer. Bedrock reports it in the message body rather than as a code
of its own, and one of its shapes is `AccessDeniedException`, the same code an
IAM shortfall produces. So `verdict_for` reads the message before it reads the
code, and the entitlement markers are tested first. Reporting both as one FAIL
sends a student to the wrong person.

**Both invoke actions are measured, not only the cheaper one.**
`docs/permissions.md` records a session where `InvokeModel` succeeded for a model
whose `InvokeModelWithResponseStream` was refused, same account, same run. A
Strands agent streams by default, so the streaming path is the one the workshop
depends on, and a check that only called `Converse` would have reported that
session ready.

This step creates nothing and registers no teardown, so it is safe to run on its
own after step 2.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from botocore.exceptions import BotoCoreError, ClientError

from workshop_lab.harness import FAIL, PASS, SKIP

if TYPE_CHECKING:
    from workshop_lab.harness import Harness

# Inference-profile ids, not bare model ids. Every Claude 4 model in the
# us-east-1 catalog lists INFERENCE_PROFILE as its only inference type, so a
# bare `anthropic.` id answers with a ValidationException that measures nothing
# about access. Vocareum said the same thing independently in 2026-08-03
# correspondence: invoke through the `us.` or `global.` id.
SONNET_MODEL_ID = "us.anthropic.claude-sonnet-4-6"
OPUS_MODEL_ID = "us.anthropic.claude-opus-4-8"

# The newest 4-series model of each family Vocareum named, and the Sonnet is the
# id the workshop's own labs already carry in MODEL_ID. Pinned rather than picked
# from the live catalog on purpose: a check that chooses its own model reports a
# different model per session, and two sessions then cannot be compared.
MODELS = (
    (SONNET_MODEL_ID, "every agent lab in the workshop calls this one"),
    (OPUS_MODEL_ID, "the newest 4-series Opus"),
)

INVOKE_ACTION = "bedrock:InvokeModel"
STREAM_ACTION = "bedrock:InvokeModelWithResponseStream"

# One turn, one word back. The question is whether the account may call the
# model, so the prompt is the smallest thing that produces text, and a low token
# ceiling keeps a refusal and a success the same price.
PROMPT = "Reply with one word: ready"
MESSAGES = [{"role": "user", "content": [{"text": PROMPT}]}]
INFERENCE_CONFIG = {"maxTokens": 32}

# Anthropic entitlement, in every wording Bedrock has been seen to use for it.
# Tested before the error code, because the third of these arrives as
# AccessDeniedException and an IAM shortfall does too.
ENTITLEMENT_MARKERS = (
    "is not available for this account",
    "use case details",
    "have access to the model",
)

# The Marketplace subscription check Bedrock runs per model and per operation.
# `lab.template` already grants aws-marketplace:Subscribe and ViewSubscriptions,
# so this shape is the subscription itself being absent rather than the
# permission to read it.
MARKETPLACE_MARKER = "aws-marketplace"

# A model id this region's catalog does not carry, which for a pinned id means
# the pin went stale rather than that the account lost anything.
UNKNOWN_MODEL_MARKERS = (
    "model identifier is invalid",
    "could not resolve the foundation model",
)

# The bare-id mistake. Kept as a verdict of its own because the fix is in this
# file and not in the account.
PROFILE_MARKERS = ("inference profile", "on-demand throughput isn't supported")

# Both of the above are `ValidationException` shapes, and both are matched only
# under that code. An IAM refusal names the profile it refused, so its message
# carries the model id and can carry the word profile too; read loosely, that
# would answer a real permission gap with "fix the id in workshop_lab.models"
# and send nobody to the policy that actually refused the call.
BAD_ID_CODE = "ValidationException"

NO_TEXT_DETAIL = "the call returned no text, so the model did not answer"


def verdict_for(code: str, message: str) -> tuple[str, str]:
    """Turn one Bedrock error into a verdict and a line naming who owns it.

    Message first, code second, for the two shapes that share a code. Bedrock
    reports the account-entitlement gate as `AccessDeniedException` with an
    entitlement message, which is the same code an ordinary IAM shortfall
    produces, and the two go to different people. The rest are matched under the
    code AWS actually returns them with, so a message that merely mentions a
    model id cannot be mistaken for one that names a bad model id. Anything
    unmatched keeps its code and its message rather than being guessed at.
    """
    body = message.lower()
    if any(marker in body for marker in ENTITLEMENT_MARKERS):
        return FAIL, f"this account is not entitled to the model: {message[:160]}"
    if MARKETPLACE_MARKER in body:
        return FAIL, f"the model has no Marketplace subscription: {message[:160]}"
    if code == BAD_ID_CODE:
        if any(marker in body for marker in UNKNOWN_MODEL_MARKERS):
            return FAIL, f"Bedrock does not know this model id: {message[:160]}"
        if any(marker in body for marker in PROFILE_MARKERS):
            return FAIL, f"call it by its us. inference-profile id: {message[:160]}"
    if code == "AccessDeniedException":
        return FAIL, f"IAM or an SCP refused the call: {message[:160]}"
    if code == "ThrottlingException":
        return SKIP, "Bedrock throttled the request, so nothing was measured"
    return FAIL, f"{code}: {message[:160]}"


def text_of(response: dict) -> str:
    """The text a `Converse` reply carries, or "" if it carries none."""
    blocks = response.get("output", {}).get("message", {}).get("content", [])
    return " ".join(
        block["text"].strip() for block in blocks if block.get("text")
    ).strip()


def text_of_stream(response: dict) -> str:
    """The text a `ConverseStream` reply carries, read off the event stream.

    A stream that authorizes and then produces no delta is a different outcome
    from one that was refused, and only draining it tells them apart.
    """
    parts = [
        event["contentBlockDelta"]["delta"]["text"]
        for event in response.get("stream", [])
        if event.get("contentBlockDelta", {}).get("delta", {}).get("text")
    ]
    return "".join(parts).strip()


class ModelAccess:
    """Calls each pinned Claude model on both invoke actions and reports."""

    def __init__(self, lab: Harness) -> None:
        self.lab = lab

    @property
    def runtime(self) -> Any:
        return self.lab.client("bedrock-runtime")

    # --- the two calls --------------------------------------------------------
    def converse(self, model_id: str) -> str:
        return text_of(
            self.runtime.converse(
                modelId=model_id,
                messages=MESSAGES,
                inferenceConfig=INFERENCE_CONFIG,
            )
        )

    def converse_stream(self, model_id: str) -> str:
        return text_of_stream(
            self.runtime.converse_stream(
                modelId=model_id,
                messages=MESSAGES,
                inferenceConfig=INFERENCE_CONFIG,
            )
        )

    # --- measuring -----------------------------------------------------------
    def measure(self, action: str, model_id: str, call: Callable[[str], str]) -> str:
        """Run one call and record one row. Returns the verdict.

        Not `Harness.check`: that maps every `ClientError` to FAIL with the code
        and the message, and the whole point here is that two of those messages
        are somebody else's problem.
        """
        name = f"{action} {model_id}"
        try:
            answer = call(model_id)
        except ClientError as error:
            code = error.response["Error"]["Code"]
            message = error.response["Error"].get("Message", "")
            verdict, detail = verdict_for(code, message)
            self.lab.record(name, verdict, detail)
            return verdict
        except BotoCoreError as error:
            self.lab.record(name, FAIL, str(error)[:160])
            return FAIL
        if not answer:
            self.lab.record(name, FAIL, NO_TEXT_DETAIL)
            return FAIL
        self.lab.record(name, PASS, f"the model answered {answer[:40]!r}")
        return PASS

    # --- the step ------------------------------------------------------------
    def run(self) -> bool:
        """Call both models both ways. True only when all four calls answered."""
        verdicts: list[str] = []
        for model_id, why in MODELS:
            self.lab.echo(f"\n{model_id}: {why}")
            verdicts.append(self.measure(INVOKE_ACTION, model_id, self.converse))
            verdicts.append(self.measure(STREAM_ACTION, model_id, self.converse_stream))

        if all(verdict == PASS for verdict in verdicts):
            self.lab.echo("\nOK. Both Claude 4 models answer, streaming and not.")
            return True
        if FAIL not in verdicts:
            self.lab.echo(
                "\nBedrock throttled this. Wait a minute and re-run the cell."
            )
            return False
        self.lab.echo(
            "\nThe agent labs cannot run without these models. Report it and quote"
            "\nthe failing line: an entitlement message is an account subscription,"
            "\na refusal is the lab's own policy, and different people fix them."
        )
        return False
