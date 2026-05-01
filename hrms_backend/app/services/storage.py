"""Object storage helpers (S3 / MinIO)."""
from __future__ import annotations

import uuid
from typing import BinaryIO, Optional

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name=settings.S3_REGION,
    )


def _ensure_bucket() -> None:
    s3 = _client()
    try:
        s3.head_bucket(Bucket=settings.S3_BUCKET)
    except ClientError:
        try:
            s3.create_bucket(Bucket=settings.S3_BUCKET)
        except ClientError:
            # Bucket may exist or another worker created it.
            pass


def upload_fileobj(
    fileobj: BinaryIO,
    *,
    key_prefix: str,
    filename: str,
    content_type: Optional[str] = None,
) -> tuple[str, str]:
    """Upload to S3/MinIO. Returns (object_key, public_url)."""
    _ensure_bucket()
    safe_name = filename.replace(" ", "_")
    key = f"{key_prefix.strip('/')}/{uuid.uuid4().hex}_{safe_name}"
    extra: dict = {}
    if content_type:
        extra["ContentType"] = content_type
    _client().upload_fileobj(fileobj, settings.S3_BUCKET, key, ExtraArgs=extra)
    # Public URL pointing at MinIO/S3 directly.
    base = settings.S3_ENDPOINT.rstrip("/")
    url = f"{base}/{settings.S3_BUCKET}/{key}"
    return key, url


def signed_url(key: str, *, expires_in: int = 600) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expires_in,
    )
