# Antora Build Errors

Pre-existing errors found during site build. These are not caused by the Lab 6 restructure.

## 1. Missing image: mcp-agent-architecture.png

**File:** `site/modules/ROOT/pages/lab5.adoc`
**Error:** `target of image not found: mcp-agent-architecture.png`
**Cause:** lab5.adoc references `image::mcp-agent-architecture.png` but the image file does not exist in `site/modules/ROOT/images/`.

## 2. Broken xref: lab5-sample-queries.adoc

**File:** `site/modules/ROOT/pages/sample-queries.adoc`
**Error:** `target of xref not found: lab5-sample-queries.adoc`
**Cause:** `sample-queries.adoc` links to `xref:lab5-sample-queries.adoc` but `lab5-sample-queries.adoc` only exists in `archive_pages/`, not in `pages/`.
