# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/registry.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""Copy a container image between registries using only the standard library.

Vocareum runs an EventBridge rule in every student account that calls StopBuild
about five seconds into every CodeBuild build. The build dies in PROVISIONING,
no buildspec command runs, and no student can produce the container image the
rest of the lab needs. The workshop ships a pre-built linux/arm64 image instead.
AgentCore Runtime accepts an image only from the caller's own private ECR in the
same region, so the notebook has to put a copy of that image into the student's
own account before it can create a Runtime.

The Vocareum Notebook lab type has no Docker daemon, so `docker pull` and
`docker push` do not exist here. What is left is the OCI Registry HTTP API v2
spoken directly over `urllib`, which is what this module is. Standard library
plus boto3, because the student environment is not guaranteed to have anything
else.

Two measured facts shape the retries below.

Unauthenticated pulls from `public.ecr.aws` are capped at 1 per second per
source IP, and the cap is not adjustable. Measured 2026-08-06: a burst of 30
concurrent copies from one IP had 9 of 30 refused with HTTP 429
`TOOMANYREQUESTS`, and every single refusal landed on the manifest GET. Blob
reads answer 307 to pre-signed S3 and leave the throttled front door
immediately, so they were never refused. Jittered exponential backoff on the
manifest GET took the same burst to 30 of 30, worst case 5.5 seconds to a 200.
A class of thirty students may start within the same few minutes, and whether
Vocareum puts them behind one egress IP is unknown, so the backoff ships.

A 30 MB layer crossing two registries gets its connection reset often enough to
matter. There is no resuming a half-written chunked upload without knowing what
the destination kept, so each blob attempt opens a fresh upload session.

