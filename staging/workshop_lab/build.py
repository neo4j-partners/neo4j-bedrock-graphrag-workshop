# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/build.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Build the container in CodeBuild, and get an image into ECR either way.

Two things happen here and only one of them usually works.

**The build.** AgentCore Runtime accepts ARM64 images only and this environment
has no Docker daemon, so the build runs in CodeBuild on an ARM container with
`privilegedMode` on, which is the single setting the whole step depends on.

**The fallback.** Vocareum runs an EventBridge rule in every student account
that calls `StopBuild` about five seconds into every build. The build dies in
PROVISIONING, no buildspec command runs, and the log stream stays empty. That is
a restriction on the environment, not a fault in the build definition, and the
report has to say which one it is: a bare FAIL sends people to debug a Dockerfile
that never executed. So the workshop publishes the image it would have built, and
`workshop_lab.registry` copies it into the student's own ECR.

**The fallback is chosen by asking ECR, not by reading the build status.** That
is what makes it self-healing. If Vocareum ever stops killing builds, the image
is already there, the copy does not run, and nothing here needs reverting.
"""

from __future__ import annotations

import json
import urllib.error
from typing import TYPE_CHECKING, Any

from botocore.exceptions import BotoCoreError, ClientError

from workshop_lab.harness import FAIL, INFO, PASS, SKIP
from workshop_lab.naming import PREBUILT_IMAGE
from workshop_lab.registry import copy_image

if TYPE_CHECKING:
    from workshop_lab.harness import Harness

CODEBUILD_ARM_IMAGE = "aws/codebuild/amazonlinux2-aarch64-standard:3.0"
BUILD_TIMEOUT_SECONDS = 1500
BUILD_POLL_SECONDS = 20
LOG_TAIL_LINES = 25

# The phases a build passes through before any buildspec command runs. Stopped in
# one of these means the container never came up.
PRE_COMMAND_PHASES = frozenset({"SUBMITTED", "QUEUED", "PROVISIONING"})
BUILD_FAILED_STATES = frozenset({"FAILED", "FAULT", "STOPPED", "TIMED_OUT"})
ARCHITECTURES = frozenset({"aarch64", "arm64", "x86_64"})

STOPPED_EXPLANATION = """
      Every CodeBuild build in this account is stopped a few seconds after it
      starts, while it is still provisioning. No buildspec command ran, so the
      Dockerfile, the ARM64 environment, and the IAM role are all untested and
      none of them is the cause. Confirm it for yourself:

        aws events list-rules --name-prefix voc-codebuild
        aws cloudtrail lookup-events \\
          --lookup-attributes AttributeKey=EventName,AttributeValue=StopBuild

      The rule lives outside your reach: an SCP denies events:ListTargetsByRule
      to the student role, so only Vocareum can change it. The request is
      written up in support/vocareum-support.md."""


def buildspec(region: str, registry: str, image_uri: str) -> str:
    """The four commands, each of which fails for a different reason.

    `uname -m` prints the build architecture, because anything but `aarch64`
    means the image will not run on AgentCore. `docker login` exercises the
    CodeBuild role. `docker build` pulls the base image from ghcr.io, so a
    failure there is network egress rather than permissions. `docker push`
    writes to the repository.
    """
    return json.dumps(
        {
            "version": "0.2",
            "phases": {
                "pre_build": {
                    "commands": [
                        "uname -m",
                        (
                            f"aws ecr get-login-password --region {region}"
                            " | docker login --username AWS"
                            f" --password-stdin {registry}"
                        ),
                    ]
                },
                "build": {"commands": [f"docker build -t {image_uri} ."]},
                "post_build": {"commands": [f"docker push {image_uri}"]},
            },
        }
    )


def stopped_before_it_started(build: dict[str, Any]) -> bool:
    """True when something called StopBuild before the container came up."""
    if build.get("buildStatus") != "STOPPED":
        return False
    return any(
        phase.get("phaseStatus") == "STOPPED"
        and phase.get("phaseType") in PRE_COMMAND_PHASES
        for phase in build.get("phases", [])
    )


def phase_lines(build: dict[str, Any]) -> list[str]:
    """One line per build phase, plus the reason any phase gave."""
    rendered = []
    for phase in build.get("phases", []):
        status = phase.get("phaseStatus", "")
        seconds = phase.get("durationInSeconds")
        duration = f"{seconds}s" if seconds is not None else ""
        rendered.append(f"{phase['phaseType']:<14} {status:<10} {duration}")
        for context in phase.get("contexts", []):
            reason = context.get("message") or context.get("statusCode") or ""
            if reason:
                rendered.append(f"  {reason}")
    return rendered


def architecture_from(lines: list[str]) -> str:
    """The one line `uname -m` printed, or "unknown" if it never ran."""
    return next(
        (line.strip() for line in lines if line.strip() in ARCHITECTURES), "unknown"
    )


class ContainerBuild:
    """Runs the CodeBuild build, then makes sure an image is in ECR regardless."""

    BUILD_CHECK = "codebuild container build"
    ARCHITECTURE_CHECK = "build architecture is ARM64"
    IMAGE_CHECK = "image present in ECR"

    def __init__(self, lab: Harness, codebuild_role: str | None) -> None:
        self.lab = lab
        self.codebuild_role = codebuild_role
        self.image_pushed = False

    @property
    def codebuild(self):
        return self.lab.client("codebuild")

    @property
    def logs(self):
        return self.lab.client("logs")

    @property
    def ecr(self):
        return self.lab.client("ecr")

    # --- the build ------------------------------------------------------------
    def log_lines(self, build: dict[str, Any]) -> list[str]:
        """The build's log lines, or an empty list if they are unreadable."""
        group = build.get("logs", {}).get("groupName")
        stream = build.get("logs", {}).get("streamName")
        if not group or not stream:
            return []
        try:
            events = self.logs.get_log_events(
                logGroupName=group, logStreamName=stream, startFromHead=True
            )["events"]
        except (BotoCoreError, ClientError) as error:
            self.lab.echo(f"      could not read the build log: {error}")
            return []
        return [event["message"].rstrip() for event in events]

    def create_project(self) -> Any:
        """Create the project, and register its delete.

        Wrapped in `retry_while` on `InvalidInputException` because CodeBuild
        rejects a service role IAM created moments ago, and that is eventual
        consistency rather than a refusal.
        """
        name = self.lab.names.codebuild_project
        names = self.lab.names
        project = self.lab.check(
            "codebuild:CreateProject",
            lambda: self.lab.retry_while(
                lambda: self.codebuild.create_project(
                    name=name,
                    source={
                        "type": "S3",
                        "location": f"{names.source_bucket}/{names.source_key}",
                        "buildspec": buildspec(
                            self.lab.region, names.registry, names.image_uri
                        ),
                    },
                    artifacts={"type": "NO_ARTIFACTS"},
                    environment={
                        "type": "ARM_CONTAINER",
                        "image": CODEBUILD_ARM_IMAGE,
                        "computeType": "BUILD_GENERAL1_MEDIUM",
                        "privilegedMode": True,
                    },
                    serviceRole=self.codebuild_role,
                    tags=[
                        {"key": key, "value": value}
                        for key, value in names.tags_map.items()
                    ],
                ),
                codes={"InvalidInputException"},
                label="create_project",
            ),
            "ARM_CONTAINER with privilegedMode",
        )
        if project is not None:
            self.lab.defer(
                f"codebuild project {name}",
                lambda: self.codebuild.delete_project(name=name),
            )
        return project

    def run_build(self) -> None:
        """Start the build, wait for it, and record what it proved."""
        started = self.lab.check(
            "codebuild:StartBuild",
            lambda: self.codebuild.start_build(
                projectName=self.lab.names.codebuild_project
            ),
        )
        if started is None:
            return

        build_id = started["build"]["id"]
        self.lab.echo(f"      building {build_id}, this takes several minutes")
        state = self.lab.wait_until(
            lambda: self.codebuild.batch_get_builds(ids=[build_id])["builds"][0][
                "buildStatus"
            ],
            done={"SUCCEEDED"},
            failed=BUILD_FAILED_STATES,
            label=f"build {build_id}",
            timeout=BUILD_TIMEOUT_SECONDS,
            interval=BUILD_POLL_SECONDS,
        )
        build = self.codebuild.batch_get_builds(ids=[build_id])["builds"][0]
        lines = self.log_lines(build)
        self.record_outcome(state, build, lines)
        if state != "SUCCEEDED":
            self.report_failure(build, lines)

    def record_outcome(
        self, state: str, build: dict[str, Any], lines: list[str]
    ) -> None:
        """Turn the settled state into the two rows this step owes the tracker."""
        architecture = architecture_from(lines)
        if state == "SUCCEEDED":
            self.lab.record(self.BUILD_CHECK, PASS, f"uname -m: {architecture}")
            if architecture == "aarch64":
                self.lab.record(self.ARCHITECTURE_CHECK, PASS, "aarch64")
            else:
                self.lab.record(
                    self.ARCHITECTURE_CHECK,
                    FAIL,
                    f"uname -m printed {architecture}; AgentCore needs aarch64",
                )
        elif stopped_before_it_started(build):
            self.lab.record(
                self.BUILD_CHECK,
                FAIL,
                "stopped during PROVISIONING by this account, before any"
                " build command ran",
            )
            self.lab.record(
                self.ARCHITECTURE_CHECK, SKIP, "the build container never started"
            )
            self.lab.echo(STOPPED_EXPLANATION)
        else:
            self.lab.record(self.BUILD_CHECK, FAIL, f"settled in {state}")
            self.lab.record(self.ARCHITECTURE_CHECK, SKIP, "the build did not finish")

    def report_failure(self, build: dict[str, Any], lines: list[str]) -> None:
        """Print the phases and the log tail, which name which command failed."""
        self.lab.echo("\n      build phases:")
        for line in phase_lines(build):
            self.lab.echo(f"        {line}")
        if lines:
            self.lab.echo(f"\n      last {LOG_TAIL_LINES} log lines:")
            for line in lines[-LOG_TAIL_LINES:]:
                self.lab.echo(f"        {line}")
        else:
            self.lab.echo("\n      the build wrote no log lines")
        deep_link = build.get("logs", {}).get("deepLink")
        if deep_link:
            self.lab.echo(f"      build log: {deep_link}")

    def build(self) -> None:
        """Everything CodeBuild, or a SKIP saying why none of it ran.

        A step that got no further than CreateProject records no build row and
        no architecture row. There is nothing to say about a build that does not
        exist, and a FAIL there would read as a build that ran and lost.
        """
        if self.codebuild_role is None:
            self.lab.skip("codebuild:CreateProject", "no CodeBuild role from step 6")
            return
        if self.create_project() is None:
            return
        self.run_build()

    # --- the image ------------------------------------------------------------
    def image_in_ecr(self) -> bool:
        """Ask ECR whether the tag exists. This is what picks the fallback."""
        found = self.lab.check(
            "ecr:BatchGetImage pushed image",
            lambda: self.ecr.batch_get_image(
                repositoryName=self.lab.names.ecr_repository,
                imageIds=[{"imageTag": self.lab.prefix}],
            ),
        )
        return bool(found) and bool(found.get("images"))

    def copy_prebuilt(self) -> bool:
        """Copy the published image into this account's ECR."""
        image_uri = self.lab.names.image_uri
        self.lab.record("falling back to the pre-built image", INFO, PREBUILT_IMAGE)
        self.lab.echo(f"      copying {PREBUILT_IMAGE}")
        self.lab.echo(f"           to {image_uri}")
        self.lab.echo("      this moves about 1.3 GB and takes a few minutes")
        try:
            copy_image(PREBUILT_IMAGE, image_uri, self.ecr, self.lab.record)
        except (
            BotoCoreError,
            ClientError,
            RuntimeError,
            urllib.error.URLError,
        ) as error:
            self.lab.record(
                "registry: copied pre-built image to ECR",
                FAIL,
                f"{type(error).__name__}: {error}",
            )
            return False
        return True

    def ensure_image(self) -> bool:
        """Make sure ECR holds the image, whatever the build did."""
        self.image_pushed = self.image_in_ecr() or self.copy_prebuilt()
        if self.image_pushed:
            self.lab.record(self.IMAGE_CHECK, PASS, self.lab.names.image_uri)
        else:
            self.lab.record(
                self.IMAGE_CHECK,
                FAIL,
                "neither CodeBuild nor the registry copy put one there",
            )
        return self.image_pushed

    def run(self) -> bool:
        """Try the build, then make sure there is an image regardless."""
        self.build()
        return self.ensure_image()
