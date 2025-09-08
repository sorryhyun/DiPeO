"""S3 adapter implementing BlobStorePort."""

import io
import logging
from collections.abc import AsyncIterator
from typing import BinaryIO

from dipeo.domain.base import StorageError
from dipeo.domain.base.mixins import InitializationMixin, LoggingMixin
from dipeo.domain.base.storage_port import BlobStorePort

logger = logging.getLogger(__name__)


class S3Adapter(LoggingMixin, InitializationMixin, BlobStorePort):
    """AWS S3 implementation of BlobStorePort."""

    def __init__(self, bucket: str, client=None, region: str = "us-east-1"):
        # Initialize mixins
        InitializationMixin.__init__(self)
        self.bucket = bucket
        self.region = region
        self._client = client
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        if not self._client:
            try:
                import boto3

                self._client = boto3.client("s3", region_name=self.region)
            except ImportError as e:
                raise StorageError(
                    "boto3 is required for S3 adapter. Install with: pip install boto3"
                ) from e

        try:
            self._client.head_bucket(Bucket=self.bucket)
        except Exception as e:
            raise StorageError(f"Cannot access bucket {self.bucket}: {e}") from e

        self._initialized = True
        logger.info(f"S3Adapter initialized with bucket: {self.bucket}")

    async def put(
        self, key: str, data: bytes | BinaryIO, metadata: dict[str, str] | None = None
    ) -> str:
        if not self._initialized:
            await self.initialize()

        try:
            extra_args = {"Metadata": metadata or {}}

            if isinstance(data, bytes):
                response = self._client.put_object(
                    Bucket=self.bucket, Key=key, Body=data, **extra_args
                )
            else:
                self._client.upload_fileobj(data, self.bucket, key, ExtraArgs=extra_args)
                response = self._client.head_object(Bucket=self.bucket, Key=key)

            version_id = response.get("VersionId", "")
            logger.debug(f"Stored {key} in S3 bucket {self.bucket}, version: {version_id}")
            return version_id

        except Exception as e:
            raise StorageError(f"Failed to store {key} in S3: {e}") from e

    async def get(self, key: str, version: str | None = None) -> BinaryIO:
        if not self._initialized:
            await self.initialize()

        try:
            params = {"Bucket": self.bucket, "Key": key}
            if version:
                params["VersionId"] = version

            response = self._client.get_object(**params)

            return io.BytesIO(response["Body"].read())

        except self._client.exceptions.NoSuchKey as e:
            raise StorageError(f"Object not found: {key}") from e
        except Exception as e:
            raise StorageError(f"Failed to retrieve {key} from S3: {e}") from e

    async def exists(self, key: str) -> bool:
        if not self._initialized:
            await self.initialize()

        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except self._client.exceptions.NoSuchKey:
            return False
        except Exception as e:
            logger.warning(f"Error checking existence of {key}: {e}")
            return False

    async def delete(self, key: str, version: str | None = None) -> None:
        if not self._initialized:
            await self.initialize()

        try:
            params = {"Bucket": self.bucket, "Key": key}
            if version:
                params["VersionId"] = version

            self._client.delete_object(**params)
            logger.debug(f"Deleted {key} from S3 bucket {self.bucket}")

        except Exception as e:
            raise StorageError(f"Failed to delete {key} from S3: {e}") from e

    async def list(self, prefix: str = "", limit: int = 1000) -> AsyncIterator[str]:
        if not self._initialized:
            await self.initialize()

        try:
            paginator = self._client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=self.bucket, Prefix=prefix, PaginationConfig={"MaxItems": limit}
            )

            for page in page_iterator:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        yield obj["Key"]

        except Exception as e:
            raise StorageError(f"Failed to list objects with prefix {prefix}: {e}") from e

    def presign_url(self, key: str, operation: str = "GET", expires_in: int = 3600) -> str:
        if not self._initialized:
            raise StorageError("S3Adapter not initialized")

        try:
            client_method_map = {
                "GET": "get_object",
                "PUT": "put_object",
                "DELETE": "delete_object",
                "HEAD": "head_object",
            }

            client_method = client_method_map.get(operation.upper())
            if not client_method:
                raise ValueError(f"Unsupported operation: {operation}")

            url = self._client.generate_presigned_url(
                ClientMethod=client_method,
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )

            return url

        except Exception as e:
            raise StorageError(f"Failed to generate presigned URL for {key}: {e}") from e
