# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/teardown.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Step 14. Empty the account, and prove it rather than assume it.

**This enumerates the account. It does not replay the deletes the run registered.**
`Harness.cleanups` only ever holds what this kernel created itself, and that lost
resources three ways, all of them observed. A closed tab or a restarted kernel
empties the list while the resources keep running. A re-run step creates nothing
the second time: `CreateGateway verify-gateway` succeeded at 11:48:29Z and the
re-run failed `ConflictException` at 11:48:51Z, so no delete was ever registered
for the gateway that was still live. Worst of the three, an empty list used to
make this step print that the account was empty, reporting success for having
done nothing.

So the cleanups run first as a hint, and enumeration is what decides. This step
stands on steps 0, 2 and 4 alone: if the kernel restarted, run those three and
then this one.

**Two ways to recognise a resource, unioned, because each has a hole the other
covers.** The tag is applied at create time, but `agentcore:TagResource` is
itself a measured permission in step 10, so a refused tag leaves a live resource
untagged and a tag-only sweep walks past it. The names are the templates steps 6
to 12 build out of the prefix. A bare prefix is not enough on its own: the ECR
repository, the CodeBuild project and the Lambda all carry it in the middle of a
longer fixed name.

**Anything CloudFormation owns is left alone.** Vocareum deletes the lab stack
itself at session end. Deleting one of its resources by hand first leaves the
stack to fail its own delete, so nothing on that list is touched here however its
name reads.

**An enumeration that failed is not an empty account.** That is the one thing
this step must never round down to a pass, so a refused listing is recorded and
the verdict at the bottom refuses to report clean while any is outstanding.

Ordering is dependency order, and it is not cosmetic. Endpoints go before the
runtime that holds them, gateway targets before the gateway, the Lambda after the
gateway target that invokes it, the objects before their bucket, and IAM last,
because every role here is passed to something above and IAM will not delete a
role a live service is still using.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from botocore.exceptions import BotoCoreError, ClientError

from workshop_lab.harness import FAIL, GONE_CODES, PASS
from workshop_lab.naming import WORKSHOP_TAG_KEY, WORKSHOP_TAG_VALUE

if TYPE_CHECKING:
    from workshop_lab.harness import Harness

# AgentCore Runtime creates one CloudWatch log group per runtime endpoint under
# this fixed path, and DeleteAgentRuntime does not take it with it. The path is
# documented under bedrock-agentcore/latest/devguide/observability-configure.html.
AGENTCORE_LOG_PREFIX = "/aws/bedrock-agentcore/runtimes/"

EMPTY_CHECK = "account is empty after teardown"


def enumerated_check(label: str) -> str:
    """The tracker row name for one listing. Recorded only when it is refused."""
    return f"teardown enumerated {label}"


def error_code(error: Exception) -> str:
    """Return the AWS error code, or the message for a non-AWS failure."""
    if isinstance(error, ClientError):
        return error.response["Error"]["Code"]
    return str(error)[:120]


def items_of(response: dict) -> list[dict]:
    """Return whichever list key an AgentCore List call answered with.

    The control plane is not consistent about the name: gateways arrive under
    "items", runtimes and memories under keys of their own. Taking the first list
    of objects in the response survives that, and survives a boto3 upgrade
    renaming it, which three hard-coded guesses would not.
    """
    for value in response.values():
        if isinstance(value, list) and all(isinstance(one, dict) for one in value):
            return value
    return []


def carries_workshop_tag(read_tags: Callable[[], Any]) -> bool:
    """True when a resource carries the workshop tag.

    A refused ListTags is not an answer, and it is not fatal either, because the
    name prefixes already recognise everything this notebook creates. So it is
    swallowed and read as "not tagged". AttributeError is in there for the same
    reason step 10 tests `hasattr` before tagging: an older boto3 has no tagging
    operations for AgentCore at all.
    """
    try:
        raw = read_tags()
    except (AttributeError, ClientError, BotoCoreError):
        return False
    if isinstance(raw, dict):
        return raw.get(WORKSHOP_TAG_KEY) == WORKSHOP_TAG_VALUE
    return any(
        (entry.get("Key") or entry.get("key")) == WORKSHOP_TAG_KEY
        and (entry.get("Value") or entry.get("value")) == WORKSHOP_TAG_VALUE
        for entry in raw or []
    )


def gone(operation: str, message: str) -> ClientError:
    """Build the absence error the waiters understand.

    Several describes report a missing resource with something `GONE_CODES` does
    not contain: a bare 404, an empty list, a `projectsNotFound` entry. Each of
    those is renamed here rather than added to `GONE_CODES`, because widening
    that set would make `Harness.check` read a missing bucket as a passing
    `PutObject` in step 7.
    """
    return ClientError(
        {"Error": {"Code": "ResourceNotFoundException", "Message": message}}, operation
    )


