"""Local filesystem adapters implementing storage ports."""

import hashlib
import io
import logging
import shutil
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

import aiofiles

from dipeo.config.base_logger import get_module_logger
from dipeo.domain.base import StorageError
from dipeo.domain.base.mixins import InitializationMixin, LoggingMixin
from dipeo.domain.base.storage_port import BlobStorePort, FileInfo, FileSystemPort

logger = get_module_logger(__name__)


class LocalBlobAdapter(LoggingMixin, InitializationMixin, BlobStorePort):
    """Local filesystem implementation of BlobStorePort with versioning support."""

    def __init__(self, base_path: str | Path):
        InitializationMixin.__init__(self)
        self.base_path = Path(base_path).resolve()
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self._versions_dir = self.base_path
            self._initialized = True
        except Exception as e:
            raise StorageError(f"Failed to initialize local blob storage: {e}") from e

    def _get_object_path(self, key: str) -> Path:
        return self.base_path / key

    def _get_version_path(self, key: str, version: str) -> Path:
        return self._versions_dir / f"{key.replace('/', '_')}_{version}"

    def _compute_version(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()[:12]

    async def put(
        self, key: str, data: bytes | BinaryIO, metadata: dict[str, str] | None = None
    ) -> str:
        if not self._initialized:
            await self.initialize()

        try:
            object_path = self._get_object_path(key)
            object_path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(data, BinaryIO):
                data = data.read()

            version = self._compute_version(data)

            async with aiofiles.open(object_path, "wb") as f:
                await f.write(data)

            version_path = self._get_version_path(key, version)
            async with aiofiles.open(version_path, "wb") as f:
                await f.write(data)

            if metadata:
                meta_path = object_path.with_suffix(".meta")
                import json

                async with aiofiles.open(meta_path, "w") as f:
                    await f.write(json.dumps(metadata))

            logger.debug(f"Stored {key} with version {version}")
            return version

        except Exception as e:
            raise StorageError(f"Failed to store {key}: {e}") from e

    async def get(self, key: str, version: str | None = None) -> BinaryIO:
        if not self._initialized:
            await self.initialize()

        try:
            path = self._get_version_path(key, version) if version else self._get_object_path(key)

            if not path.exists():
                raise StorageError(f"Object not found: {key}")

            data = path.read_bytes()
            return io.BytesIO(data)

        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to retrieve {key}: {e}") from e

    async def exists(self, key: str) -> bool:
        if not self._initialized:
            await self.initialize()

        return self._get_object_path(key).exists()

    async def delete(self, key: str, version: str | None = None) -> None:
        if not self._initialized:
            await self.initialize()

        try:
            if version:
                version_path = self._get_version_path(key, version)
                if version_path.exists():
                    version_path.unlink()
            else:
                object_path = self._get_object_path(key)
                if object_path.exists():
                    object_path.unlink()

                meta_path = object_path.with_suffix(".meta")
                if meta_path.exists():
                    meta_path.unlink()

            logger.debug(f"Deleted {key}")

        except Exception as e:
            raise StorageError(f"Failed to delete {key}: {e}") from e

    async def list(self, prefix: str = "", limit: int = 1000) -> AsyncIterator[str]:
        if not self._initialized:
            await self.initialize()

        count = 0
        prefix_path = self.base_path / prefix if prefix else self.base_path

        if prefix_path.exists():
            for path in prefix_path.rglob("*"):
                if path.is_file() and not path.name.endswith(".meta"):
                    relative_path = path.relative_to(self.base_path)
                    yield str(relative_path)
                    count += 1
                    if count >= limit:
                        break

    def presign_url(self, key: str, operation: str = "GET", expires_in: int = 3600) -> str:
        if not self._initialized:
            raise StorageError("LocalBlobAdapter not initialized")

        object_path = self._get_object_path(key)
        return f"file://{object_path.absolute()}"


class LocalFileSystemAdapter(LoggingMixin, InitializationMixin, FileSystemPort):
    """Local filesystem implementation of FileSystemPort."""

    def __init__(self, base_path: str | Path | None = None):
        InitializationMixin.__init__(self)
        self.base_path = Path(base_path).resolve() if base_path else Path.cwd()
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        self.base_path.mkdir(parents=True, exist_ok=True)
        self._initialized = True

    def _resolve_path(self, path: Path) -> Path:
        return path if path.is_absolute() else self.base_path / path

    def open(self, path: Path, mode: str = "r") -> BinaryIO:
        resolved_path = self._resolve_path(path)
        try:
            if "b" not in mode:
                mode += "b"
            return open(resolved_path, mode)
        except Exception as e:
            raise StorageError(f"Failed to open {path}: {e}") from e

    def exists(self, path: Path) -> bool:
        return self._resolve_path(path).exists()

    def mkdir(self, path: Path, parents: bool = True) -> None:
        resolved_path = self._resolve_path(path)
        try:
            resolved_path.mkdir(parents=parents, exist_ok=True)
        except Exception as e:
            raise StorageError(f"Failed to create directory {path}: {e}") from e

    def listdir(self, path: Path) -> list[Path]:
        resolved_path = self._resolve_path(path)
        try:
            return list(resolved_path.iterdir())
        except Exception as e:
            raise StorageError(f"Failed to list directory {path}: {e}") from e

    def stat(self, path: Path) -> FileInfo:
        resolved_path = self._resolve_path(path)
        try:
            stats = resolved_path.stat()
            return FileInfo(
                path=resolved_path,
                size=stats.st_size,
                modified=datetime.fromtimestamp(stats.st_mtime),
                created=datetime.fromtimestamp(stats.st_ctime)
                if hasattr(stats, "st_ctime")
                else None,
            )
        except Exception as e:
            raise StorageError(f"Failed to stat {path}: {e}") from e

    def rename(self, src: Path, dst: Path) -> None:
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)
        try:
            src_path.rename(dst_path)
        except Exception as e:
            raise StorageError(f"Failed to rename {src} to {dst}: {e}") from e

    def remove(self, path: Path) -> None:
        resolved_path = self._resolve_path(path)
        try:
            resolved_path.unlink()
        except Exception as e:
            raise StorageError(f"Failed to remove {path}: {e}") from e

    def rmdir(self, path: Path, recursive: bool = False) -> None:
        resolved_path = self._resolve_path(path)
        try:
            if recursive:
                shutil.rmtree(resolved_path)
            else:
                resolved_path.rmdir()
        except Exception as e:
            raise StorageError(f"Failed to remove directory {path}: {e}") from e

    def copy(self, src: Path, dst: Path) -> None:
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)
        try:
            shutil.copy2(src_path, dst_path)
        except Exception as e:
            raise StorageError(f"Failed to copy {src} to {dst}: {e}") from e

    def size(self, path: Path) -> int:
        resolved_path = self._resolve_path(path)
        try:
            return resolved_path.stat().st_size
        except Exception as e:
            raise StorageError(f"Failed to get size of {path}: {e}") from e
