# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/memory.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Step 10. Create an AgentCore Memory, tag it, and read the tag back.

The workshop's memory module creates a Memory with two long-term strategies, then
tags it, then refuses to continue if the tag did not stick. This step does the
same three things for the same reason.

**Tagging is checked, not assumed.** The workshop's cleanup deletes only what
carries the `WorkshopResource` tag. A tag that silently fails to apply stops the
workshop later with a confusing error and leaves everything already created in
the account past the end of the lab. So the tag is written and then read back,
and a mismatch is a FAIL that says so.

**TagResource may not exist in the installed boto3.** AgentCore's tagging API
arrived after the client did. A missing method is not a permission answer, so it
is recorded as a FAIL naming the upgrade rather than left to raise an
AttributeError out of the cell.

**UpdateMemory returns before it finishes.** It leaves the Memory `UPDATING` for
over a minute, and a delete inside that window is refused. Step 14 does not know
that, so this waits for `ACTIVE` again before handing over.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from workshop_lab.harness import FAIL, PASS
from workshop_lab.naming import WORKSHOP_TAG_KEY, WORKSHOP_TAG_VALUE

if TYPE_CHECKING:
    from workshop_lab.harness import Harness

# The pair the workshop configures. Kept together because the point of the check
# is that the account allows both strategy types, not either one.
STRATEGIES = [
    {
        "userPreferenceMemoryStrategy": {
            "name": "UserPreferences",
            "namespaces": ["/users/{actorId}/preferences"],
        }
    },
    {
        "semanticMemoryStrategy": {
            "name": "UserFacts",
            "namespaces": ["/users/{actorId}/facts"],
        }
    },
]

EVENT_EXPIRY_DAYS = 7

CREATE_CHECK = "agentcore:CreateMemory"
GET_CHECK = "agentcore:GetMemory"
TAG_CHECK = "agentcore:TagResource"
LIST_TAGS_CHECK = "agentcore:ListTagsForResource"
UPDATE_CHECK = "agentcore:UpdateMemory"
TAG_READBACK_CHECK = "workshop tag survives a read-back"


class Memory:
    """Creates the Memory, proves the workshop tag sticks, and updates it."""

    def __init__(self, lab: Harness) -> None:
        self.lab = lab
        self.memory_id: str | None = None
        self.memory_arn: str | None = None

    @property
    def control(self) -> Any:
        return self.lab.client("bedrock-agentcore-control")

    def create(self) -> dict[str, Any] | None:
        """Create the Memory with both strategies, tagged, and register its delete.

        The tag goes on in the create request as well as through `tag` below, and
        the pair is not redundant. `tag` is what measures
        `bedrock-agentcore:TagResource` for the tracker, and it runs after the
        Memory is `ACTIVE`, which is a minute or more later. A create that tags
        nothing leaves the Memory unrecognisable to a tag sweep for the whole of
        that window, and unrecognisable for good if the notebook is interrupted
        inside it. So it is tagged at birth and the measurement still happens.
        """
        memory = self.lab.check(
            CREATE_CHECK,
            lambda: self.control.create_memory(
                name=self.lab.names.memory,
                description="Vocareum environment verification.",
                eventExpiryDuration=EVENT_EXPIRY_DAYS,
                memoryStrategies=STRATEGIES,
                tags=self.lab.names.tags_map,
            ),
            "two long-term strategies, the pair the workshop configures",
        )
        if memory is None:
            return None

        self.memory_id = memory["memory"]["id"]
        self.memory_arn = memory["memory"]["arn"]
        memory_id = self.memory_id
        self.lab.defer(
            f"memory {memory_id}",
            lambda: self.control.delete_memory(memoryId=memory_id),
        )
        return memory

    def wait_for_active(self, label: str, failed: set[str]) -> str:
        """Poll until the Memory is `ACTIVE`, which is when a delete is allowed.

        `failed` differs between the two callers: a Memory that has already been
        created cannot reach `CREATE_FAILED` again, and listing a state a call
        cannot produce would settle the wait on a state it never had.
        """
        memory_id = self.memory_id
        return self.lab.wait_until(
            lambda: self.control.get_memory(memoryId=memory_id)["memory"]["status"],
            done={"ACTIVE"},
            failed=failed,
            label=label,
        )

    def tag(self) -> None:
        """Write the workshop tag and read it back off the Memory."""
        if not hasattr(self.control, "tag_resource"):
            self.lab.record(
                TAG_CHECK,
                FAIL,
                "this boto3 has no TagResource for AgentCore; upgrade boto3",
            )
            return

        tagged = self.lab.check(
            TAG_CHECK,
            lambda: self.control.tag_resource(
                resourceArn=self.memory_arn, tags=self.lab.names.tags_map
            ),
        )
        read_back = self.lab.check(
            LIST_TAGS_CHECK,
            lambda: self.control.list_tags_for_resource(resourceArn=self.memory_arn),
        )
        if tagged is None or read_back is None:
            return

        stuck = read_back.get("tags", {}).get(WORKSHOP_TAG_KEY)
        if stuck == WORKSHOP_TAG_VALUE:
            self.lab.record(TAG_READBACK_CHECK, PASS, WORKSHOP_TAG_KEY)
        else:
            self.lab.record(
                TAG_READBACK_CHECK,
                FAIL,
                f"read back {stuck!r}; workshop cleanup will not find this",
            )

    def update(self) -> None:
        """Update the description, then wait out the `UPDATING` window it opens."""
        memory_id = self.memory_id
        self.lab.check(
            UPDATE_CHECK,
            lambda: self.control.update_memory(
                memoryId=memory_id,
                description="Updated by the verification notebook.",
            ),
        )
        self.wait_for_active(f"memory {memory_id} after the update", {"FAILED"})

    def run(self) -> str | None:
        """Do the whole step and return the Memory id, or None if none exists."""
        if self.create() is None:
            return None

        memory_id = self.memory_id
        self.wait_for_active(f"memory {memory_id}", {"CREATE_FAILED", "FAILED"})
        self.lab.check(GET_CHECK, lambda: self.control.get_memory(memoryId=memory_id))
        self.tag()
        self.update()
        return self.memory_id
