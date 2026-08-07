# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/selection.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""What counts as this workshop's resource, in one place for both sweepers.

Two programs delete this workshop's leftovers out of a student account, and
neither can become the other. `workshop_lab.teardown` is step 14 of the
notebook: it runs under the student session role, knows the one prefix this run
used, and reports PASS/FAIL rows into the notebook's summary.
`vocareum_tools.sweep` runs from an instructor's machine against a session it
opened, knows every name shape any generation of the workshop ever created, and
exits with a status code an instructor scripts against.

What they do have to agree on is the rule for recognising a resource, and for a
while they did not. They grew the same five fixes in parallel and ended with two
answers to one question: which tag key casing counts, how a log group under the
service's own path is matched, which S3 error codes mean the bucket is not
there. Drift there is not a style problem. This rule decides what gets deleted
and what gets left behind in an account that is about to become unreachable, so
a mistake goes one of two ways: something Vocareum owns is deleted, or the run
reports a clean account while a runtime keeps billing.

**The vocabulary lives in the published package and the private one imports it,
and that direction is forced.** `workshop_lab` installs into a student's
notebook from a public repository; `aws-vocareum` is private and a notebook
cannot install from it at all. An import the other way would resolve on this
machine and fail in every lab.

There are no client calls and no deletes here. Each program still enumerates and
deletes with the permissions and the reporting shape it has.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

# The tag every step applies to what it creates, and the tag half of the rule
# below. It is here rather than in `naming` because `naming` builds names and
# this module is the vocabulary both sweepers share. Every reader imports it
# from here directly; `naming` imports it for its own `tags_map` / `tags_list` /
# `tags_query` forms and re-exports nothing, so there is one hop and not three.
WORKSHOP_TAG_KEY = "WorkshopResource"
WORKSHOP_TAG_VALUE = "stop-ai-agent-hallucinations"

# AgentCore Runtime creates one CloudWatch log group per runtime endpoint under
# this fixed path, and DeleteAgentRuntime does not take it with it. A hand
# cleanup of one account found log groups for runtimes that no longer existed,
# still billing for stored bytes.
#
# The documented shape is
# /aws/bedrock-agentcore/runtimes/<agentRuntimeId>-<endpointName>/runtime-logs,
# per the AgentCore Runtime observability guide, checked 2026-08-06. Two parts of
# that matter. The id leads the segment and an AgentCore id is <name>-<suffix>,
# so a workshop name leads the tail and a prefix match can find it. And there is
# a trailing /runtime-logs that is easy to forget: never build one of these
# names, list them and use the name the listing reports.
AGENTCORE_RUNTIME_LOG_PREFIX = "/aws/bedrock-agentcore/runtimes/"

# AgentCore creates a DEFAULT endpoint with every runtime and refuses to delete
# it on its own. Attempting it raises and aborts the drain before the runtime,
# leaking the runtime the whole ordering exists to remove.
IMPLICIT_ENDPOINT = "DEFAULT"

# The AgentCore CodeBuild path uploads its build context to a bucket of its own
# naming, which carries neither the workshop tag nor a workshop name. Neither
# sweeper can discover it by listing, because `s3:ListAllMyBuckets` is not
# granted, so the computed name is the only handle either has on it.
S3_SOURCE_BUCKET_STEM = "bedrock-agentcore-codebuild-sources"

# S3 answers a HEAD with a status code and no body, so botocore has no error code
# to report and synthesises one. Which of the three arrives depends on the
# operation and the botocore version, so all three mean the bucket is not there.
# The notebook side used to know only two of them, which is exactly the kind of
# divergence this module exists to end.
BUCKET_GONE_CODES = frozenset({"404", "NoSuchBucket", "NotFound"})


def source_bucket_name(account_id: str, region: str) -> str:
    """Return the name the AgentCore CodeBuild path gives its source bucket.

    Computed from the live account and region, never stored. The account id is
    half the name and Vocareum rotates the account pool, so a remembered bucket
    name eventually names a bucket in an account the caller is guarded against
    ever touching.
    """
    return f"{S3_SOURCE_BUCKET_STEM}-{account_id}-{region}"


def name_prefixes(prefix: str) -> tuple[str, ...]:
    """Every name shape one run of the notebook creates from its prefix.

    A bare prefix is not enough on its own. Three names put it in the middle:
    `bedrock-agentcore-<prefix>` is the ECR repository and the CodeBuild
    project's stem, `hotel-booking-<prefix>-tool` is the Lambda, and
    `workshop-<prefix>-*` is every IAM role and the DynamoDB table.

    `vocareum_tools.sweep` does not call this to build its own list, because its
    list is the union across every generation of names that could still be
    sitting in a pooled account. It does have to remain a superset of this, and
    `tests/test_sweep.py` asserts exactly that.
    """
    return (
        prefix,
        f"workshop-{prefix}",
        f"bedrock-agentcore-{prefix}",
        f"hotel-booking-{prefix}",
    )


def tag_map(raw: Any) -> dict[str, str]:
    """Normalise any of the tag shapes AWS answers with into one mapping.

    Three shapes arrive. AgentCore, Lambda, and Logs answer with a mapping
    already. Most other services answer with `[{"Key": k, "Value": v}]`.
    CodeBuild answers with the same list spelled `key` and `value`, and a reader
    that knew only the capitalised pair saw every CodeBuild project as untagged:
    that is the tag half of selection switching itself off silently, which is
    the failure the union rule exists to prevent.

    Anything else, including the None a missing key produces, is no tags rather
    than an error. A caller here is deciding whether to delete something, and
    "the shape surprised me" must not read as "it is tagged".
    """
    if isinstance(raw, Mapping):
        return {str(key): str(value) for key, value in raw.items()}
    if not isinstance(raw, list):
        return {}
    mapped: dict[str, str] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        key = item.get("Key", item.get("key", ""))
        value = item.get("Value", item.get("value", ""))
        mapped[str(key)] = str(value)
    return mapped


