#!/usr/bin/env python3
"""Prove a notebook can import Python served from this public repository.

Run it anywhere with network access:

    python3 staging/test_raw_import.py

Run it against a branch that is not ``main``:

    python3 staging/test_raw_import.py --ref my-branch

The ``load_from_github`` function below is the part that ends up in a notebook
cell. Everything under ``__main__`` is the test harness and does not ship.

Why this exists: a Vocareum notebook workspace does not reliably receive the
helper files that sit beside the notebook in source control, so the lab notebook
in ``aws-vocareum`` either inlines its helpers into a generated cell or fetches
them at run time. This script measures whether the fetch half of that choice
actually works from the environment a student is sitting in. Running it on a
laptop proves the URLs resolve; running it in a lab notebook cell proves the lab
account has egress to ``raw.githubusercontent.com``, which is the only result
that decides anything.

Standard library only, deliberately. The student environment is not guaranteed
to have ``requests`` and this has to run before anything can be installed.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import urllib.error
import urllib.request

OWNER_REPO = "neo4j-partners/neo4j-bedrock-graphrag-workshop"
DIRECTORY = "staging"

# The modules this test fetches. ``workshop_version`` is a two-line constant and
# ``workshop_registry`` is a 14 KB module with classes and dataclasses. Both are
# named because a mechanism that carries a banner but chokes on the module that
# matters has not been tested.
MODULES = ("workshop_version", "workshop_registry")


# --------------------------------------------------------------------------
# This is the part that goes in a notebook cell.
# --------------------------------------------------------------------------
def load_from_github(
    module_name: str,
    ref: str = "main",
    owner_repo: str = OWNER_REPO,
    directory: str = DIRECTORY,
    timeout: int = 30,
    force: bool = False,
):
    """Import ``module_name`` from a public GitHub repository over HTTPS.

    Fetches the source, compiles it under its URL so a traceback names where the
    code came from, and registers the result in ``sys.modules`` so a second call
    for the same name is not a second download.

    ``ref`` is a branch, tag, or commit SHA. A branch moves under you between one
    student's run and the next; pin a SHA once the content stops changing.

    The ``sys.modules`` check returns whatever is already registered under this
    name, which is not always what was asked for. Measured while writing this:
    ``load_from_github("keyword", owner_repo="python/cpython")`` returns the
    local stdlib ``keyword`` and never issues a request. The same would happen to
    a lab notebook if a stale sidecar copy of the module were imported first, and
    the student would run old code with no sign that anything was skipped. Pass
    ``force=True`` to bypass the cache and always take the network copy; check
    ``module.__file__`` if you need to know which one you got.
    """
    if not force and module_name in sys.modules:
        return sys.modules[module_name]

    url = f"https://raw.githubusercontent.com/{owner_repo}/{ref}/{directory}/{module_name}.py"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            source = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise ImportError(
                f"{url} returned 404. Either the file is not pushed to "
                f"'{ref}' yet, or the repository is private. A private repo "
                f"answers 404 rather than 403, so the two look identical here."
            ) from error
        raise ImportError(f"{url} returned HTTP {error.code}.") from error
    except urllib.error.URLError as error:
        raise ImportError(
            f"Could not reach {url}: {error.reason}. This environment has no "
            f"route to raw.githubusercontent.com, so the notebook has to carry "
            f"its helpers inline instead of fetching them."
        ) from error

    # spec_from_loader with loader=None builds a module object without asking the
    # import system to find a file for it. exec against the module's own __dict__
    # is what an ordinary import does once the source is in hand.
    spec = importlib.util.spec_from_loader(module_name, loader=None, origin=url)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = url
    sys.modules[module_name] = module
    try:
        exec(compile(source, url, "exec"), module.__dict__)
    except Exception:
        # A half-initialised module left in sys.modules would be handed out by
        # the next call as though it had loaded cleanly.
        del sys.modules[module_name]
        raise
    return module


# --------------------------------------------------------------------------
# Test harness.
# --------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref",
        default="main",
        help="branch, tag, or commit SHA to fetch from (default: main)",
    )
    arguments = parser.parse_args()

    print(f"Repository: {OWNER_REPO}")
    print(f"Ref:        {arguments.ref}")
    print(f"Directory:  {DIRECTORY}/")
    print()

    failures = 0

    for module_name in MODULES:
        try:
            # force=True so the test measures the network every time. Without it
            # a local file of the same name would satisfy the call and the run
            # would pass without proving anything.
            module = load_from_github(module_name, ref=arguments.ref, force=True)
        except ImportError as error:
            print(f"FAIL  {module_name}")
            print(f"      {error}")
            failures += 1
            continue

        names = [name for name in vars(module) if not name.startswith("_")]
        print(f"PASS  {module_name}  ({len(names)} public names from {module.__file__})")

    print()

    # The banner is the specific thing step 1 of the lab notebook prints. Checking
    # it here means this script fails for the same reason the notebook would.
    version = sys.modules.get("workshop_version")
    if version is not None:
        print(f"      {version.version_banner()}")
    else:
        print("      no banner: workshop_version did not load")

    # Touching a real symbol proves the module executed rather than merely
    # downloaded. A module that failed halfway can still look importable.
    registry = sys.modules.get("workshop_registry")
    if registry is not None:
        classes = sorted(
            name
            for name, value in vars(registry).items()
            if isinstance(value, type) and not name.startswith("_")
        )
        print(f"      workshop_registry defines: {', '.join(classes) or '(no classes)'}")

    print()
    if failures:
        print(f"{failures} of {len(MODULES)} modules failed to load.")
        return 1
    print(f"All {len(MODULES)} modules loaded from raw.githubusercontent.com.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
