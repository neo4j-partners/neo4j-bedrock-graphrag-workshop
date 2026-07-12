#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     # Orchestration
#     "papermill>=2.6.0",
#     "nbformat>=5.10",
#     "ipykernel>=6.29",
#     "jupyter-client>=8.6",
#     "python-dotenv>=1.0",
#     # Lab dependencies, pre-provisioned so the neutralized %pip cells have
#     # nothing left to install at run time. Mirrors the %pip lines in the
#     # in-scope notebooks (Labs 3, 4, 6, Appendix).
#     "neo4j-graphrag[bedrock]>=1.18.0",
#     "strands-agents",
#     "strands-agents-tools",
#     "mcp",
#     "httpx",
#     # Deploy-only (Lab 4 02 / Appendix 02), used only with --include-deploy.
#     "bedrock-agentcore-starter-toolkit>=0.3.3",
#     "bedrock-agentcore>=1.4.7",
#     "pyyaml",
# ]
# ///
"""Validate the workshop notebooks against a pre-loaded Neo4j graph.

Local analog of the Databricks ``automate.py`` pattern: each in-scope notebook
asserts its own correctness via inline cells, and this runner executes it with
papermill and treats a clean run (no cell raised) as a pass.

Credential handling (Option A): the runner reads ``--env`` and injects those
keys into the process environment before papermill launches the kernel. Because
each lab's ``lib/data_utils.py`` loads ``CONFIG.txt`` with the default
``load_dotenv`` (``override=False``), the injected values win and ``CONFIG.txt``
is never touched. Participants who set nothing fall back to ``CONFIG.txt`` as
usual.

Usage:
    uv run setup/run_notebooks.py                     # all in-scope, default CONFIG.txt
    uv run setup/run_notebooks.py --labs 4            # a single lab
    uv run setup/run_notebooks.py --labs 3,4,6        # a list
    uv run setup/run_notebooks.py --labs 4-6          # a range
    uv run setup/run_notebooks.py --labs appendix     # the appendix notebook
    uv run setup/run_notebooks.py --env setup/.env.gold
    uv run setup/run_notebooks.py --include-deploy    # also run deploy notebooks
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# Default env follows the same precedence as the notebooks' lib/data_utils.py:
# prefer the project-root .env (real local creds), fall back to CONFIG.txt.
# This keeps the injected values (Option A) consistent with what the lib would
# load itself, so neither clobbers the other.
DEFAULT_ENV = REPO_ROOT / ".env" if (REPO_ROOT / ".env").exists() else REPO_ROOT / "CONFIG.txt"
KERNEL_NAME = "graphrag-workshop"

# Lines that install packages; neutralized before execution.
_PIP_MAGIC = re.compile(r"^(\s*)[%!]\s*(pip|pip3|conda|uv)\b")


@dataclass
class Notebook:
    """One in-scope notebook and how the runner should treat it."""

    lab: str  # "3", "4", "6", or "appendix"
    path: Path
    requires_mcp: bool = False
    is_deploy: bool = False


# Registry of in-scope notebooks. Data-load notebooks (Lab 2) are intentionally
# absent: the runner assumes the graph is already loaded.
NOTEBOOKS: list[Notebook] = [
    Notebook("3", REPO_ROOT / "Lab_3_GraphRAG_Search" / "01_vector_retriever.ipynb"),
    Notebook("3", REPO_ROOT / "Lab_3_GraphRAG_Search" / "02_vector_cypher_retriever.ipynb"),
    Notebook("4", REPO_ROOT / "Lab_4_GraphRAG_Agent" / "01_strands_graphrag_agent.ipynb"),
    Notebook(
        "4",
        REPO_ROOT / "Lab_4_GraphRAG_Agent" / "02_deploy_to_agentcore.ipynb",
        is_deploy=True,
    ),
    Notebook("6", REPO_ROOT / "Lab_6_MCP_Server" / "01_intro_strands_mcp.ipynb", requires_mcp=True),
    Notebook("6", REPO_ROOT / "Lab_6_MCP_Server" / "02_graph_enriched_search.ipynb", requires_mcp=True),
    Notebook("6", REPO_ROOT / "Lab_6_MCP_Server" / "03_text2cypher_agent.ipynb", requires_mcp=True),
    Notebook("appendix", REPO_ROOT / "zz_Appendix_What_Is_An_Agent" / "01_basic_strands_agent.ipynb"),
    Notebook(
        "appendix",
        REPO_ROOT / "zz_Appendix_What_Is_An_Agent" / "02_deploy_to_agentcore.ipynb",
        is_deploy=True,
    ),
]


@dataclass
class Result:
    notebook: Notebook
    status: str  # "PASS", "FAIL", or "SKIP"
    reason: str = ""
    detail: str = ""


# ---------------------------------------------------------------------------
# Lab selection
# ---------------------------------------------------------------------------

_KNOWN_LABS = ("3", "4", "6", "appendix")


def parse_labs(spec: str | None) -> set[str]:
    """Turn a ``--labs`` spec into a set of lab tokens.

    Accepts a single lab (``4``), a comma list (``3,4,6``), a numeric range
    (``4-6``), and the literal ``appendix`` (or ``A``). ``None`` selects every
    in-scope lab.
    """
    if spec is None:
        return set(_KNOWN_LABS)

    selected: set[str] = set()
    for token in spec.split(","):
        token = token.strip().lower()
        if not token:
            continue
        if token in ("appendix", "a"):
            selected.add("appendix")
        elif re.fullmatch(r"\d+-\d+", token):
            start, end = (int(n) for n in token.split("-"))
            if start > end:
                raise ValueError(f"invalid range '{token}': start > end")
            selected.update(str(n) for n in range(start, end + 1))
        elif token.isdigit():
            selected.add(token)
        else:
            raise ValueError(f"invalid --labs token '{token}'")

    # Numeric tokens outside the in-scope set (e.g. 5 from a 4-6 range) are
    # dropped; that lab simply has no in-scope notebooks. An all-unknown spec
    # yields an empty set, which main() reports as an error.
    return selected & set(_KNOWN_LABS)


# ---------------------------------------------------------------------------
# Environment (Option A)
# ---------------------------------------------------------------------------

def inject_env(env_file: Path) -> None:
    """Load ``env_file`` and set its keys into ``os.environ``.

    The kernel subprocess papermill launches inherits this environment. Inside
    the notebook, ``load_dotenv(CONFIG.txt)`` runs with the default
    ``override=False`` and therefore cannot clobber these values.
    """
    from dotenv import dotenv_values

    if not env_file.exists():
        raise SystemExit(f"env file not found: {env_file}")

    values = dotenv_values(env_file)
    for key, value in values.items():
        if value is not None:
            os.environ[key] = value


def _is_placeholder(value: str | None) -> bool:
    if not value:
        return True
    stripped = value.strip()
    return not stripped or stripped.lower().startswith("your-")


def mcp_available() -> bool:
    """Whether MCP credentials look real (present and not a placeholder)."""
    return not _is_placeholder(os.environ.get("MCP_GATEWAY_URL")) and not _is_placeholder(
        os.environ.get("MCP_ACCESS_TOKEN")
    )


# ---------------------------------------------------------------------------
# Notebook preparation and execution
# ---------------------------------------------------------------------------

def neutralize_pip(nb) -> int:
    """Comment out every ``%pip``/``!pip``/``conda``/``uv`` install line.

    Operates line by line so mixed cells keep their real code. Returns the
    number of lines neutralized. Mutates the in-memory notebook only; the
    original file is never written.
    """
    count = 0
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        new_lines = []
        for line in cell.source.splitlines(keepends=True):
            if _PIP_MAGIC.match(line):
                indent = _PIP_MAGIC.match(line).group(1)
                newline = "\n" if line.endswith("\n") else ""
                new_lines.append(f"{indent}# [run_notebooks] neutralized: {line.strip()}{newline}")
                count += 1
            else:
                new_lines.append(line)
        cell.source = "".join(new_lines)
    return count


def ensure_kernel() -> None:
    """Register the current interpreter as a Jupyter kernel (idempotent)."""
    from jupyter_client.kernelspec import KernelSpecManager

    if KERNEL_NAME in KernelSpecManager().find_kernel_specs():
        return
    subprocess.run(
        [
            sys.executable, "-m", "ipykernel", "install",
            "--user", "--name", KERNEL_NAME, "--display-name", "GraphRAG Workshop",
        ],
        check=True,
        capture_output=True,
    )


def run_notebook(nb: Notebook, tmp_dir: Path, timeout: int) -> Result:
    """Neutralize, execute, and score a single notebook."""
    import nbformat
    import papermill as pm

    doc = nbformat.read(str(nb.path), as_version=4)
    neutralized = neutralize_pip(doc)

    temp_in = tmp_dir / f"{nb.path.stem}__prepared.ipynb"
    temp_out = tmp_dir / f"{nb.path.stem}__executed.ipynb"
    nbformat.write(doc, str(temp_in))

    rel = nb.path.relative_to(REPO_ROOT)
    print(f"\n─── Running {rel}  (neutralized {neutralized} install line(s)) ───", flush=True)

    try:
        pm.execute_notebook(
            str(temp_in),
            str(temp_out),
            kernel_name=KERNEL_NAME,
            cwd=str(nb.path.parent),  # so relative lib/ imports resolve
            execution_timeout=timeout,
            progress_bar=False,
            stdout_file=sys.stdout,
            stderr_file=sys.stderr,
        )
    except pm.exceptions.PapermillExecutionError as exc:
        detail = f"{exc.ename}: {exc.evalue}\n" + "".join(exc.traceback or [])
        return Result(nb, "FAIL", reason=f"{exc.ename}: {exc.evalue}", detail=detail)
    except Exception as exc:  # noqa: BLE001 - report any executor error as a failure
        return Result(nb, "FAIL", reason=str(exc), detail=traceback.format_exc())

    return Result(nb, "PASS")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def select_notebooks(labs: set[str], include_deploy: bool) -> list[tuple[Notebook, str | None]]:
    """Return (notebook, skip_reason) pairs for the chosen labs.

    ``skip_reason`` is ``None`` when the notebook should run.
    """
    selected: list[tuple[Notebook, str | None]] = []
    for nb in NOTEBOOKS:
        if nb.lab not in labs:
            continue
        if nb.is_deploy and not include_deploy:
            selected.append((nb, "deploy notebook (use --include-deploy)"))
        elif nb.requires_mcp and not mcp_available():
            selected.append((nb, "MCP not configured"))
        elif not nb.path.exists():
            selected.append((nb, "notebook file not found"))
        else:
            selected.append((nb, None))
    return selected


def print_summary(results: list[Result]) -> None:
    passed = [r for r in results if r.status == "PASS"]
    failed = [r for r in results if r.status == "FAIL"]
    skipped = [r for r in results if r.status == "SKIP"]

    print("\n" + "═" * 60)
    print("Results")
    print("═" * 60)
    for r in results:
        rel = r.notebook.path.relative_to(REPO_ROOT)
        line = f"  {r.status:<4}  {rel}"
        if r.reason:
            line += f"  ({r.reason})"
        print(line)
    print(
        f"\n  Passed: {len(passed)}   Failed: {len(failed)}   "
        f"Skipped: {len(skipped)}   Total: {len(results)}"
    )

    if failed:
        print("\n" + "─" * 60)
        print("Failure detail")
        print("─" * 60)
        for r in failed:
            print(f"\n### {r.notebook.path.relative_to(REPO_ROOT)}")
            print(r.detail.rstrip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--labs",
        default=None,
        help="Labs to run: '4', '3,4,6', '4-6', or 'appendix'. Default: all in-scope.",
    )
    parser.add_argument(
        "--env",
        type=Path,
        default=DEFAULT_ENV,
        help=f"Env file to inject (Option A). Default: {DEFAULT_ENV}",
    )
    parser.add_argument(
        "--include-deploy",
        action="store_true",
        help="Also run deploy notebooks (Lab 4 02, Appendix 02). Off by default.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Per-cell execution timeout in seconds (default: 600).",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the prepared/executed temp notebooks for inspection.",
    )
    args = parser.parse_args()

    try:
        labs = parse_labs(args.labs)
    except ValueError as exc:
        parser.error(str(exc))

    if not labs:
        parser.error(f"no in-scope labs selected from '{args.labs}' (choose from {', '.join(_KNOWN_LABS)})")

    inject_env(args.env)
    ensure_kernel()

    plan = select_notebooks(labs, args.include_deploy)
    if not plan:
        print(f"No in-scope notebooks for labs: {', '.join(sorted(labs))}")
        return 0

    print(f"Env: {args.env}")
    print(f"Labs: {', '.join(sorted(labs))}")
    print(f"MCP available: {mcp_available()}")

    results: list[Result] = []
    tmp_root = Path(tempfile.mkdtemp(prefix="run_notebooks_"))
    try:
        for nb, skip_reason in plan:
            if skip_reason is not None:
                rel = nb.path.relative_to(REPO_ROOT)
                print(f"\n─── SKIP {rel}  ({skip_reason}) ───", flush=True)
                results.append(Result(nb, "SKIP", reason=skip_reason))
                continue
            results.append(run_notebook(nb, tmp_root, args.timeout))
    finally:
        if not args.keep_temp:
            for f in tmp_root.glob("*"):
                f.unlink()
            tmp_root.rmdir()
        else:
            print(f"\nTemp notebooks kept in: {tmp_root}")

    print_summary(results)
    return 1 if any(r.status == "FAIL" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