def carries_workshop_tag(
    raw: Any,
    tag_key: str = WORKSHOP_TAG_KEY,
    tag_value: str = WORKSHOP_TAG_VALUE,
) -> bool:
    """True when a tag read, in whatever shape it arrived, carries the workshop tag."""
    return tag_map(raw).get(tag_key) == tag_value


# How many refused resources a count names before it stops listing them. Enough
# to tell one refused service from a whole account of them, short enough that a
# blind sweep does not bury its own plan under the evidence.
DENIAL_SAMPLE = 3


@dataclass
class TagReads:
    """A running count of tag reads that answered against tag reads that did not.

    Selection cannot tell those apart and should not: a refusal and an untagged
    resource both mean "no workshop tag", and both are meant to, because the
    name half already recognises everything either sweeper created. They are not
    the same fact about the account. `logs:ListTagsForResource` was granted on
    2026-08-07 and `docs/permissions.md` still carries it Untested, so a run
    where every tag read was refused reads exactly like a run where nothing was
    tagged, and both read like a clean account.

    This counts the difference so it can be printed. It changes no verdict on
    either side. Escalating a refusal into a failure would fail the notebook's
    empty check on every student run in an account that refuses the read, which
    is the ordinary case rather than the anomaly, so what is bought here is a
    report that says the tag half was blind for N resources instead of quietly
    answering "untagged" N times.
    """

    reads: int = 0
    denials: int = 0
    labels: list[str] = field(default_factory=list)

    def answered(self) -> None:
        """Record a tag read that returned, whether or not it carried tags."""
        self.reads += 1

    def refused(self, label: str) -> None:
        """Record a tag read that failed, keeping the first few names."""
        self.reads += 1
        self.denials += 1
        if len(self.labels) < DENIAL_SAMPLE:
            self.labels.append(label)

    def note(self) -> str:
        """One line naming the blindness, or an empty string when there is none."""
        if not self.denials:
            return ""
        named = ", ".join(self.labels)
        more = "" if self.denials <= len(self.labels) else ", and more"
        return (
            f"tag reads refused for {self.denials} of {self.reads} resources "
            f"({named}{more}); each was read as untagged and the name half decided"
        )


def matches_prefix(name: str, prefixes: Iterable[str]) -> bool:
    """True when a name starts with any of the prefixes.

    `str.startswith` takes a tuple and not any iterable, and both callers hold
    their prefixes as tuples already; the conversion is here so a caller passing
    a list gets an answer rather than a TypeError at delete-decision time.
    """
    return name.startswith(tuple(prefixes))


def selected_by(
    name: str,
    tags: Mapping[str, str],
    prefixes: Iterable[str],
    tag_key: str = WORKSHOP_TAG_KEY,
    tag_value: str = WORKSHOP_TAG_VALUE,
    require_prefix: bool = False,
) -> str:
    """Say why a resource is in scope, or return an empty string for out of scope.

    The two halves are unioned rather than intersected. Tagging an AgentCore
    resource is itself a measured permission, so an account that refuses it
    produces real workshop resources carrying no tags at all; a name that
    matches has to be enough on its own.

    `require_prefix` inverts that for IAM. A student account also holds
    Vocareum's own voclabs and vocareum roles and whatever service-linked roles
    AWS put there, and a role selectable by tag alone would be deletable the
    moment anything tagged one.
    """
    reasons = []
    if tags.get(tag_key) == tag_value:
        reasons.append("tag")
    prefixed = matches_prefix(name, prefixes)
    if prefixed:
        reasons.append("prefix")
    if require_prefix and not prefixed:
        return ""
    return "+".join(reasons)


def log_group_prefixes(prefixes: Iterable[str]) -> tuple[str, ...]:
    """The workshop's name prefixes, moved under the AgentCore log path.

    A log group name starts with the service's own path rather than with a
    workshop name, so a prefix match against the raw name never fires. Composing
    the two keeps the shared rule usable unchanged: the tag half still selects a
    group under this path whatever it is called, and the prefix half still
    refuses one no workshop resource named.

    `log_group_tail` is the same test written the other way round, for a caller
    holding one name rather than a prefix list, and
    `tests/test_workshop_lab_selection.py` proves the two agree.
    """
    return tuple(AGENTCORE_RUNTIME_LOG_PREFIX + one for one in prefixes)


def log_group_tail(name: str) -> str:
    """The part of a log group name a workshop name can lead."""
    return name.removeprefix(AGENTCORE_RUNTIME_LOG_PREFIX)


def stack_owned_keys(physical_id: str) -> set[str]:
    """Every string a list API might report for one CloudFormation resource.

    An ARN's last segment is what the sibling list APIs return as a name, so
    both forms are recorded. A stack that reports a secret by ARN and a
    `list_secrets` that reports it by name are otherwise two different strings
    for one resource, and the exclusion misses.

    Exclusion is the safe direction. Over-exclude and a resource survives one
    more sweep; under-exclude and the lab stack fails its own delete at session
    end and the account cannot be recycled at all.
    """
    if not physical_id:
        return set()
    return {physical_id, physical_id.rsplit("/", 1)[-1]}