This used to be inlined into a generated notebook cell, because a sibling module
does not reach a Vocareum workspace. It is installed with the rest of
`workshop_lab` now, so there is one copy again. `tests/test_workshop_lab_drift.py`
is what keeps the published copy honest.
"""

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

MANIFEST_TYPES = ",".join(
    [
        "application/vnd.docker.distribution.manifest.v2+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.oci.image.index.v1+json",
    ]
)
INDEX_TYPES = frozenset(
    {
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.index.v1+json",
    }
)
TARGET_PLATFORM = ("linux", "arm64")
UPLOAD_CHUNK = 5 * 1024 * 1024

# 429 is the anonymous pull throttle. The 5xx codes are the registry failing in
# a way that says nothing about the request, so both are worth another attempt.
# Nothing else is: a 401 or a 404 will still be a 401 or a 404 on the sixth try,
# and retrying those turns a clear failure into a slow one.
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
MANIFEST_ATTEMPTS = 6
BLOB_ATTEMPTS = 4
MAX_BACKOFF_SECONDS = 20


def _ignore_progress(name: str, verdict: str, detail: str = "") -> None:
    """Discard one progress row, which is what `copy_image` does by default."""


class StripAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    """Drop the registry credential when a blob redirects to object storage.

    Blob reads answer 307 to a pre-signed S3 URL. Forwarding the registry's
    Authorization header to that URL makes S3 reject the request for carrying
    two authentication mechanisms, so it has to come off before the hop.
    """

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            for store in (redirected.headers, redirected.unredirected_hdrs):
                for key in [k for k in store if k.lower() == "authorization"]:
                    del store[key]
        return redirected


_opener = urllib.request.build_opener(StripAuthOnRedirect)


def request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    tolerate: tuple[int, ...] = (),
) -> tuple[int, bytes, dict[str, str]]:
    """Make one registry call and return its status, body, and headers."""
    call = urllib.request.Request(url, data=body, method=method)
    for key, value in (headers or {}).items():
        call.add_header(key, value)
    try:
        with _opener.open(call, timeout=300) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as error:
        if error.code in tolerate:
            return error.code, error.read(), dict(error.headers)
        raise


def request_with_retry(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    tolerate: tuple[int, ...] = (),
    attempts: int = MANIFEST_ATTEMPTS,
    sleep: Callable[[float], None] = time.sleep,
    jitter: Callable[[float, float], float] = random.uniform,
) -> tuple[int, bytes, dict[str, str]]:
    """Make one registry call, backing off on throttling and on server faults.

    This exists for the manifest GET. That is the one request the anonymous
    pull throttle refuses under load, and until 2026-08-06 it was the only
    request in the copy with no retry around it at all, so a 429 there failed
    the whole run. Blob reads happened to retry already, because
    `copy_blob_with_retry` catches `URLError` and `HTTPError` subclasses it.
    Retrying by accident is not a property worth depending on, so the manifest
    GET says what it means.

    The backoff is jittered because thirty students throttled at the same
    instant would otherwise all wake at the same instant and throttle each
    other again. `sleep` and `jitter` are arguments so the tests can run
    offline and without waiting.
    """
    for attempt in range(1, attempts + 1):
        try:
            return request(method, url, headers=headers, body=body, tolerate=tolerate)
        except urllib.error.HTTPError as error:
            if error.code not in RETRY_STATUSES or attempt == attempts:
                raise
            sleep(min(2**attempt, MAX_BACKOFF_SECONDS) * jitter(0.5, 1.5))
    raise AssertionError("unreachable")


@dataclass(frozen=True)
class Registry:
    """One registry endpoint and the header that authenticates to it."""

    host: str
    repository: str
    auth: str

    def url(self, path: str) -> str:
        return f"https://{self.host}/v2/{self.repository}/{path}"

    def headers(self, **extra: str) -> dict[str, str]:
        return {"Authorization": self.auth, **extra}


def parse_reference(reference: str) -> tuple[str, str, str]:
    """Split `host/namespace/repo:tag` into host, repository, and tag."""
    remainder, _, tag = reference.rpartition(":")
    if "/" in tag or not remainder:
        raise ValueError(f"expected host/repository:tag, got {reference!r}")
    host, _, repository = remainder.partition("/")
    if not repository:
        raise ValueError(f"expected host/repository:tag, got {reference!r}")
    return host, repository, tag


def public_pull_token(host: str, repository: str) -> str:
    """Fetch the anonymous pull token a public registry hands out."""
    query = urllib.parse.urlencode(
        {"scope": f"repository:{repository}:pull", "service": host}
    )
    _, body, _ = request_with_retry("GET", f"https://{host}/token/?{query}")
    return f"Bearer {json.loads(body)['token']}"


def private_push_auth(ecr: Any) -> str:
    """Fetch the Basic credential ECR issues for its own registry."""
    token = ecr.get_authorization_token()["authorizationData"][0]["authorizationToken"]
    return f"Basic {token}"


def select_platform_manifest(source: Registry, raw: bytes) -> tuple[bytes, str]:
    """Resolve a multi-platform index down to the linux/arm64 manifest."""
    index = json.loads(raw)
    for entry in index.get("manifests", []):
        platform = entry.get("platform", {})
        pair = (platform.get("os"), platform.get("architecture"))
        if pair == TARGET_PLATFORM:
            _, body, response_headers = request_with_retry(
                "GET",
                source.url(f"manifests/{entry['digest']}"),
                headers=source.headers(Accept=MANIFEST_TYPES),
            )
            return body, response_headers.get("Content-Type", "")
    raise RuntimeError("the source image has no linux/arm64 manifest")


def referenced_digests(manifest: dict[str, Any]) -> Iterator[str]:
    """Yield the config digest and every layer digest, in push order."""
    yield manifest["config"]["digest"]
    for layer in manifest["layers"]:
        yield layer["digest"]


def absolute(host: str, location: str) -> str:
    """Turn a registry's upload Location into a full URL."""
    if location.startswith("http"):
        return location
    return f"https://{host}{location}"


def read_exactly(stream: Any, size: int) -> bytes:
    """Read up to size bytes, short only at the end of the stream."""
    buffer = bytearray()
    while len(buffer) < size:
        piece = stream.read(size - len(buffer))
        if not piece:
            break
        buffer += piece
    return bytes(buffer)


