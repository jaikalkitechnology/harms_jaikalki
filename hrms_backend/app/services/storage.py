"""File storage helpers — supports a local mounted directory or S3/MinIO.

The active backend is chosen by `settings.STORAGE_BACKEND` ("local" | "s3").

For "local":
- Files are written under `LOCAL_STORAGE_PATH/{key}`.
- The public URL is `{PUBLIC_BASE_URL}{LOCAL_STORAGE_URL_PREFIX}/{key}`.
- FastAPI mounts `LOCAL_STORAGE_URL_PREFIX` to the same directory in
  `app/main.py`, so files are downloadable directly.

For "s3":
- Files go to `S3_BUCKET` and the public URL points at the endpoint.
- `signed_url(key)` returns a presigned GET for short-lived access.
"""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Optional

from app.config import settings


def _safe_name(filename: str) -> str:
    return filename.replace(" ", "_").replace("/", "_").replace("\\", "_")


def _build_key(key_prefix: str, filename: str) -> str:
    return f"{key_prefix.strip('/')}/{uuid.uuid4().hex}_{_safe_name(filename)}"


# ── Local backend ────────────────────────────────────────────────────
def _local_root() -> Path:
    root = Path(settings.LOCAL_STORAGE_PATH)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _local_url(key: str) -> str:
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    prefix = "/" + settings.LOCAL_STORAGE_URL_PREFIX.strip("/")
    return f"{base}{prefix}/{key}"


def _upload_local(
    fileobj: BinaryIO,
    *,
    key_prefix: str,
    filename: str,
    content_type: Optional[str] = None,  # noqa: ARG001 — no-op for local
) -> tuple[str, str]:
    key = _build_key(key_prefix, filename)
    target = _local_root() / key
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as out:
        shutil.copyfileobj(fileobj, out)
    return key, _local_url(key)


def _delete_local(key: str) -> None:
    target = _local_root() / key
    if target.exists() and target.is_file():
        target.unlink()


# ── S3 backend ───────────────────────────────────────────────────────
def _s3_client():
    import boto3
    from botocore.client import Config

    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name=settings.S3_REGION,
    )


def _ensure_bucket() -> None:
    from botocore.exceptions import ClientError

    s3 = _s3_client()
    try:
        s3.head_bucket(Bucket=settings.S3_BUCKET)
    except ClientError:
        try:
            s3.create_bucket(Bucket=settings.S3_BUCKET)
        except ClientError:
            # Bucket may already exist or another worker created it.
            pass


def _upload_s3(
    fileobj: BinaryIO,
    *,
    key_prefix: str,
    filename: str,
    content_type: Optional[str] = None,
) -> tuple[str, str]:
    _ensure_bucket()
    key = _build_key(key_prefix, filename)
    extra: dict = {}
    if content_type:
        extra["ContentType"] = content_type
    _s3_client().upload_fileobj(
        fileobj, settings.S3_BUCKET, key, ExtraArgs=extra
    )
    base = settings.S3_ENDPOINT.rstrip("/")
    url = f"{base}/{settings.S3_BUCKET}/{key}"
    return key, url


def _signed_url_s3(key: str, *, expires_in: int = 600) -> str:
    return _s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expires_in,
    )


# ── Public API ───────────────────────────────────────────────────────
def upload_fileobj(
    fileobj: BinaryIO,
    *,
    key_prefix: str,
    filename: str,
    content_type: Optional[str] = None,
) -> tuple[str, str]:
    """Upload a file. Returns (object_key, public_url).

    The backend is selected by `settings.STORAGE_BACKEND`.
    """
    backend = (settings.STORAGE_BACKEND or "local").lower()
    if backend == "s3":
        return _upload_s3(
            fileobj,
            key_prefix=key_prefix,
            filename=filename,
            content_type=content_type,
        )
    return _upload_local(
        fileobj,
        key_prefix=key_prefix,
        filename=filename,
        content_type=content_type,
    )


def signed_url(key: str, *, expires_in: int = 600) -> str:
    """Return a download URL for a previously-uploaded key.

    For the local backend the URL never expires (it points at the static
    mount). For S3, returns a presigned URL valid for `expires_in` seconds.
    """
    backend = (settings.STORAGE_BACKEND or "local").lower()
    if backend == "s3":
        return _signed_url_s3(key, expires_in=expires_in)
    return _local_url(key)


def read_bytes(key: str) -> bytes:
    """Read back a previously-uploaded file. Raises FileNotFoundError
    when the key doesn't exist."""
    backend = (settings.STORAGE_BACKEND or "local").lower()
    if backend == "s3":
        from botocore.exceptions import ClientError

        try:
            obj = _s3_client().get_object(Bucket=settings.S3_BUCKET, Key=key)
        except ClientError as exc:
            raise FileNotFoundError(key) from exc
        return obj["Body"].read()
    root = _local_root().resolve()
    target = (root / key).resolve()
    # Keys come from our own DB rows, but never read outside the root.
    if root not in target.parents or not target.is_file():
        raise FileNotFoundError(key)
    return target.read_bytes()


def key_from_url(url: Optional[str]) -> Optional[str]:
    """Recover the object key from a URL returned by ``upload_fileobj``
    (older rows store only the URL). None when it isn't one of ours."""
    if not url:
        return None
    local_prefix = _local_url("")
    if url.startswith(local_prefix):
        return url[len(local_prefix):] or None
    s3_prefix = f"{(settings.S3_ENDPOINT or '').rstrip('/')}/{settings.S3_BUCKET}/"
    if settings.S3_ENDPOINT and url.startswith(s3_prefix):
        return url[len(s3_prefix):] or None
    return None


def delete(key: str) -> None:
    """Best-effort delete. Used by retention/cleanup jobs."""
    backend = (settings.STORAGE_BACKEND or "local").lower()
    if backend == "s3":
        try:
            _s3_client().delete_object(Bucket=settings.S3_BUCKET, Key=key)
        except Exception:
            pass
        return
    _delete_local(key)


def storage_info() -> dict:
    """Diagnostic helper for /health, etc."""
    backend = (settings.STORAGE_BACKEND or "local").lower()
    if backend == "s3":
        return {
            "backend": "s3",
            "endpoint": settings.S3_ENDPOINT,
            "bucket": settings.S3_BUCKET,
        }
    root = _local_root()
    return {
        "backend": "local",
        "path": str(root),
        "writable": os.access(root, os.W_OK),
    }
