from __future__ import annotations

import base64
import mimetypes
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ImageAsset:
    image_id: str
    data: bytes
    mime_type: str

    @property
    def inline_data(self) -> str:
        return base64.b64encode(self.data).decode("ascii")


class ImageStorage(Protocol):
    def download(self, image_id: str) -> ImageAsset | None: ...


class HttpImageStorage:
    """Downloads image IDs from a configured storage HTTP endpoint."""

    def __init__(self, base_url: str, timeout_seconds: float = 10.0, max_bytes: int = 5_000_000):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes

    def download(self, image_id: str) -> ImageAsset | None:
        url = f"{self.base_url}/{urllib.parse.quote(image_id, safe='')}"
        request = urllib.request.Request(url, headers={"Accept": "image/*"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                content_type = response.headers.get_content_type()
                if not content_type.startswith("image/"):
                    return None
                data = response.read(self.max_bytes + 1)
                if len(data) > self.max_bytes:
                    return None
                return ImageAsset(image_id=image_id, data=data, mime_type=content_type)
        except (OSError, ValueError):
            return None


class FilebaseImageStorage:
    """Downloads complaint image objects from Filebase's S3-compatible API."""

    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        region: str,
        signature_version: str,
        bucket: str,
        max_bytes: int = 5_000_000,
    ):
        import boto3
        from botocore.client import Config

        self.bucket = bucket
        self.max_bytes = max_bytes
        normalized_signature = signature_version.lower()
        if normalized_signature == "v4":
            normalized_signature = "s3v4"
        elif not normalized_signature.startswith("s3"):
            normalized_signature = f"s3{normalized_signature}"
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
            config=Config(signature_version=normalized_signature),
        )

    def download(self, image_id: str) -> ImageAsset | None:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=image_id)
            body = response["Body"]
            data = body.read(self.max_bytes + 1)
            body.close()
            if len(data) > self.max_bytes:
                return None
            mime_type = response.get("ContentType") or mimetypes.guess_type(image_id)[0] or "image/jpeg"
            if not mime_type.startswith("image/"):
                return None
            return ImageAsset(image_id=image_id, data=data, mime_type=mime_type)
        except Exception as exc:
            from botocore.exceptions import BotoCoreError, ClientError

            if isinstance(exc, (BotoCoreError, ClientError, OSError, ValueError)):
                return None
            raise

    def upload(self, image_id: str, data: bytes, mime_type: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=image_id,
            Body=data,
            ContentType=mime_type,
        )


class NoopImageStorage:
    def download(self, image_id: str) -> ImageAsset | None:
        return None
