"""Storage port definitions for DiPeO domain layer.

These protocols define the boundaries between domain logic and infrastructure,
allowing the domain to remain independent of specific storage implementations.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Protocol, runtime_checkable


@dataclass
class FileInfo:
    path: Path
    size: int
    modified: datetime
    created: datetime | None = None
    mime_type: str | None = None


@dataclass
class Artifact:
    """Versioned artifact with metadata."""

    name: str
    version: str
    data: bytes | BinaryIO
    metadata: dict[str, str]
    tags: list[str] | None = None


@dataclass
class ArtifactRef:
    name: str
    version: str
    uri: str
    size: int
    created: datetime
    metadata: dict[str, str]


@runtime_checkable
class BlobStorePort(Protocol):
    """Object storage with streaming and versioning."""

    async def put(
        self, key: str, data: bytes | BinaryIO, metadata: dict[str, str] | None = None
    ) -> str: ...

    async def get(self, key: str, version: str | None = None) -> BinaryIO: ...

    async def exists(self, key: str) -> bool: ...

    async def delete(self, key: str, version: str | None = None) -> None: ...

    async def list(self, prefix: str = "", limit: int = 1000) -> AsyncIterator[str]: ...

    def presign_url(self, key: str, operation: str = "GET", expires_in: int = 3600) -> str: ...


@runtime_checkable
class FileSystemPort(Protocol):
    """POSIX-like file operations."""

    def open(self, path: Path, mode: str = "r") -> BinaryIO: ...

    def exists(self, path: Path) -> bool: ...

    def mkdir(self, path: Path, parents: bool = True) -> None: ...

    def listdir(self, path: Path) -> list[Path]: ...

    def stat(self, path: Path) -> FileInfo: ...

    def rename(self, src: Path, dst: Path) -> None: ...

    def remove(self, path: Path) -> None: ...

    def rmdir(self, path: Path, recursive: bool = False) -> None: ...

    def copy(self, src: Path, dst: Path) -> None: ...

    def size(self, path: Path) -> int: ...


@runtime_checkable
class ArtifactStorePort(Protocol):
    async def push(self, artifact: Artifact) -> ArtifactRef: ...

    async def pull(self, ref: ArtifactRef) -> Path: ...

    async def list_versions(self, name: str) -> list[ArtifactRef]: ...

    async def promote(self, ref: ArtifactRef, stage: str) -> None: ...

    async def tag(self, ref: ArtifactRef, tags: list[str]) -> None: ...

    async def find_by_tag(self, tag: str) -> list[ArtifactRef]: ...

    async def get_latest(self, name: str, stage: str | None = None) -> ArtifactRef | None: ...


@dataclass
class DiagramInfo:
    id: str
    path: Path
    format: str
    size: int
    modified: datetime
    created: datetime | None = None
    metadata: dict[str, str] | None = None
