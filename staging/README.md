# staging/

Python that a lab notebook fetches at run time instead of importing from a file
beside itself.

## Why this directory exists

A Vocareum notebook workspace does not reliably receive the helper files that
sit next to the notebook in source control. Vocareum's documentation says
everything in `/voc/startercode` is copied into each student's `/voc/work`, and
Jupyter puts the notebook's own directory on `sys.path`, so a sibling module
should import. Measured 2026-08-06 in a real lab session: it does not. Step 1 of
the `aws-vocareum` lab notebook raised `ImportError` for its sibling
`workshop_version`.

That leaves two ways to get Python in front of a student, and this directory is
the second one:

1. **Inline it.** `aws-vocareum/scripts/sync_notebook_module.py` copies a module
   into a generated notebook cell, and `tests/test_notebook_drift.py` fails when
   the cell and the module disagree. No network, one artifact to publish, but
   every helper edit means regenerating and republishing the notebook.
2. **Fetch it.** The notebook pulls the module from a public URL. Helper code
   changes without republishing, at the cost of a run-time dependency on GitHub
   being reachable and up when the class starts.

This repository is public, so option 2 is testable here. `aws-vocareum` is
private, and a private repo answers `raw.githubusercontent.com` requests with
**404, not 403** — which is why the fetch cannot be hosted there and why a
missing file and a private repo are indistinguishable from the client.

## What is here

| File | Role |
| --- | --- |
| `workshop_version.py` | Two-line constant plus `version_banner()`. The smallest thing that proves an import worked. |
| `workshop_registry.py` | The real payload: 14 KB, stdlib-only, copies a container image between registries over the OCI Registry HTTP API. Verbatim copy of `aws-vocareum/notebooks/workshop_registry.py`. |
| `test_raw_import.py` | The loader, plus a harness that fetches both modules and reports PASS/FAIL. |

`workshop_registry.py` is a **copy**, and nothing currently keeps it in step with
the original in `aws-vocareum`. Decide the mechanism before treating this as the
source of truth; the inline path over there has a drift test and this does not.

## Running the test

```bash
python3 staging/test_raw_import.py                 # against main
python3 staging/test_raw_import.py --ref my-branch # against a branch
```

Run it on a laptop and it proves the URLs resolve and the modules execute. Run
it in a **lab notebook cell** and it proves the student account has egress to
`raw.githubusercontent.com`. Only the second result decides anything. The lab
account is known to reach PyPI and `public.ecr.aws`; GitHub has not been
measured from inside one.

## The loader

`load_from_github` in `test_raw_import.py` is the part that ends up in a
notebook cell. Standard library only, because it has to run before anything can
be installed.

```python
import importlib.util
import sys
import urllib.request

def load_from_github(module_name, ref="main", force=False):
    if not force and module_name in sys.modules:
        return sys.modules[module_name]
    url = (
        f"https://raw.githubusercontent.com/neo4j-partners/"
        f"neo4j-bedrock-graphrag-workshop/{ref}/staging/{module_name}.py"
    )
    with urllib.request.urlopen(url, timeout=30) as response:
        source = response.read().decode("utf-8")
    spec = importlib.util.spec_from_loader(module_name, loader=None, origin=url)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = url
    sys.modules[module_name] = module
    exec(compile(source, url, "exec"), module.__dict__)
    return module

version = load_from_github("workshop_version")
print(version.version_banner())
```

Three details in the full version that are not decoration:

- **Compiling under the URL** puts the URL in any traceback, so a student
  reporting an error names the file you can actually open.
- **404 gets its own message.** It means either "not pushed to this ref yet" or
  "repo is private", and the client cannot tell which.
- **`force`.** The `sys.modules` check returns whatever is already registered
  under that name, not necessarily what was requested. Measured while writing
  this: asking for `keyword` from `python/cpython` returns the local stdlib
  module and issues no request at all. A stale sidecar copy in `/voc/work` would
  do the same to a lab notebook, silently. Check `module.__file__` when it
  matters.

## Pinning

The examples use `main`, which moves. Once the content settles, pin a commit SHA
so every student in a class runs the same bytes:

```
https://raw.githubusercontent.com/neo4j-partners/neo4j-bedrock-graphrag-workshop/<sha>/staging/workshop_version.py
```

`raw.githubusercontent.com` caches a branch URL for about five minutes, so a
push is not visible to a running class immediately. A SHA URL has no such lag
because it can never change.
