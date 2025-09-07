"""Storage adapters implementing domain storage ports.

This module provides concrete implementations for:
- BlobStorePort: Object storage with versioning (S3, local filesystem)
- FileSystemPort: POSIX-like file operations (local filesystem)
- ArtifactStorePort: High-level artifact management
"""

from .artifact_adapter import ArtifactStoreAdapter
from .local_adapter import LocalBlobAdapter, LocalFileSystemAdapter
from .s3_adapter import S3Adapter

__all__ = [
    "ArtifactStoreAdapter",
    "LocalBlobAdapter",
    "LocalFileSystemAdapter",
    "S3Adapter",
]
