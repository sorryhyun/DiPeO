"""Storage adapters implementing domain storage ports.

This module provides concrete implementations for:
- BlobStorePort: Object storage with versioning (S3, local filesystem)
- FileSystemPort: POSIX-like file operations (local filesystem)
- ArtifactStorePort: High-level artifact management
- DiagramStoragePort: Specialized storage for diagram files with format awareness
"""

from .s3_adapter import S3Adapter
from .local_adapter import LocalBlobAdapter, LocalFileSystemAdapter
from .artifact_adapter import ArtifactStoreAdapter
from .diagram_adapter import DiagramStorageAdapter

__all__ = [
    "S3Adapter",
    "LocalBlobAdapter",
    "LocalFileSystemAdapter",
    "ArtifactStoreAdapter",
    "DiagramStorageAdapter",
]