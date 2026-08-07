# staging/

The Python the Neo4j AWS workshop's lab notebook installs at run time, instead of
importing from a file shipped beside it.

**Everything in this directory is generated.** The source lives in the private
`aws-vocareum` repository under `src/workshop_lab/`, and
`aws-vocareum/scripts/sync_workshop_lab.py` writes it here. Edit it there. An
edit made here is overwritten on the next sync, and
`aws-vocareum/tests/test_workshop_lab_drift.py` fails while the two disagree.

## Why the notebook installs its helpers instead of shipping them

Vocareum's documentation says everything in `/voc/startercode` is copied into
each student's `/voc/work`, and Jupyter puts the notebook's own directory on
`sys.path`, so a module sitting next to the notebook should import. Measured
2026-08-06 in a live lab session: it does not. The notebook raised `ImportError`
for its sibling module.

Measured the same day in the same session: the lab account reaches public GitHub
over HTTPS, and `pip` installs from it without complaint. So the helpers are
packaged and installed rather than shipped.

They cannot be installed from `aws-vocareum` itself, because that repository is
private, and a private repository answers both `raw.githubusercontent.com` and
the archive endpoint with **404, not 403**. From the client, a missing file and a
private repository are the same answer. This repository is public, which is the
only reason the install works.

## What the notebook runs

Step 0 of `lab-01-verify-environment.ipynb`:

```python
%pip install --quiet "https://github.com/neo4j-partners/neo4j-bedrock-graphrag-workshop/archive/refs/heads/main.zip#subdirectory=staging"
```

`#subdirectory=staging` points pip at this directory's `pyproject.toml` rather
than at the repository root, so the rest of the workshop repository is downloaded
and ignored.

**pip reinstalls from a direct URL even when the version has not changed.**
Verified empirically while building this. That is the whole benefit of the
approach: a helper can be fixed and pushed here, and the next student to run
step 0 gets the fix, with no notebook to republish and no Vocareum click path to
repeat.

## What is here

| Path | Role |
| --- | --- |
| `workshop_lab/__init__.py` | The public surface: `Harness`, `Names`, `Neo4jProbe`, the `PASS`/`FAIL`/`SKIP` verdicts, and `__version__` |
| `workshop_lab/guards.py` | The three checks that stop the notebook rather than warn it: credentials present, account expected, region `us-east-1` |
| `workshop_lab/harness.py` | One object owning the boto3 session, the cached clients, the result list, the deferred deletes, and the waiters |
| `workshop_lab/naming.py` | Every resource name and tag the notebook uses, derived from one prefix |
| `workshop_lab/neo4j_probe.py` | The Aura round trip, which is the one check that talks to something other than AWS |
| `pyproject.toml` | Enough packaging for pip to build the directory. Generated, including the version |

## Pinning before a class

The install URL above tracks `refs/heads/main`, which moves. Once the content
settles for a cohort, tag it and pin the tag, so a push mid-class cannot change
what a student installs:

```
https://github.com/neo4j-partners/neo4j-bedrock-graphrag-workshop/archive/refs/tags/lab-v1.zip#subdirectory=staging
```

A commit SHA works the same way. GitHub caches a branch archive briefly, so a
push is not instantly visible to a class already running; a tag or SHA has no
such lag because it can never change.
