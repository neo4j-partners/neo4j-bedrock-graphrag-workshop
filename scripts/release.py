#!/usr/bin/env python3
"""Commit, tag, and push the published `workshop_lab` package.

The verification notebook's step 0 installs `workshop_lab` from a GitHub
archive of this repository at a pinned tag. That tag is the only thing standing
between a fix and a student, and it fails quietly: an archive URL naming a tag
that does not exist answers 404, and `%pip install` reports it as a package
that could not be found.

Nothing here edits code. The source of `staging/workshop_lab/` lives in the
private `aws-vocareum` repository and is copied in by its
`scripts/sync_workshop_lab.py`. By the time this script runs, the version has
already been bumped there and synced here, so the version to tag is read out of
the published copy rather than passed on the command line. A tag that does not
match what `staging/` actually holds is the failure this exists to prevent.

    ./scripts/release.py            # show what would happen, change nothing
    ./scripts/release.py --push     # commit, tag, and push

Uses no dependencies, so it runs under any Python 3.11+ without uv.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_INIT = REPOSITORY_ROOT / "staging" / "workshop_lab" / "__init__.py"
PROJECT_FILE = REPOSITORY_ROOT / "staging" / "pyproject.toml"

# Only the published package is committed here. Everything else in this
# repository is a lab, released on its own schedule, and sweeping it into a
# `workshop_lab` commit would put unreviewed notebook edits behind a tag that
# claims to be a package release.
PUBLISHED = "staging"
REMOTE = "origin"

VERSION_LINE = re.compile(r'^__version__\s*=\s*"([^"]+)"', re.MULTILINE)
PROJECT_VERSION_LINE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)


def git(*arguments: str) -> str:
    """Run git in this repository and return its stdout, or stop with stderr.

    A failing git command prints its reason on stderr and nothing on stdout, so
    a caller that ignored the exit code would carry on with an empty string and
    tag the wrong thing.

    Only newlines come off the end. `git status --porcelain` encodes the state
    of a file in the first two columns and leaves the first one blank for an
    unstaged change, so stripping whitespace would shift the first line's path
    by a character.
    """
    done = subprocess.run(
        ["git", "-C", str(REPOSITORY_ROOT), *arguments],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        detail = (done.stderr or done.stdout).strip()
        sys.exit(f"git {' '.join(arguments)} failed: {detail}")
    return done.stdout.rstrip("\n")


def read_version(path: Path, pattern: re.Pattern[str]) -> str:
    if not path.exists():
        sys.exit(
            f"{path} is missing. Run scripts/sync_workshop_lab.py in aws-vocareum."
        )
    found = pattern.search(path.read_text(encoding="utf-8"))
    if found is None:
        sys.exit(f"{path} declares no version.")
    return found.group(1)


def published_version() -> str:
    """Return the version both published files agree on.

    They are written by the same sync, so a disagreement means the sync was
    interrupted or one file was hand-edited. Tagging either number would ship a
    package whose metadata contradicts the `__version__` step 0 prints, which
    is the one signal a student has that a fix landed.
    """
    package = read_version(PACKAGE_INIT, VERSION_LINE)
    project = read_version(PROJECT_FILE, PROJECT_VERSION_LINE)
    if package != project:
        sys.exit(
            f"version mismatch: {PACKAGE_INIT.name} says {package}, "
            f"{PROJECT_FILE.name} says {project}. Re-run "
            "scripts/sync_workshop_lab.py in aws-vocareum."
        )
    return package


def pending() -> list[str]:
    """Return the published files that differ from the last commit."""
    status = git("status", "--porcelain", "--", PUBLISHED)
    return [line[3:] for line in status.splitlines() if line]


def local_tag_commit(tag: str) -> str | None:
    found = git("tag", "--list", tag)
    return git("rev-list", "-n", "1", tag) if found else None


def remote_tag_commit(tag: str) -> str | None:
    """Return the commit the remote has under this tag, if it has one.

    Checked separately from the local tag because the two go out of sync in
    both directions: a tag pushed from another machine is absent here, and a
    tag created here and never pushed is absent there. Only the remote one is
    what a student installs.
    """
    for line in git("ls-remote", "--tags", REMOTE, f"refs/tags/{tag}").splitlines():
        commit, _, reference = line.partition("\t")
        # Annotated tags also answer with a `^{}` line naming the commit the
        # tag object points at. Either line identifies the same release.
        if reference.rstrip("^{}") == f"refs/tags/{tag}":
            return commit
    return None


def refuse_to_move(tag: str, commit: str, where: str) -> None:
    sys.exit(
        f"{tag} already exists {where}, at {commit[:12]}, and this would move it.\n"
        "Moving a tag changes what step 0 installs for anyone who has already "
        "run it, without changing the version they see printed.\n"
        f"Bump __version__ in aws-vocareum's src/workshop_lab/__init__.py, "
        "re-run scripts/sync_workshop_lab.py, then run this again."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--push",
        action="store_true",
        help="actually commit, tag, and push (default is to print the plan)",
    )
    options = parser.parse_args()

    version = published_version()
    tag = f"v{version}"
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch == "HEAD":
        sys.exit(
            "HEAD is detached, so there is no branch to push. Check one out first."
        )
    changed = pending()

    local = local_tag_commit(tag)
    remote = remote_tag_commit(tag)
    head = git("rev-parse", "HEAD")

    # An existing tag plus staged changes is the dangerous combination: the tag
    # would have to move to include them. An existing tag with nothing pending
    # is just a release that is already out.
    if changed and local is not None:
        refuse_to_move(tag, local, "locally")
    if changed and remote is not None:
        refuse_to_move(tag, remote, f"on {REMOTE}")
    if not changed and local is not None and local != head:
        refuse_to_move(tag, local, "locally")

    if not changed and remote is not None:
        print(f"{tag} is already published at {remote[:12]}. Nothing to do.")
        return 0

    print(f"version   {version}   (from staging/)")
    print(f"branch    {branch}")
    if changed:
        for path in changed:
            print(f"  staged  {path}")
    else:
        print("  no staging/ changes; tagging the current commit")

    if not options.push:
        print("\nDry run. Re-run with --push to commit, tag, and push.")
        return 0

    if changed:
        git("add", "--all", "--", PUBLISHED)
        git("commit", "-m", f"workshop_lab {version}")
        print(f"committed workshop_lab {version}")
    if local is None:
        git("tag", tag)
    git("push", REMOTE, branch)
    git("push", REMOTE, tag)

    # The push can report success and still leave the remote without the tag if
    # the ref was rejected, and a missing tag is a 404 at step 0 rather than an
    # error anyone here would see.
    published = remote_tag_commit(tag)
    if published is None:
        sys.exit(f"{tag} is still not on {REMOTE}. Students would get a 404 at step 0.")
    print(f"pushed {tag} at {published[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
