"""Local filesystem adapters implementing storage ports."""

import io
import shutil
import hashlib
import logging
from typing import AsyncIterator, BinaryIO
from pathlib import Path
from datetime import datetime
import aiofiles

from dipeo.domain.ports.storage import BlobStorePort, FileSystemPort, FileInfo
from dipeo.core import BaseService, StorageError

logger = logging.getLogger(__name__)


class LocalBlobAdapter(BaseService, BlobStorePort):
    """Local filesystem implementation of BlobStorePort with versioning support."""
    
    def __init__(self, base_path: str | Path):
        """Initialize local blob storage.
        
        Args:
            base_path: Base directory for blob storage
        """
        super().__init__()
        self.base_path = Path(base_path)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize storage directory."""
        if self._initialized:
            return
            
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self._versions_dir = self.base_path / ".versions"
            self._versions_dir.mkdir(exist_ok=True)
            self._initialized = True
            logger.info(f"LocalBlobAdapter initialized at: {self.base_path}")
        except Exception as e:
            raise StorageError(f"Failed to initialize local blob storage: {e}")
    
    def _get_object_path(self, key: str) -> Path:
        """Get path for object."""
        return self.base_path / key
    
    def _get_version_path(self, key: str, version: str) -> Path:
        """Get path for specific version."""
        return self._versions_dir / f"{key.replace('/', '_')}_{version}"
    
    def _compute_version(self, data: bytes) -> str:
        """Compute version hash from data."""
        return hashlib.sha256(data).hexdigest()[:12]
    
    async def put(self, key: str, data: bytes | BinaryIO, metadata: dict[str, str] | None = None) -> str:
        """Store object and return version ID."""
        if not self._initialized:
            await self.initialize()
            
        try:
            object_path = self._get_object_path(key)
            object_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read data if it's a file-like object
            if isinstance(data, BinaryIO):
                data = data.read()
            
            # Compute version
            version = self._compute_version(data)
            
            # Save current version
            async with aiofiles.open(object_path, "wb") as f:
                await f.write(data)
            
            # Save to version history
            version_path = self._get_version_path(key, version)
            async with aiofiles.open(version_path, "wb") as f:
                await f.write(data)
            
            # Save metadata if provided
            if metadata:
                meta_path = object_path.with_suffix(".meta")
                import json
                async with aiofiles.open(meta_path, "w") as f:
                    await f.write(json.dumps(metadata))
            
            logger.debug(f"Stored {key} with version {version}")
            return version
            
        except Exception as e:
            raise StorageError(f"Failed to store {key}: {e}")
    
    async def get(self, key: str, version: str | None = None) -> BinaryIO:
        """Retrieve object."""
        if not self._initialized:
            await self.initialize()
            
        try:
            if version:
                path = self._get_version_path(key, version)
            else:
                path = self._get_object_path(key)
            
            if not path.exists():
                raise StorageError(f"Object not found: {key}")
            
            data = path.read_bytes()
            return io.BytesIO(data)
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to retrieve {key}: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if object exists."""
        if not self._initialized:
            await self.initialize()
            
        return self._get_object_path(key).exists()
    
    async def delete(self, key: str, version: str | None = None) -> None:
        """Delete object."""
        if not self._initialized:
            await self.initialize()
            
        try:
            if version:
                # Delete specific version
                version_path = self._get_version_path(key, version)
                if version_path.exists():
                    version_path.unlink()
            else:
                # Delete current version and metadata
                object_path = self._get_object_path(key)
                if object_path.exists():
                    object_path.unlink()
                
                meta_path = object_path.with_suffix(".meta")
                if meta_path.exists():
                    meta_path.unlink()
                    
            logger.debug(f"Deleted {key}")
            
        except Exception as e:
            raise StorageError(f"Failed to delete {key}: {e}")
    
    async def list(self, prefix: str = "", limit: int = 1000) -> AsyncIterator[str]:
        """List objects with prefix."""
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
        """Generate file:// URL for local access."""
        if not self._initialized:
            raise StorageError("LocalBlobAdapter not initialized")
            
        object_path = self._get_object_path(key)
        return f"file://{object_path.absolute()}"


class LocalFileSystemAdapter(BaseService, FileSystemPort):
    """Local filesystem implementation of FileSystemPort."""
    
    def __init__(self, base_path: str | Path | None = None):
        """Initialize filesystem adapter.
        
        Args:
            base_path: Base directory (defaults to current directory)
        """
        super().__init__()
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize filesystem."""
        if self._initialized:
            return
            
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info(f"LocalFileSystemAdapter initialized at: {self.base_path}")
    
    def _resolve_path(self, path: Path) -> Path:
        """Resolve path relative to base."""
        if path.is_absolute():
            return path
        return self.base_path / path
    
    def open(self, path: Path, mode: str = "r") -> BinaryIO:
        """Open file for reading/writing."""
        resolved_path = self._resolve_path(path)
        try:
            if "b" not in mode:
                mode += "b"  # Ensure binary mode
            return open(resolved_path, mode)
        except Exception as e:
            raise StorageError(f"Failed to open {path}: {e}")
    
    def exists(self, path: Path) -> bool:
        """Check if path exists."""
        return self._resolve_path(path).exists()
    
    def mkdir(self, path: Path, parents: bool = True) -> None:
        """Create directory."""
        resolved_path = self._resolve_path(path)
        try:
            resolved_path.mkdir(parents=parents, exist_ok=True)
        except Exception as e:
            raise StorageError(f"Failed to create directory {path}: {e}")
    
    def listdir(self, path: Path) -> list[Path]:
        """List directory contents."""
        resolved_path = self._resolve_path(path)
        try:
            return list(resolved_path.iterdir())
        except Exception as e:
            raise StorageError(f"Failed to list directory {path}: {e}")
    
    def stat(self, path: Path) -> FileInfo:
        """Get file metadata."""
        resolved_path = self._resolve_path(path)
        try:
            stats = resolved_path.stat()
            return FileInfo(
                path=resolved_path,
                size=stats.st_size,
                modified=datetime.fromtimestamp(stats.st_mtime),
                created=datetime.fromtimestamp(stats.st_ctime) if hasattr(stats, 'st_ctime') else None
            )
        except Exception as e:
            raise StorageError(f"Failed to stat {path}: {e}")
    
    def rename(self, src: Path, dst: Path) -> None:
        """Rename/move file."""
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)
        try:
            src_path.rename(dst_path)
        except Exception as e:
            raise StorageError(f"Failed to rename {src} to {dst}: {e}")
    
    def remove(self, path: Path) -> None:
        """Delete file."""
        resolved_path = self._resolve_path(path)
        try:
            resolved_path.unlink()
        except Exception as e:
            raise StorageError(f"Failed to remove {path}: {e}")
    
    def rmdir(self, path: Path, recursive: bool = False) -> None:
        """Remove directory."""
        resolved_path = self._resolve_path(path)
        try:
            if recursive:
                shutil.rmtree(resolved_path)
            else:
                resolved_path.rmdir()
        except Exception as e:
            raise StorageError(f"Failed to remove directory {path}: {e}")
    
    def copy(self, src: Path, dst: Path) -> None:
        """Copy file."""
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)
        try:
            shutil.copy2(src_path, dst_path)
        except Exception as e:
            raise StorageError(f"Failed to copy {src} to {dst}: {e}")
    
    def size(self, path: Path) -> int:
        """Get file size in bytes."""
        resolved_path = self._resolve_path(path)
        try:
            return resolved_path.stat().st_size
        except Exception as e:
            raise StorageError(f"Failed to get size of {path}: {e}")