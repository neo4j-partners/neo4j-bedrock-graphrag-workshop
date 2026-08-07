# This file is generated. Editing it here is wasted work.
#
# Source:     aws-vocareum/src/workshop_lab/build_source.py
# Regenerate: ./scripts/sync_workshop_lab.py
#
# tests/test_workshop_lab_drift.py fails when the copies disagree.
"""The container the lab builds, and the two places it has to exist first.

CodeBuild does not read the notebook. It reads a zip from S3, so the Dockerfile
and the server have to be files in a bucket before any build can start, and the
ECR repository has to exist before that build has anywhere to push.

Two things here are load-bearing and neither is obvious at the call site.

**The base image is not on AWS.** `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`
is the workshop's own base image, kept on purpose: pulling it is the one part of
the build that needs outbound internet from inside CodeBuild. Swapping it for an
ECR Public image would make the build succeed while measuring nothing about
egress, which is the question step 8 exists to answer.

**The source bucket is shared and is not deleted.** The AgentCore starter toolkit
names one bucket per account and region and reuses it, so a bucket that already
exists is the ordinary case rather than a failure, and teardown removes only the
object this run put in it.
"""

from __future__ import annotations

import io
import zipfile
from typing import TYPE_CHECKING

from botocore.exceptions import ClientError

from workshop_lab.harness import PASS

if TYPE_CHECKING:
    from workshop_lab.harness import Harness

DOCKERFILE = """FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
COPY server.py /app/server.py
EXPOSE 8080
CMD ["python", "/app/server.py"]
"""

# The smallest thing an AgentCore Runtime accepts: an HTTP server answering
# GET /ping and POST /invocations on 8080. It is not an agent. It exists so the
# Runtime can start, be invoked, and prove the path works.
SERVER = """# The smallest container an AgentCore Runtime will accept.
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    # Answers the two routes the AgentCore Runtime contract requires.

    def _send(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/") == "/ping":
            self._send(200, {"status": "Healthy"})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.rstrip("/") != "/invocations":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            received = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            received = {"raw": raw.decode("utf-8", "replace")}
        self._send(200, {"echo": received, "source": "vocareum-verify"})

    def log_message(self, fmt, *args):
        print(self.address_string() + " " + (fmt % args), flush=True)


print("listening on 0.0.0.0:8080", flush=True)
ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
"""


def bundle() -> bytes:
    """Zip the two source files the way CodeBuild expects to find them.

    Both sit at the archive root. CodeBuild's buildspec runs `docker build .`
    against the extracted directory, so a Dockerfile one level down is a build
    that cannot find its own COPY source.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Dockerfile", DOCKERFILE)
        archive.writestr("server.py", SERVER)
    return buffer.getvalue()


class BuildSource:
    """Creates the ECR repository and puts the build source in S3."""

    def __init__(self, lab: Harness) -> None:
        self.lab = lab
        self.zip_bytes = bundle()
        self.repository_created = False
        self.uploaded = False

    @property
    def ecr(self):
        return self.lab.client("ecr")

    @property
    def s3(self):
        return self.lab.client("s3")

    def create_repository(self) -> bool:
        """Create the repository the image is pushed to, and register its delete.

        `force=True` on the delete because a repository holding images refuses an
        ordinary delete, and by teardown it usually holds one.
        """
        name = self.lab.names.ecr_repository
        created = self.lab.check(
            f"ecr:CreateRepository {name}",
            lambda: self.ecr.create_repository(
                repositoryName=name, tags=self.lab.names.tags_list
            ),
        )
        if created is not None:
            self.lab.defer(
                f"ecr repository {name}",
                lambda: self.ecr.delete_repository(repositoryName=name, force=True),
            )
        self.repository_created = created is not None
        return self.repository_created

    def ensure_bucket(self) -> None:
        """Reuse the toolkit's shared source bucket, or create it once, and tag it.

        Recorded as PASS when it already exists. The measurement this step owes
        the tracker is whether the account can hold build source at all, and a
        bucket that is already there answers that.

        The tag is a second call because CreateBucket is the one create in this
        notebook that takes no tags at all. It runs on the reuse path too: a
        bucket this run depends on carries the workshop tag whether or not this
        run is the one that made it, and PutBucketTagging replaces the whole tag
        set rather than failing on a bucket that already has one.
        """
        bucket = self.lab.names.source_bucket
        try:
            self.s3.head_bucket(Bucket=bucket, ExpectedBucketOwner=self.lab.account_id)
        except ClientError:
            created = self.lab.check(
                "s3:CreateBucket source bucket",
                lambda: self.s3.create_bucket(Bucket=bucket),
            )
            if created is None:
                return
        else:
            self.lab.record(
                "s3:CreateBucket source bucket", PASS, "already exists, reused"
            )
        self.lab.check(
            "s3:PutBucketTagging source bucket",
            lambda: self.s3.put_bucket_tagging(
                Bucket=bucket,
                Tagging={"TagSet": self.lab.names.tags_list},
                ExpectedBucketOwner=self.lab.account_id,
            ),
        )

    def upload(self) -> bool:
        """Put the zip at the key CodeBuild will be pointed at, tagged.

        `Tagging` on PutObject authorizes against `s3:PutObjectTagging` as well
        as `s3:PutObject`. Without the second grant this call is refused outright
        rather than storing the object untagged, so `lab.template` grants both
        and this check failing on `AccessDenied` means the template is behind.
        """
        bucket, key = self.lab.names.source_bucket, self.lab.names.source_key
        put = self.lab.check(
            "s3:PutObject build source",
            lambda: self.s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=self.zip_bytes,
                Tagging=self.lab.names.tags_query,
                ExpectedBucketOwner=self.lab.account_id,
            ),
            f"{len(self.zip_bytes)} bytes to s3://{bucket}/{key}",
        )
        if put is not None:
            self.lab.defer(
                f"s3 object {key}",
                lambda: self.s3.delete_object(Bucket=bucket, Key=key),
            )
        self.uploaded = put is not None
        return self.uploaded

    def prepare(self) -> bool:
        """Do all three, and report whether step 8 has something to build.

        The bucket is not part of the return value. Its own check already
        recorded a verdict, and the thing step 8 needs is the object, which
        cannot have uploaded if the bucket is missing.
        """
        self.create_repository()
        self.ensure_bucket()
        self.upload()
        return self.repository_created and self.uploaded
