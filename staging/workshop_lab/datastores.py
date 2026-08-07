# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/datastores.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Step 12. The secret the Lambda reads and the table the memory module writes.

Both are quick, and both carry one detail that is not obvious.

**The secret holds placeholders, not the real Aura credentials.** Anything in
this notebook can end up in a printed cell, a saved output, or a support ticket.
Step 3 already proved the real credentials work, so nothing is gained by putting
them here and something is risked.

**A table whose tags are still settling refuses `DeleteTable`.** Tagging leaves
the table busy for longer than the two item calls take, so the delete registered
for step 14 retries through `ResourceInUseException` rather than assuming the
table is idle by the time teardown reaches it.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from workshop_lab.harness import FAIL, PASS, SKIP

if TYPE_CHECKING:
    from workshop_lab.harness import Harness

# The four-field shape the deployed Lambda reads. Placeholders on purpose.
SECRET_PAYLOAD = {
    "uri": "neo4j+s://placeholder",
    "username": "placeholder",
    "password": "placeholder",
    "database": "neo4j",
}

# Composite key and on-demand billing, matching the workshop's own table.
KEY_SCHEMA = [
    {"AttributeName": "pk", "KeyType": "HASH"},
    {"AttributeName": "sk", "KeyType": "RANGE"},
]
ATTRIBUTE_DEFINITIONS = [
    {"AttributeName": "pk", "AttributeType": "S"},
    {"AttributeName": "sk", "AttributeType": "S"},
]
ITEM = {"pk": {"S": "verify"}, "sk": {"S": "1"}, "ok": {"BOOL": True}}
ITEM_KEY = {"pk": {"S": "verify"}, "sk": {"S": "1"}}

DELETE_TABLE_TIMEOUT = 180
DELETE_TABLE_INTERVAL = 10

CREATE_SECRET_CHECK = "secretsmanager:CreateSecret"
DESCRIBE_SECRET_CHECK = "secretsmanager:DescribeSecret"
GET_SECRET_CHECK = "secretsmanager:GetSecretValue"
CREATE_TABLE_CHECK = "dynamodb:CreateTable"
PUT_ITEM_CHECK = "dynamodb:PutItem"
GET_ITEM_CHECK = "dynamodb:GetItem"
ROUND_TRIP_CHECK = "dynamodb item round trip"


class DataStores:
    """Creates the workshop's secret and its bookings table, and uses both."""

    def __init__(self, lab: Harness) -> None:
        self.lab = lab

    @property
    def secrets(self) -> Any:
        return self.lab.client("secretsmanager")

    @property
    def dynamodb(self) -> Any:
        return self.lab.client("dynamodb")

    # --- Secrets Manager ------------------------------------------------------
    def create_secret(self) -> None:
        """Create the secret, then describe and read it the way the Lambda does."""
        name = self.lab.names.secret
        secret = self.lab.check(
            CREATE_SECRET_CHECK,
            lambda: self.secrets.create_secret(
                Name=name,
                SecretString=json.dumps(SECRET_PAYLOAD),
                Tags=self.lab.names.tags_list,
            ),
            "the same four-field shape the deployed Lambda reads",
        )
        if secret is None:
            return

        self.lab.defer(
            f"secret {name}",
            lambda: self.secrets.delete_secret(
                SecretId=name, ForceDeleteWithoutRecovery=True
            ),
        )
        self.lab.check(
            DESCRIBE_SECRET_CHECK,
            lambda: self.secrets.describe_secret(SecretId=name),
        )
        self.lab.check(
            GET_SECRET_CHECK,
            lambda: self.secrets.get_secret_value(SecretId=name),
        )

    # --- DynamoDB -------------------------------------------------------------
    def delete_table_when_idle(self, name: str) -> None:
        """Delete a table, waiting out the window where it is still busy.

        Registered as the teardown delete rather than a bare `delete_table`,
        because tagging leaves a table `ResourceInUseException` for longer than
        the rest of this step takes. The waiting is `Harness.retry_while`, which
        is where step 14 already does this same delete: two hand-rolled retry
        loops around one call is how the two ended up with different timeouts.
        """
        self.lab.retry_while(
            lambda: self.dynamodb.delete_table(TableName=name),
            codes={"ResourceInUseException"},
            label=f"delete table {name}",
            timeout=DELETE_TABLE_TIMEOUT,
            interval=DELETE_TABLE_INTERVAL,
        )

    def create_table(self) -> bool:
        """Create the table and wait for `ACTIVE`, which is when it takes items."""
        name = self.lab.names.table
        table = self.lab.check(
            CREATE_TABLE_CHECK,
            lambda: self.dynamodb.create_table(
                TableName=name,
                KeySchema=KEY_SCHEMA,
                AttributeDefinitions=ATTRIBUTE_DEFINITIONS,
                BillingMode="PAY_PER_REQUEST",
                Tags=self.lab.names.tags_list,
            ),
            "composite key, PAY_PER_REQUEST",
        )
        if table is None:
            return False

        self.lab.defer(
            f"dynamodb table {name}", lambda: self.delete_table_when_idle(name)
        )
        self.lab.wait_until(
            lambda: self.dynamodb.describe_table(TableName=name)["Table"][
                "TableStatus"
            ],
            done={"ACTIVE"},
            failed={"CREATE_FAILED"},
            label=f"table {name}",
            timeout=180,
            interval=5,
        )
        return True

    def round_trip(self) -> None:
        """Write one item and read it back, consistently."""
        name = self.lab.names.table
        self.lab.check(
            PUT_ITEM_CHECK,
            lambda: self.dynamodb.put_item(TableName=name, Item=ITEM),
        )
        read = self.lab.check(
            GET_ITEM_CHECK,
            lambda: self.dynamodb.get_item(
                TableName=name, Key=ITEM_KEY, ConsistentRead=True
            ),
        )
        if read is None:
            self.lab.record(ROUND_TRIP_CHECK, SKIP, "the read did not run")
        elif read.get("Item"):
            self.lab.record(ROUND_TRIP_CHECK, PASS)
        else:
            self.lab.record(ROUND_TRIP_CHECK, FAIL, "the item was written but not read")

    # --- the step -------------------------------------------------------------
    def run(self) -> None:
        self.create_secret()
        if self.create_table():
            self.round_trip()
