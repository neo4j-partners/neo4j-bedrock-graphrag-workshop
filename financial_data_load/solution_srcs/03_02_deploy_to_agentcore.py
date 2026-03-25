"""
Deploy Basic Strands Agent to AgentCore Runtime

This solution deploys the pre-built agent from agentcore_deploy/ to
Amazon Bedrock AgentCore Runtime, invokes it via boto3, and cleans up.

Run with: uv run python main.py solutions <N>
"""

import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import boto3
import yaml
from botocore.config import Config

from config import BedrockConfig

# ---------------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------------

config = BedrockConfig()
REGION = config.region

AGENT_NAME = "basic_strands_agent"
AGENT_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "Lab_3_Intro_to_Bedrock_and_Agents"
    / "agentcore_deploy"
)

def _find_agentcore() -> str:
    """Find the agentcore CLI, checking the current venv first."""
    # Check alongside the running Python (works inside uv .venv)
    venv_bin = Path(sys.executable).parent / "agentcore"
    if venv_bin.exists():
        return str(venv_bin)
    found = shutil.which("agentcore")
    if found:
        return found
    raise FileNotFoundError(
        "agentcore CLI not found. Install with: pip install bedrock-agentcore-starter-toolkit"
    )


AGENTCORE_CLI = _find_agentcore()

print(f"Region:     {REGION}")
print(f"Agent dir:  {AGENT_DIR}")
print(f"CLI:        {AGENTCORE_CLI}")


# ---------------------------------------------------------------------------
# 2. Verify deployment package
# ---------------------------------------------------------------------------

def verify_deployment_package():
    """Verify the agentcore_deploy directory has the required files."""
    required = ["agent.py", "pyproject.toml"]
    for name in required:
        path = AGENT_DIR / name
        if not path.exists():
            raise FileNotFoundError(f"Missing deployment file: {path}")
        print(f"  Found: {name} ({path.stat().st_size} bytes)")
    print("Deployment package verified.")


# ---------------------------------------------------------------------------
# 3. Generate AgentCore config
# ---------------------------------------------------------------------------

def generate_config() -> Path:
    """Generate .bedrock_agentcore.yaml for deployment."""
    sts = boto3.client("sts")
    account_id = sts.get_caller_identity()["Account"]

    agent_dir_str = str(AGENT_DIR)
    entrypoint = os.path.join(agent_dir_str, "agent.py")

    agentcore_config = {
        "default_agent": AGENT_NAME,
        "agents": {
            AGENT_NAME: {
                "name": AGENT_NAME,
                "language": "python",
                "entrypoint": entrypoint,
                "deployment_type": "direct_code_deploy",
                "runtime_type": "PYTHON_3_13",
                "platform": "linux/arm64",
                "source_path": agent_dir_str,
                "aws": {
                    "account": account_id,
                    "region": REGION,
                    "execution_role_auto_create": True,
                    "ecr_auto_create": False,
                    "s3_auto_create": True,
                    "network_configuration": {
                        "network_mode": "PUBLIC",
                    },
                    "protocol_configuration": {
                        "server_protocol": "HTTP",
                    },
                    "observability": {
                        "enabled": True,
                    },
                },
            }
        },
    }

    config_path = AGENT_DIR / ".bedrock_agentcore.yaml"
    with open(config_path, "w") as f:
        yaml.dump(agentcore_config, f, default_flow_style=False)

    print(f"Wrote {config_path}")
    print(f"  Agent:   {AGENT_NAME}")
    print(f"  Account: {account_id}")
    print(f"  Region:  {REGION}")
    return config_path


# ---------------------------------------------------------------------------
# 4. Deploy
# ---------------------------------------------------------------------------

def deploy():
    """Deploy the agent to AgentCore Runtime."""
    print("Deploying to AgentCore Runtime...")
    result = subprocess.run(
        [AGENTCORE_CLI, "deploy", "--auto-update-on-conflict"],
        cwd=str(AGENT_DIR),
        capture_output=True,
        text=True,
        timeout=600,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"agentcore deploy failed (exit {result.returncode})")
    print("Deploy succeeded.")


# ---------------------------------------------------------------------------
# 5. Invoke via boto3
# ---------------------------------------------------------------------------

def invoke_agent(prompt: str):
    """Invoke the deployed agent via boto3."""
    config_path = AGENT_DIR / ".bedrock_agentcore.yaml"
    with open(config_path) as f:
        deploy_config = yaml.safe_load(f)

    default_agent = deploy_config["default_agent"]
    agent_config = deploy_config["agents"][default_agent]
    agent_arn = agent_config["bedrock_agentcore"]["agent_arn"]
    agent_region = agent_config["aws"]["region"]

    print(f"Agent:  {default_agent}")
    print(f"ARN:    {agent_arn}")
    print(f"Region: {agent_region}")

    client = boto3.client(
        "bedrock-agentcore",
        region_name=agent_region,
        config=Config(read_timeout=300),
    )

    response = client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        runtimeSessionId=str(uuid.uuid4()),
        payload=json.dumps({"prompt": prompt}).encode(),
        qualifier="DEFAULT",
    )

    content = "".join(
        chunk.decode("utf-8") for chunk in response.get("response", [])
    )

    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        parsed = content

    print(f"Prompt:   {prompt}")
    print(f"Response: {parsed}")
    return parsed


# ---------------------------------------------------------------------------
# 6. Cleanup
# ---------------------------------------------------------------------------

def destroy():
    """Destroy the deployed agent."""
    print("Destroying deployed agent...")
    result = subprocess.run(
        [AGENTCORE_CLI, "destroy", "--force"],
        cwd=str(AGENT_DIR),
        capture_output=True,
        text=True,
        timeout=300,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print("Warning: agentcore destroy may have failed.")
    else:
        print("Destroy succeeded.")


# ---------------------------------------------------------------------------
# 7. Main
# ---------------------------------------------------------------------------

def main():
    """Deploy, invoke, and optionally clean up the AgentCore agent.

    Set AGENTCORE_CLEANUP=true to destroy the agent after testing.
    Default is to leave it running.
    """
    # Verify deployment package
    verify_deployment_package()
    print()

    # Generate config
    generate_config()
    print()

    # Deploy
    deploy()
    print()

    # Invoke
    invoke_agent("What is 100 + 200?")
    print()

    # Cleanup (opt-in)
    if os.environ.get("AGENTCORE_CLEANUP", "").lower() in ("true", "1", "yes"):
        destroy()
    else:
        print("Skipping cleanup. Set AGENTCORE_CLEANUP=true to destroy after testing.")
        print(f"Manual cleanup: cd {AGENT_DIR} && agentcore destroy")


if __name__ == "__main__":
    main()
