"""The published revision of the lab notebook, fetched over raw.githubusercontent.com.

This module is a test of a mechanism as much as it is a constant.

A Vocareum notebook workspace does not reliably receive the helper files that
sit beside the notebook in source control. Vocareum's documentation says
everything in ``/voc/startercode`` is copied into each student's ``/voc/work``,
and Jupyter runs a notebook with its own directory on ``sys.path``, so a sibling
module beside the notebook should import. Measured 2026-08-06: it does not. Step
1 of the lab notebook raised ``ImportError`` for the sibling ``workshop_version``.

So the module moves out of the workspace entirely and onto a public URL. This
file is the smallest thing that proves the replacement works in a real lab
session. If step 1 prints the banner, a student notebook can pull Python from a
public GitHub repository at run time, and the generated-cell machinery in
``aws-vocareum`` (``scripts/sync_notebook_module.py``) is a choice rather than a
constraint. If the fetch raises, the generated cell stays the only mechanism
that ships code to a student.

``workshop_registry.py`` sits beside this file so the same test also covers a
real 14 KB module with imports and classes, not just a two-line constant. A
mechanism that carries a banner but chokes on the module that matters has not
been tested.
"""

# Bump this when the published notebook changes, so a student's output names the
# revision they actually ran.
NOTEBOOK_VERSION = "1.1.0"

# Where this file was served from. Kept as a literal rather than derived from
# ``__file__`` because the loader sets ``__file__`` to the URL and a student
# reading the banner should be able to see the expected source without trusting
# the loader that produced it.
SOURCE = (
    "https://raw.githubusercontent.com/neo4j-partners/"
    "neo4j-bedrock-graphrag-workshop/main/staging/workshop_version.py"
)


def version_banner() -> str:
    """Return the single line step 1 prints above the credential check."""
    return f"Lab 1 notebook version: {NOTEBOOK_VERSION} (fetched from raw.githubusercontent.com)"