@dataclass(frozen=True)
class Target:
    """One resource to delete, and the describe that proves it is gone."""

    label: str
    delete: Callable[[], Any]
    probe: Callable[[], Any]


class Teardown:
    """Enumerates the account, deletes what this notebook owns, confirms it went."""

    def __init__(self, lab: Harness) -> None:
        self.lab = lab
        # A bare prefix does not match every name: the ECR repository, the
        # CodeBuild project and the Lambda carry it in the middle.
        self.name_prefixes = (
            lab.prefix,
            f"workshop-{lab.prefix}",
            f"bedrock-agentcore-{lab.prefix}",
            f"hotel-booking-{lab.prefix}",
        )
        self.stack_owned: set[str] = set()
        self.enumerated: list[str] = []
        self.enumeration_failures: list[str] = []
        # Every runtime id this run decided to delete. The log group sweep waits
        # on these rather than on a clock.
        self.runtime_ids: list[str] = []

    # --- clients --------------------------------------------------------------
    @property
    def control(self) -> Any:
        return self.lab.client("bedrock-agentcore-control")

    @property
    def iam(self) -> Any:
        return self.lab.client("iam")

    @property
    def ecr(self) -> Any:
        return self.lab.client("ecr")

    @property
    def s3(self) -> Any:
        return self.lab.client("s3")

    @property
    def codebuild(self) -> Any:
        return self.lab.client("codebuild")

    @property
    def awslambda(self) -> Any:
        return self.lab.client("lambda")

    @property
    def secrets(self) -> Any:
        return self.lab.client("secretsmanager")

    @property
    def dynamodb(self) -> Any:
        return self.lab.client("dynamodb")

    @property
    def logs(self) -> Any:
        return self.lab.client("logs")

    @property
    def source_bucket_name(self) -> str:
        """Computed from the live account and region, never read out of step 7.

        Rebuilt rather than remembered, for the restarted-kernel case. The name
        is the AgentCore toolkit's own fixed shape, `s3:ListAllMyBuckets` is not
        granted, so this computed name is the only handle there is on the bucket
        and nothing hardcodes it or discovers it by listing.
        """
        return self.lab.names.source_bucket

    # --- listing --------------------------------------------------------------
    def enumerate_all(self, label: str, produce: Callable[[], list[Any]]) -> list[Any]:
        """List one service's resources, recording a refusal rather than raising."""
        self.enumerated.append(label)
        try:
            return produce()
        except (ClientError, BotoCoreError) as error:
            code = error_code(error)
            self.enumeration_failures.append(f"{label}: {code}")
            self.lab.record(enumerated_check(label), FAIL, code)
            return []

    def pages(self, service: Any, operation: str, key: str, **kwargs: Any) -> list[Any]:
        """Collect every page of a paginated List into one flat list."""
        collected: list[Any] = []
        for page in service.get_paginator(operation).paginate(**kwargs):
            collected.extend(page.get(key, []))
        return collected

    def agentcore_all(self, call: Callable[..., dict], **kwargs: Any) -> list[dict]:
        """Collect every page of an AgentCore List call.

        These operations have no boto3 paginator, and a leftover from an earlier
        session is exactly the thing that would be sitting on page two.
        """
        collected: list[dict] = []
        token = None
        while True:
            page = call(**kwargs, nextToken=token) if token else call(**kwargs)
            collected.extend(items_of(page))
            token = page.get("nextToken")
            if not token:
                return collected

    def agentcore_tags(self, arn: str) -> Callable[[], Any]:
        """Return a reader for one AgentCore resource's tags."""
        return lambda: self.control.list_tags_for_resource(resourceArn=arn).get(
            "tags", {}
        )

    # --- selection ------------------------------------------------------------
    def read_stack_owned(self) -> set[str]:
        """Every physical id CloudFormation is currently responsible for.

        The four `workshop-{prefix}` roles are created by step 6 rather than by
        the stack, so they are not on this list and are in scope.

        A failure here is printed rather than recorded. The list only ever widens
        what is skipped, and no name below matches a `lab.template` resource, so
        losing it cannot delete anything extra. Losing it quietly could.
        """
        try:
            cfn = self.lab.client("cloudformation")
            owned: set[str] = set()
            for summary in self.pages(cfn, "list_stacks", "StackSummaries"):
                if summary.get("StackStatus") == "DELETE_COMPLETE":
                    continue
                for resource in self.pages(
                    cfn,
                    "list_stack_resources",
                    "StackResourceSummaries",
                    StackName=summary["StackName"],
                ):
                    physical = resource.get("PhysicalResourceId") or ""
                    if physical:
                        owned.add(physical)
                        owned.add(physical.rsplit("/", 1)[-1])
            self.stack_owned = owned
            self.lab.echo(
                f"CloudFormation owns {len(owned)} names. Those are left alone."
            )
        except (ClientError, BotoCoreError) as error:
            self.stack_owned = set()
            self.lab.echo(
                f"      could not read CloudFormation stacks: {error_code(error)}"
            )
            self.lab.echo("      nothing is skipped on that basis; the filters decide")
        return self.stack_owned

    def ours(
        self, name: str, arn: str = "", read_tags: Callable[[], Any] | None = None
    ) -> bool:
        """True when this notebook created the resource, by name or by tag."""
        if name in self.stack_owned or (arn and arn in self.stack_owned):
            return False
        if any(name.startswith(one) for one in self.name_prefixes):
            return True
        return read_tags is not None and carries_workshop_tag(read_tags)

    # --- deletes that need more than one call ---------------------------------
    def delete_gateway_when_drained(self, gateway: str) -> None:
        """Delete a gateway once its targets are gone and its own status settled.

        Two things refuse a DeleteGateway: a gateway still holding targets, and a
        gateway that has not settled. The gateway leaked on 2026-08-04 was
        deleted 34 seconds after its create, the call failed
        `ValidationException`, and the gateway was still in the account two days
        later. The target deletes are separate entries ahead of this one so each
        is reported on its own, but DeleteGatewayTarget returns before the target
        is gone, so the wait for an empty gateway belongs here.
        """
        self.lab.wait_until(
            lambda: (
                "empty"
                if not self.agentcore_all(
                    self.control.list_gateway_targets, gatewayIdentifier=gateway
                )
                else "holding targets"
            ),
            done={"empty"},
            failed=set(),
            label=f"targets of gateway {gateway}",
            timeout=180,
        )
        self.lab.wait_until(
            lambda: self.control.get_gateway(gatewayIdentifier=gateway)["status"],
            done={"ACTIVE", "READY"},
            failed={"FAILED"},
            label=f"gateway {gateway}",
            timeout=180,
        )
        self.control.delete_gateway(gatewayIdentifier=gateway)

    def remove_role(self, name: str) -> None:
        """Empty a role first, because IAM refuses to delete one that is not."""
        for inline in self.iam.list_role_policies(RoleName=name)["PolicyNames"]:
            self.iam.delete_role_policy(RoleName=name, PolicyName=inline)
        for managed in self.iam.list_attached_role_policies(RoleName=name)[
            "AttachedPolicies"
        ]:
            self.iam.detach_role_policy(RoleName=name, PolicyArn=managed["PolicyArn"])
        self.iam.delete_role(RoleName=name)

    def delete_log_group_when_runtimes_gone(self, name: str) -> None:
        """Delete an endpoint log group, but not until its runtime has gone.

        An AgentCore Runtime takes 100 seconds or more to disappear after its
        delete call returns, and it keeps writing to its endpoint log group for
        the whole of that window. A DeleteLogGroup issued inside it is undone by
        the next write: the delete succeeds, this step reports the group gone,
        and the group is back in the account a few seconds later. So wait for the
        runtimes first. A group left over from an earlier session has no runtime
        left to wait on, and `wait_until_gone` returns on its first describe.
        """
        for runtime in self.runtime_ids:
            self.lab.wait_until_gone(
                lambda runtime=runtime: self.control.get_agent_runtime(
                    agentRuntimeId=runtime
                ),
                f"agent runtime {runtime}, before deleting its log group",
                timeout=420,
            )
        self.logs.delete_log_group(logGroupName=name)

    def empty_source_bucket(self, keys: list[str]) -> None:
        """Delete the listed objects from the build-source bucket, 1000 at a time.

        DeleteObjects takes at most 1000 keys per call, so the keys are batched.
        It also answers HTTP 200 while refusing individual keys in an Errors
        list, so a partial failure is silent unless Errors is read. It is read
        here, printed, and turned into the ClientError the delete loop knows how
        to report. A call with no keys is itself an error, which the empty range
        already skips.

        ExpectedBucketOwner matters most on this call. It is what makes a name
        computed for the wrong account fail loudly instead of emptying a bucket
        belonging to someone else.
        """
        for start in range(0, len(keys), 1000):
            batch = keys[start : start + 1000]
            answer = self.s3.delete_objects(
                Bucket=self.source_bucket_name,
                Delete={"Objects": [{"Key": key} for key in batch], "Quiet": True},
                ExpectedBucketOwner=self.lab.account_id,
            )
            errors = answer.get("Errors") or []
            if not errors:
                continue
            for entry in errors[:5]:
                self.lab.echo(f"      refused {entry.get('Key')}: {entry.get('Code')}")
            raise ClientError(
                {
                    "Error": {
                        "Code": errors[0].get("Code") or "DeleteObjectsFailed",
                        "Message": f"{len(errors)} of {len(batch)} keys refused",
                    }
                },
                "DeleteObjects",
            )

    def delete_source_bucket(self, bucket: str) -> None:
        """Delete the emptied build-source bucket, naming versions if it refuses.

        BucketNotEmpty is retried, because the object delete is one target ahead
        of this one. A bucket still not empty after that holds something this
        step does not delete, and there is one such thing: a non-current object
        version or a delete marker. Nothing here calls ListObjectVersions, and
        `lab.template` does not grant `s3:ListBucketVersions`, so a bucket that
        ever had versioning enabled keeps hidden objects and refuses its own
        delete. That is reported rather than worked around, because deleting
        versions widens this sweep further than it has been agreed to go.
        """
        try:
            self.lab.retry_while(
                lambda: self.s3.delete_bucket(
                    Bucket=bucket, ExpectedBucketOwner=self.lab.account_id
                ),
                codes={"BucketNotEmpty"},
                label=f"delete bucket {bucket}",
                timeout=60,
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == "BucketNotEmpty":
                self.lab.echo(
                    f"      {bucket} is still not empty after every object in it was"
                )
                self.lab.echo(
                    "      deleted. The likely cause is object versioning: this step"
                )
                self.lab.echo(
                    "      deletes current objects only, so non-current versions and"
                )
                self.lab.echo(
                    "      delete markers survive and hold the bucket. Empty it in the"
                )
                self.lab.echo(
                    "      S3 console, which does delete versions, then re-run."
                )
            raise

    # --- probes that rename absence -------------------------------------------
    def codebuild_probe(self, name: str) -> Any:
        """Describe a CodeBuild project, reporting absence the way the others do.

        BatchGetProjects answers a missing project with an empty list and a
        `projectsNotFound` entry rather than an error, so `wait_until_gone` would
        wait out its whole timeout and then call a deleted project present.
        """
        found = self.codebuild.batch_get_projects(names=[name])
        if not found.get("projects"):
            raise gone("BatchGetProjects", name)
        return found["projects"][0]

    def log_group_tags(self, name: str) -> Callable[[], Any]:
        """Return a reader for one log group's tags.

        ListTagsForResource wants the log group ARN without the trailing ":*"
        that DescribeLogGroups puts on its `arn` field, so the ARN is built from
        the name here rather than read back out of the listing.
        """
        arn = f"arn:aws:logs:{self.lab.region}:{self.lab.account_id}:log-group:{name}"
        return lambda: self.logs.list_tags_for_resource(resourceArn=arn).get("tags", {})

    def log_group_probe(self, name: str) -> Any:
        """Describe one log group, reporting absence the way the others do.

        DescribeLogGroups answers a missing group with an empty list rather than
        an error, and `logGroupNamePrefix` is a prefix, so a surviving group has
        to be matched exactly. Without both, `wait_until_gone` would sit out its
        whole timeout and then call a deleted group present.
        """
        listed = self.logs.describe_log_groups(logGroupNamePrefix=name)
        for group in listed.get("logGroups", []):
            if group.get("logGroupName") == name:
                return group
        raise gone("DescribeLogGroups", name)

    def s3_bucket_probe(self) -> Any:
        """Head the build-source bucket, renaming absence to a code probes accept.

        HeadBucket answers a missing bucket with a bare 404 and no body, so boto3
        reports the code as "404", which is not in `GONE_CODES`.
        """
        try:
            return self.s3.head_bucket(
                Bucket=self.source_bucket_name,
                ExpectedBucketOwner=self.lab.account_id,
            )
        except ClientError as error:
            if error.response["Error"]["Code"] in {"404", "NoSuchBucket"}:
                raise gone("HeadBucket", self.source_bucket_name) from error
            raise

    def source_objects_probe(self) -> Any:
        """Report an emptied bucket the way the other probes report an absent one.

        An emptied bucket answers ListObjectsV2 with a 200 carrying no Contents
        rather than with an error, and a bucket the target after this one has
        already deleted answers NoSuchBucket. Both mean the objects are gone.
        """
        try:
            listed = self.s3.list_objects_v2(
                Bucket=self.source_bucket_name,
                MaxKeys=1,
                ExpectedBucketOwner=self.lab.account_id,
            )
        except ClientError as error:
            if error.response["Error"]["Code"] in {"NoSuchBucket", "404"}:
                raise gone("ListObjectsV2", "no objects left") from error
            raise
        if not listed.get("Contents"):
            raise gone("ListObjectsV2", "no objects left")
        return listed

    def build_sources(self) -> list[dict]:
        """List every object in the build-source bucket, absent bucket as none.

        No Prefix. A prefix is derived from the current session, so a
        prefix-scoped sweep walks past an earlier session's objects, those
        objects hold the bucket non-empty, DeleteBucket then refuses forever and
        the student has no way past it. The bucket lives in one student's
        disposable account and holds AgentCore build sources only.

        `pages` drives the boto3 paginator, which is what carries this past the
        1000 keys ListObjectsV2 returns in one call, and an account that has run
        the workshop several times has more than that.
        """
        try:
            return self.pages(
                self.s3,
                "list_objects_v2",
                "Contents",
                Bucket=self.source_bucket_name,
                ExpectedBucketOwner=self.lab.account_id,
            )
        except ClientError as error:
            if error.response["Error"]["Code"] in {"NoSuchBucket", "404"}:
                return []
            raise

    # --- collection, in dependency order --------------------------------------
    def collect_runtimes(self) -> list[Target]:
        """Runtime endpoints, then the runtimes that hold them.

        The DEFAULT endpoint belongs to the service rather than to this notebook.
        """
        targets: list[Target] = []
        for item in self.enumerate_all(
            "agent runtimes",
            lambda: self.agentcore_all(self.control.list_agent_runtimes),
        ):
            runtime = item.get("agentRuntimeId") or ""
            name = item.get("agentRuntimeName") or ""
            arn = item.get("agentRuntimeArn") or ""
            if not runtime or not self.ours(
                name or runtime, arn, self.agentcore_tags(arn)
            ):
                continue
            targets.extend(self._endpoint_targets(runtime))
            targets.append(self._runtime_target(runtime, name))
            self.runtime_ids.append(runtime)
        return targets

    def _endpoint_targets(self, runtime: str) -> list[Target]:
        targets: list[Target] = []
        for endpoint in self.enumerate_all(
            f"endpoints of runtime {runtime}",
            lambda: self.agentcore_all(
                self.control.list_agent_runtime_endpoints, agentRuntimeId=runtime
            ),
        ):
            name = endpoint.get("name") or ""
            if not name or name == "DEFAULT":
                continue
            targets.append(self._endpoint_target(runtime, name))
        return targets

    def _endpoint_target(self, runtime: str, endpoint: str) -> Target:
        return Target(
            f"runtime endpoint {runtime}/{endpoint}",
            lambda: self.control.delete_agent_runtime_endpoint(
                agentRuntimeId=runtime, endpointName=endpoint
            ),
            lambda: self.control.get_agent_runtime_endpoint(
                agentRuntimeId=runtime, endpointName=endpoint
            ),
        )

    def _runtime_target(self, runtime: str, name: str) -> Target:
        return Target(
            f"agent runtime {runtime} {name}",
            lambda: self.control.delete_agent_runtime(agentRuntimeId=runtime),
            lambda: self.control.get_agent_runtime(agentRuntimeId=runtime),
        )

    def collect_runtime_log_groups(self) -> list[Target]:
        """The per-endpoint log groups a deleted runtime leaves behind.

        Deleting a runtime does not delete them, so a hand cleanup of one account
        found log groups for runtimes that no longer existed, still billing for
        stored bytes.

        The name under the fixed path starts with `<agentRuntimeId>-`, and the
        runtime id starts with the runtime name, so the same prefix filter
        recognises these. The tag union stays anyway: the service creates these
        groups, not this notebook, so a group carrying no workshop tag is the
        ordinary case rather than a sign that TagResource was refused.
        """
        targets: list[Target] = []
        for item in self.enumerate_all(
            "agentcore runtime log groups",
            lambda: self.pages(
                self.logs,
                "describe_log_groups",
                "logGroups",
                logGroupNamePrefix=AGENTCORE_LOG_PREFIX,
            ),
        ):
            name = item.get("logGroupName") or ""
            if not name:
                continue
            # A log group's CloudFormation physical id is its own name, so the
            # name is what the stack-owned half of ours() needs. The tail goes in
            # the first slot for the prefix match, which the fixed /aws/... path
            # would otherwise never satisfy.
            tail = name.removeprefix(AGENTCORE_LOG_PREFIX)
            if not self.ours(tail, name, self.log_group_tags(name)):
                continue
            targets.append(self._log_group_target(name))
        return targets

    def _log_group_target(self, name: str) -> Target:
        return Target(
            f"log group {name}",
            lambda: self.delete_log_group_when_runtimes_gone(name),
            lambda: self.log_group_probe(name),
        )

    def collect_gateways(self) -> list[Target]:
        """Gateway targets first, then the gateway, which waits itself out."""
        targets: list[Target] = []
        for item in self.enumerate_all(
            "gateways", lambda: self.agentcore_all(self.control.list_gateways)
        ):
            gateway = item.get("gatewayId") or ""
            name = item.get("name") or ""
            arn = item.get("gatewayArn") or ""
            if not gateway or not self.ours(
                name or gateway, arn, self.agentcore_tags(arn)
            ):
                continue
            targets.extend(self._gateway_target_targets(gateway))
            targets.append(self._gateway_target(gateway, name))
        return targets

    def _gateway_target_targets(self, gateway: str) -> list[Target]:
        targets: list[Target] = []
        for entry in self.enumerate_all(
            f"targets of gateway {gateway}",
            lambda: self.agentcore_all(
                self.control.list_gateway_targets, gatewayIdentifier=gateway
            ),
        ):
            target = entry.get("targetId") or ""
            if not target:
                continue
            targets.append(self._one_gateway_target(gateway, target))
        return targets

    def _one_gateway_target(self, gateway: str, target: str) -> Target:
        return Target(
            f"gateway target {gateway}/{target}",
            lambda: self.control.delete_gateway_target(
                gatewayIdentifier=gateway, targetId=target
            ),
            lambda: self.control.get_gateway_target(
                gatewayIdentifier=gateway, targetId=target
            ),
        )

    def _gateway_target(self, gateway: str, name: str) -> Target:
        return Target(
            f"gateway {gateway} {name}",
            lambda: self.delete_gateway_when_drained(gateway),
            lambda: self.control.get_gateway(gatewayIdentifier=gateway),
        )

    def collect_memories(self) -> list[Target]:
        """A memory's id is its name plus a suffix, and that id is the only place
        the name appears in a List response."""
        targets: list[Target] = []
        for item in self.enumerate_all(
            "memories", lambda: self.agentcore_all(self.control.list_memories)
        ):
            memory = item.get("id") or item.get("memoryId") or ""
            arn = item.get("arn") or ""
            if not memory or not self.ours(memory, arn, self.agentcore_tags(arn)):
                continue
            targets.append(self._memory_target(memory))
        return targets

    def _memory_target(self, memory: str) -> Target:
        return Target(
            f"memory {memory}",
            lambda: self.control.delete_memory(memoryId=memory),
            lambda: self.control.get_memory(memoryId=memory),
        )

    def collect_functions(self) -> list[Target]:
        """Lambda, deleted after the gateway target that invokes it."""
        targets: list[Target] = []
        for item in self.enumerate_all(
            "lambda functions",
            lambda: self.pages(self.awslambda, "list_functions", "Functions"),
        ):
            function = item.get("FunctionName") or ""
            arn = item.get("FunctionArn") or ""
            if not function or not self.ours(function, arn, self._function_tags(arn)):
                continue
            targets.append(self._function_target(function))
        return targets

    def _function_tags(self, arn: str) -> Callable[[], Any]:
        return lambda: self.awslambda.list_tags(Resource=arn).get("Tags", {})

    def _function_target(self, function: str) -> Target:
        return Target(
            f"lambda {function}",
            lambda: self.awslambda.delete_function(FunctionName=function),
            lambda: self.awslambda.get_function(FunctionName=function),
        )

    def collect_codebuild_projects(self) -> list[Target]:
        """Name only: step 8 passes the tags in the CreateProject request itself,
        so a project that exists untagged is not a case that can arise, and
        reading tags would mean one BatchGetProjects per project in the account.
        """
        targets: list[Target] = []
        for name in self.enumerate_all(
            "codebuild projects",
            lambda: self.pages(self.codebuild, "list_projects", "projects"),
        ):
            if not self.ours(name):
                continue
            targets.append(self._codebuild_target(name))
        return targets

    def _codebuild_target(self, name: str) -> Target:
        return Target(
            f"codebuild project {name}",
            lambda: self.codebuild.delete_project(name=name),
            lambda: self.codebuild_probe(name),
        )

    def collect_ecr_repositories(self) -> list[Target]:
        """force, because the repository holds the image step 8 put in it and
        DeleteRepository refuses a repository that is not empty."""
        targets: list[Target] = []
        for item in self.enumerate_all(
            "ecr repositories",
            lambda: self.pages(self.ecr, "describe_repositories", "repositories"),
        ):
            repo = item.get("repositoryName") or ""
            arn = item.get("repositoryArn") or ""
            if not repo or not self.ours(repo, arn, self._repository_tags(arn)):
                continue
            targets.append(self._repository_target(repo))
        return targets

    def _repository_tags(self, arn: str) -> Callable[[], Any]:
        return lambda: self.ecr.list_tags_for_resource(resourceArn=arn).get("tags", [])

    def _repository_target(self, repo: str) -> Target:
        return Target(
            f"ecr repository {repo}",
            lambda: self.ecr.delete_repository(repositoryName=repo, force=True),
            lambda: self.ecr.describe_repositories(repositoryNames=[repo]),
        )

    def collect_tables(self) -> list[Target]:
        """DeleteTable refuses a table that is not ACTIVE, and tagging leaves a
        new table busy for longer than the item calls take, so the refusal is
        waited out rather than counted."""
        targets: list[Target] = []
        for name in self.enumerate_all(
            "dynamodb tables",
            lambda: self.pages(self.dynamodb, "list_tables", "TableNames"),
        ):
            arn = (
                f"arn:aws:dynamodb:{self.lab.region}:{self.lab.account_id}:table/{name}"
            )
            if not self.ours(name, arn, self._table_tags(arn)):
                continue
            targets.append(self._table_target(name))
        return targets

    def _table_tags(self, arn: str) -> Callable[[], Any]:
        return lambda: self.dynamodb.list_tags_of_resource(ResourceArn=arn).get(
            "Tags", []
        )

    def _table_target(self, name: str) -> Target:
        return Target(
            f"dynamodb table {name}",
            lambda: self.lab.retry_while(
                lambda: self.dynamodb.delete_table(TableName=name),
                codes={"ResourceInUseException"},
                label=f"delete table {name}",
                timeout=180,
            ),
            lambda: self.dynamodb.describe_table(TableName=name),
        )

    def collect_secrets(self) -> list[Target]:
        """ForceDeleteWithoutRecovery, because an ordinary delete only schedules
        one and holds the name for the recovery window, which is seven days at
        the shortest. The next run of this notebook could not create it."""
        targets: list[Target] = []
        for item in self.enumerate_all(
            "secrets", lambda: self.pages(self.secrets, "list_secrets", "SecretList")
        ):
            name = item.get("Name") or ""
            arn = item.get("ARN") or ""
            if not name or not self.ours(name, arn, self._secret_tags(item)):
                continue
            targets.append(self._secret_target(name, arn))
        return targets

    def _secret_tags(self, item: dict) -> Callable[[], Any]:
        return lambda: item.get("Tags", [])

    def _secret_target(self, name: str, arn: str) -> Target:
        return Target(
            f"secret {name}",
            lambda: self.secrets.delete_secret(
                SecretId=arn, ForceDeleteWithoutRecovery=True
            ),
            lambda: self.secrets.describe_secret(SecretId=arn),
        )

    def collect_source_bucket(self) -> list[Target]:
        """Everything in the build-source bucket, then the bucket itself, which
        is ordered second because DeleteBucket refuses a bucket that is not empty.

        Its name matches none of the workshop prefixes and the toolkit creates it
        untagged, so `ours` cannot recognise it. What identifies it is the name
        being the one computed from this account and this region.

        The stack-owned check is still consulted, because `lab.template` creates
        an S3 bucket of its own and deleting a stack's resource by hand leaves
        the stack to fail its own delete at session end. Both the objects and the
        bucket sit inside that check, so a stack-owned bucket is not emptied
        either.
        """
        targets: list[Target] = []
        for bucket in self.enumerate_all("build source bucket", self._source_bucket):
            if bucket in self.stack_owned:
                self.lab.echo(f"      {bucket} belongs to a stack, so it is left alone")
                continue
            keys = [
                item["Key"]
                for item in self.enumerate_all(
                    "build sources in s3", self.build_sources
                )
                if item.get("Key")
            ]
            if keys:
                targets.append(self._source_objects_target(bucket, keys))
            targets.append(self._source_bucket_target(bucket))
        return targets

    def _source_bucket(self) -> list[str]:
        """Return the bucket's name if it is there, or nothing if it is not.

        A 403 is deliberately not swallowed. It means the bucket exists and this
        session cannot see it, which is a refused listing rather than an empty
        account, and `enumerate_all` is what has to hear about that.
        """
        try:
            self.s3_bucket_probe()
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                return []
            raise
        return [self.source_bucket_name]

    def _source_objects_target(self, bucket: str, keys: list[str]) -> Target:
        return Target(
            f"{len(keys)} objects in s3 bucket {bucket}",
            lambda: self.empty_source_bucket(keys),
            self.source_objects_probe,
        )

    def _source_bucket_target(self, bucket: str) -> Target:
        return Target(
            f"s3 bucket {bucket}",
            lambda: self.delete_source_bucket(bucket),
            self.s3_bucket_probe,
        )

    def collect_roles(self) -> list[Target]:
        """IAM last. Every role here is passed to something above, and IAM will
        not delete a role a live service is still using.

        Name only, on purpose. ListRoles returns no tags, so a tag union would
        cost one ListRoleTags per role in the account, Vocareum's own included.
        Step 6 cannot name these roles anything else either: `lab.template`
        scopes `iam:PutRolePolicy` to `role/workshop-*`, so an untagged role
        still matches.
        """
        targets: list[Target] = []
        for item in self.enumerate_all(
            "iam roles", lambda: self.pages(self.iam, "list_roles", "Roles")
        ):
            role = item.get("RoleName") or ""
            if not role or not self.ours(role, item.get("Arn") or ""):
                continue
            targets.append(self._role_target(role))
        return targets

    def _role_target(self, role: str) -> Target:
        return Target(
            f"iam role {role}",
            lambda: self.remove_role(role),
            lambda: self.iam.get_role(RoleName=role),
        )

    def collect(self) -> list[Target]:
        """Every target, in the order they have to be deleted in."""
        self.lab.echo("\nEnumerating the account for anything this notebook owns:")
        return [
            *self.collect_runtimes(),
            *self.collect_runtime_log_groups(),
            *self.collect_gateways(),
            *self.collect_memories(),
            *self.collect_functions(),
            *self.collect_codebuild_projects(),
            *self.collect_ecr_repositories(),
            *self.collect_tables(),
            *self.collect_secrets(),
            *self.collect_source_bucket(),
            *self.collect_roles(),
        ]

    # --- the run --------------------------------------------------------------
    def run_hints(self) -> None:
        """Replay this kernel's own deletes, newest first.

        They are quick and already dependency-safe, because they are in reverse
        order of creation. A hint that fails is not a finding: the enumeration
        covers the same resources and it is the one that decides.
        """
        self.lab.echo("Running the CLEANUPS hints. Enumeration below is what decides.")
        if not self.lab.cleanups:
            self.lab.echo(
                "      no hints registered: nothing was created here, or this"
            )
            self.lab.echo("      kernel restarted. The enumeration is the real answer.")
        for label, delete in reversed(self.lab.cleanups):
            try:
                # Deleting an endpoint returns before the endpoint is gone, and
                # the runtime refuses to go while one still exists. That conflict
                # is a timing artifact, so it is waited out rather than reported.
                self.lab.retry_while(delete, codes={"ConflictException"}, label=label)
                self.lab.echo(f"deleted  {label}")
            except (ClientError, BotoCoreError) as error:
                code = error_code(error)
                if code in GONE_CODES:
                    self.lab.echo(f"absent   {label}")
                else:
                    self.lab.echo(
                        f"hint     {label}: {code}, leaving it to the enumeration"
                    )

    def report_plan(self, targets: list[Target]) -> None:
        if targets:
            self.lab.echo(
                f"      {len(targets)} resources to delete, in dependency order:"
            )
            for target in targets:
                self.lab.echo(f"        {target.label}")
        else:
            self.lab.echo(f"      nothing found across {len(self.enumerated)} listings")

    def delete_all(self, targets: list[Target]) -> list[str]:
        """Delete every target and return the ones that refused."""
        failed: list[str] = []
        for target in targets:
            try:
                self.lab.retry_while(
                    target.delete, codes={"ConflictException"}, label=target.label
                )
                self.lab.echo(f"deleted  {target.label}")
            except (ClientError, BotoCoreError) as error:
                code = error_code(error)
                if code in GONE_CODES:
                    self.lab.echo(f"absent   {target.label}")
                else:
                    failed.append(f"{target.label}: {code}")
                    self.lab.echo(f"FAILED   {target.label}: {code}")
        return failed

    def confirm(self, targets: list[Target]) -> list[str]:
        """Poll every target until it is gone, and return the ones that are not.

        A delete that returned is not a delete that finished. Skipping this
        claimed a clean account five separate times while resources were still
        in it.
        """
        self.lab.echo(
            "\nConfirming each resource is gone rather than assuming the delete took:"
        )
        still_present: list[str] = []
        for target in targets:
            if self.lab.wait_until_gone(target.probe, target.label):
                self.lab.echo(f"gone     {target.label}")
            else:
                still_present.append(target.label)
                self.lab.echo(f"PRESENT  {target.label}")
        if not targets:
            self.lab.echo("      nothing to confirm")
        return still_present

    def report(
        self, targets: list[Target], failed: list[str], still_present: list[str]
    ) -> bool:
        """Record the one verdict this step exists to produce."""
        if self.enumeration_failures or still_present:
            self.lab.record(
                EMPTY_CHECK,
                FAIL,
                f"{len(self.enumeration_failures)} listings refused,"
                f" {len(still_present)} still present,"
                f" {len(failed)} delete errors",
            )
            self.lab.echo(
                "\nRe-run this cell. Anything still present after that has to be"
                " deleted"
            )
            self.lab.echo(
                "in the AWS console. Ending the session removes the lab stack and"
            )
            self.lab.echo(
                "nothing else, so whatever is left here keeps running and costing."
            )
            return False
        self.lab.record(
            EMPTY_CHECK,
            PASS,
            f"{len(self.enumerated)} listings read,"
            f" {len(targets)} resources confirmed gone",
        )
        return True

    def run(self) -> bool:
        """Do the whole step. True when the account is measured empty."""
        self.read_stack_owned()
        self.run_hints()
        targets = self.collect()
        self.report_plan(targets)
        failed = self.delete_all(targets)
        still_present = self.confirm(targets)
        return self.report(targets, failed, still_present)
