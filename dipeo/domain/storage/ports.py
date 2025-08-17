"""Storage port definitions for DiPeO domain layer.

These protocols define the boundaries between domain logic and infrastructure,
allowing the domain to remain independent of specific storage implementations.
"""

from typing import Protocol, AsyncIterator, BinaryIO, runtime_checkable
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileInfo:
    """Metadata about a file."""
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
    """Reference to a stored artifact."""
    name: str
    version: str
    uri: str
    size: int
    created: datetime
    metadata: dict[str, str]


@runtime_checkable
class BlobStorePort(Protocol):
    """Object storage with streaming and versioning."""
    
    async def put(self, key: str, data: bytes | BinaryIO, metadata: dict[str, str] | None = None) -> str:
        """Store object and return version ID."""
        ...
    
    async def get(self, key: str, version: str | None = None) -> BinaryIO:
        """Retrieve object by key and optional version."""
        ...
    
    async def exists(self, key: str) -> bool:
        """Check if object exists."""
        ...
    
    async def delete(self, key: str, version: str | None = None) -> None:
        """Delete object."""
        ...
    
    async def list(self, prefix: str = "", limit: int = 1000) -> AsyncIterator[str]:
        """List objects with prefix."""
        ...
    
    def presign_url(self, key: str, operation: str = "GET", expires_in: int = 3600) -> str:
        """Generate presigned URL for direct access."""
        ...


@runtime_checkable
class FileSystemPort(Protocol):
    """POSIX-like file operations."""
    
    def open(self, path: Path, mode: str = "r") -> BinaryIO:
        """Open file for reading/writing."""
        ...
    
    def exists(self, path: Path) -> bool:
        """Check if path exists."""
        ...
    
    def mkdir(self, path: Path, parents: bool = True) -> None:
        """Create directory."""
        ...
    
    def listdir(self, path: Path) -> list[Path]:
        """List directory contents."""
        ...
    
    def stat(self, path: Path) -> FileInfo:
        """Get file metadata."""
        ...
    
    def rename(self, src: Path, dst: Path) -> None:
        """Rename/move file."""
        ...
    
    def remove(self, path: Path) -> None:
        """Delete file."""
        ...
    
    def rmdir(self, path: Path, recursive: bool = False) -> None:
        """Remove directory."""
        ...
    
    def copy(self, src: Path, dst: Path) -> None:
        """Copy file."""
        ...
    
    def size(self, path: Path) -> int:
        """Get file size in bytes."""
        ...


@runtime_checkable  
class ArtifactStorePort(Protocol):
    """High-level artifact management."""
    
    async def push(self, artifact: Artifact) -> ArtifactRef:
        """Store versioned artifact."""
        ...
    
    async def pull(self, ref: ArtifactRef) -> Path:
        """Retrieve artifact to local path."""
        ...
    
    async def list_versions(self, name: str) -> list[ArtifactRef]:
        """List all versions of an artifact."""
        ...
    
    async def promote(self, ref: ArtifactRef, stage: str) -> None:
        """Promote artifact to stage (dev/staging/prod)."""
        ...
    
    async def tag(self, ref: ArtifactRef, tags: list[str]) -> None:
        """Add tags to artifact."""
        ...
    
    async def find_by_tag(self, tag: str) -> list[ArtifactRef]:
        """Find artifacts by tag."""
        ...
    
    async def get_latest(self, name: str, stage: str | None = None) -> ArtifactRef | None:
        """Get latest version of an artifact."""
        ...


@dataclass
class DiagramInfo:
    """Metadata about a diagram file."""
    id: str
    path: Path
    format: str
    size: int
    modified: datetime
    created: datetime | None = None
    metadata: dict[str, str] | None = None