def copy_blob(source: Registry, dest: Registry, digest: str) -> str:
    """Copy one blob if the destination does not already hold it.

    The upload goes out as a sequence of PATCH chunks closed by a PUT rather
    than as a single monolithic PUT. ECR accepts a monolithic PUT for something
    the size of a config blob and drops the connection partway through one the
    size of a layer, which surfaces as a broken pipe rather than an HTTP error.
    Chunking also keeps a layer of any size out of memory.
    """
    status, _, _ = request(
        "HEAD", dest.url(f"blobs/{digest}"), headers=dest.headers(), tolerate=(404,)
    )
    if status == 200:
        return "already present"

    _, _, opened = request(
        "POST",
        dest.url("blobs/uploads/"),
        headers=dest.headers(**{"Content-Length": "0"}),
    )
    location = absolute(dest.host, opened["Location"])

    pull = urllib.request.Request(source.url(f"blobs/{digest}"), method="GET")
    for key, value in source.headers().items():
        pull.add_header(key, value)

    offset = 0
    with _opener.open(pull, timeout=300) as blob:
        while chunk := read_exactly(blob, UPLOAD_CHUNK):
            _, _, patched = request(
                "PATCH",
                location,
                headers=dest.headers(
                    **{
                        "Content-Type": "application/octet-stream",
                        "Content-Range": f"{offset}-{offset + len(chunk) - 1}",
                    }
                ),
                body=chunk,
            )
            offset += len(chunk)
            location = absolute(dest.host, patched.get("Location", location))

    separator = "&" if "?" in location else "?"
    request(
        "PUT",
        f"{location}{separator}digest={digest}",
        headers=dest.headers(**{"Content-Length": "0"}),
    )
    return f"{offset // 1024} KiB"


def copy_blob_with_retry(
    source: Registry,
    dest: Registry,
    digest: str,
    attempts: int = BLOB_ATTEMPTS,
    record: Callable[[str, str, str], None] = _ignore_progress,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Copy one blob, starting a fresh upload if the connection drops.

    A 30 MB layer crossing two registries gets its connection reset often
    enough to matter. There is no resuming a half-written chunked upload
    without knowing what the registry kept, so each attempt opens a new upload
    session. Blobs already committed are skipped by the HEAD in `copy_blob`.
    """
    for attempt in range(1, attempts + 1):
        try:
            return copy_blob(source, dest, digest)
        except (urllib.error.URLError, ConnectionError) as error:
            if attempt == attempts:
                raise
            record(
                f"registry: blob {digest[7:19]}",
                "INFO",
                f"{error}, retrying ({attempt}/{attempts - 1})",
            )
            sleep(3 * attempt)
    raise AssertionError("unreachable")


def copy_image(
    source_ref: str,
    dest_ref: str,
    ecr: Any,
    record: Callable[[str, str, str], None] = _ignore_progress,
) -> str:
    """Copy a whole image between registries without a Docker daemon.

    `record` takes a check name, a verdict, and a detail, which is the shape of
    the notebook's own reporting function. It defaults to a no-op so a caller
    that reports differently is not forced to supply one.
    """
    source_host, source_repo, source_tag = parse_reference(source_ref)
    dest_host, dest_repo, dest_tag = parse_reference(dest_ref)

    source = Registry(
        source_host, source_repo, public_pull_token(source_host, source_repo)
    )
    dest = Registry(dest_host, dest_repo, private_push_auth(ecr))

    _, raw, response_headers = request_with_retry(
        "GET",
        source.url(f"manifests/{source_tag}"),
        headers=source.headers(Accept=MANIFEST_TYPES),
    )
    media_type = response_headers.get("Content-Type", "")
    if media_type in INDEX_TYPES:
        raw, media_type = select_platform_manifest(source, raw)

    manifest = json.loads(raw)
    for digest in referenced_digests(manifest):
        copy_blob_with_retry(source, dest, digest, record=record)

    request(
        "PUT",
        dest.url(f"manifests/{dest_tag}"),
        headers=dest.headers(**{"Content-Type": media_type}),
        body=raw,
    )
    record(
        "registry: copied pre-built image to ECR",
        "PASS",
        f"{dest_ref}, {len(manifest['layers'])} layers",
    )
    return dest_ref
