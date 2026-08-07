# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/guards.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""The checks that stop the lab notebook rather than warn it.

Three questions have to be answered before any measurement below them means
anything: are there credentials at all, do they belong to the account the
student was assigned, and is the session in the region the workshop needs. Each
one raises. A warning would let the remaining cells run and report confidently
about the wrong account, which has already produced one false answer in this
repository's history and is the reason `probe.py` carries the same three guards
for the operator-side tools.

These are functions rather than methods so the pytest suite can drive them with
a fake session and no AWS call. `Harness` calls them; nothing else should need
to.
"""

from __future__ import annotations

from typing import Any

# AgentCore and the Nova multimodal embedding model exist in no other region, so
# a session anywhere else cannot verify the environment this workshop runs in.
REQUIRED_REGION = "us-east-1"

CREDENTIAL_FIELDS = (
    "aws_access_key_id",
    "aws_secret_access_key",
    "aws_session_token",
)


def mask(value: str, keep: int = 4) -> str:
    """Show the length and last few characters, never the secret itself."""
    if len(value) <= keep:
        return "****"
    return f"[{len(value)} chars]****{value[-keep:]}"


def frozen_credentials(session: Any) -> dict[str, str]:
    """Return the three credential fields, with absent ones as empty strings.

    A terminated Vocareum session hands back empty strings rather than no
    credentials at all. boto3 reads those as absent, falls through its provider
    chain, and ends up on whatever ambient credentials the machine holds. So the
    empty string and the missing key have to be treated as the same failure.
    """
    found = session.get_credentials()
    if found is None:
        raise RuntimeError(
            "No AWS credentials at all. Your lab session has probably ended. "
            "Close this tab, start the lab again, and reopen the notebook."
        )
    frozen = found.get_frozen_credentials()
    return {
        "aws_access_key_id": frozen.access_key or "",
        "aws_secret_access_key": frozen.secret_key or "",
        "aws_session_token": frozen.token or "",
    }


def verify_credentials(session: Any, echo: Any = print) -> None:
    """Stop the notebook unless all three credential fields carry a value.

    Returns nothing on purpose. Jupyter displays the value of a cell's last
    expression, so handing the credentials back would put the live secret key
    and session token on screen and into the saved `.ipynb` the moment anyone
    called this without assigning the result.
    """
    fields = frozen_credentials(session)
    blank = [name for name, value in fields.items() if not value.strip()]
    if blank:
        raise RuntimeError(
            f"These credential fields are empty: {', '.join(blank)}. "
            "Your lab session has ended or was never fully started. "
            "Close this tab, start the lab again, and reopen the notebook. "
            "Nothing below this cell can be trusted until this passes."
        )

    for name, value in fields.items():
        echo(f"{name:<22} = {mask(value)}")
    echo("\nOK. All three credential fields carry a value.")


def verify_region(region: str, required: str = REQUIRED_REGION) -> None:
    """Stop the notebook unless the session is in the region the workshop needs."""
    if region != required:
        raise RuntimeError(
            f"This workshop needs {required} and this session is in {region}. "
            "The Nova multimodal embedding model exists only in us-east-1. Tell "
            "your instructor before continuing, because nothing below this cell "
            "is meaningful in the wrong region."
        )


def verify_identity(
    sts: Any,
    region: str,
    required: str = REQUIRED_REGION,
    echo: Any = print,
) -> str:
    """Confirm the region, then name the account and principal. Returns account id."""
    verify_region(region, required)

    identity = sts.get_caller_identity()
    account_id = identity["Account"]

    echo(f"Account:  {account_id}")
    echo(f"Identity: {identity['Arn']}")
    echo(f"Region:   {region}")
    echo(f"\nOK. {region} is the region this workshop runs in.")
    return account_id
