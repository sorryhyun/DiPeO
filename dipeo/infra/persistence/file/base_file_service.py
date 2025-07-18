"""Base file service with core operations."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dipeo.core import (
    BaseService,
    FileOperationError,
    handle_file_operation,
)
from dipeo.core.ports.file_service import FileServicePort
from dipeo.domain.file.services import BackupService
from dipeo.domain.validators import FileValidator as DomainFileValidator

from .async_adapter import AsyncFileAdapter
from .file_info import FileInfo
from .handlers.registry import FormatHandlerRegistry

logger = logging.getLogger(__name__)


class BaseFileService(BaseService, FileServicePort):
    """Core file service with essential operations only."""
    
    def __init__(
        self,
        base_dir: str | Path | None = None,
        format_registry: FormatHandlerRegistry | None = None,
        async_adapter: AsyncFileAdapter | None = None,
        backup_service: BackupService | None = None,
        validator: DomainFileValidator | None = None,
    ):
        super().__init__()
        
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.formats = format_registry or FormatHandlerRegistry()
        self.async_adapter = async_adapter or AsyncFileAdapter()
        self.backup_service = backup_service or BackupService()
        self.validator = validator or DomainFileValidator()
    
    async def initialize(self) -> None:
        """Initialize the service."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"BaseFileService initialized with base_dir: {self.base_dir}")
    
    # === Core Operations ===
    
    @handle_file_operation("read")
    def read(
        self,
        file_id: str,
        person_id: str | None = None,
        directory: str | None = None,
    ) -> dict[str, Any]:
        """Read a file synchronously.
        
        Args:
            file_id: Identifier or path of the file to read
            person_id: Optional person context for file resolution
            directory: Optional directory override
            
        Returns:
            Dictionary with file content and metadata
        """
        file_path = self._resolve_path(file_id, person_id, directory)
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_id}",
                "file_id": file_id,
                "path": str(file_path),
            }
        
        # Use format registry to read
        content, raw_content = self.formats.read_file(file_path)
        
        # Determine if JSON based on handler
        is_json = file_path.suffix.lower() == '.json'
        
        return {
            "success": True,
            "file_id": file_id,
            "path": str(file_path),
            "content": content,
            "raw_content": raw_content,
            "is_json": is_json,
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(
                file_path.stat().st_mtime, tz=UTC
            ).isoformat(),
        }
    
    @handle_file_operation("write")
    async def write(
        self,
        file_id: str,
        person_id: str | None = None,
        directory: str | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        """Write content to a file asynchronously.
        
        Args:
            file_id: Identifier or path of the file to write
            person_id: Optional person context for file resolution
            directory: Optional directory override
            content: Content to write to the file
            
        Returns:
            Dictionary with write operation result
        """
        file_path = self._resolve_path(file_id, person_id, directory)
        
        # Create backup if file exists
        backup_path = await self._create_backup_if_exists(file_path)
        
        # Write using format registry
        if content is None:
            content = ""
        
        await self.formats.write_file(file_path, content)
        
        return {
            "success": True,
            "file_id": file_id,
            "path": str(file_path),
            "size": len(str(content)),
            "backup_path": str(backup_path) if backup_path else None,
            "created": datetime.now().isoformat(),
        }
    
    async def save_file(
        self, content: bytes, filename: str, target_path: str | None = None
    ) -> dict[str, Any]:
        """Save binary content to a file.
        
        Args:
            content: Binary content to save
            filename: Name of the file
            target_path: Optional target directory path
            
        Returns:
            Dictionary with saved file information
        """
        try:
            # Validate filename
            self.validator.validate_filename_strict(filename)
            
            # Determine target directory
            if target_path:
                target_dir = self.base_dir / target_path
            else:
                target_dir = self.base_dir
            
            target_dir.mkdir(parents=True, exist_ok=True)
            file_path = target_dir / filename
            
            # Create backup if exists
            backup_path = await self._create_backup_if_exists(file_path)
            
            # Write binary content
            await self.async_adapter.write_bytes_async(file_path, content)
            
            return {
                "success": True,
                "filename": filename,
                "path": str(file_path),
                "size": len(content),
                "backup_path": str(backup_path) if backup_path else None,
                "created": datetime.now().isoformat(),
            }
        
        except Exception as e:
            return {"success": False, "error": str(e), "filename": filename}
    
    # === Essential Utility Methods ===
    
    async def file_exists(self, path: str) -> bool:
        """Check if file exists.
        
        Args:
            path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        file_path = self._resolve_path(path)
        return file_path.exists() and file_path.is_file()
    
    async def get_file_size(self, path: str) -> int:
        """Get file size in bytes.
        
        Args:
            path: Path to the file
            
        Returns:
            File size in bytes
            
        Raises:
            FileOperationError: If file not found
        """
        file_path = self._resolve_path(path)
        if file_path.exists():
            return file_path.stat().st_size
        raise FileOperationError(f"File not found: {path}")
    
    async def list_files(self, directory: str | None = None) -> list[FileInfo]:
        """List files with detailed information.
        
        Args:
            directory: Directory to list files from
            
        Returns:
            List of FileInfo objects
        """
        files = []
        scan_dir = self._resolve_path(directory or "")
        
        if not scan_dir.exists():
            return files
        
        for file_path in scan_dir.rglob("*"):
            if file_path.is_file():
                try:
                    stats = file_path.stat()
                    relative_path = file_path.relative_to(self.base_dir)
                    
                    # Determine format type
                    format_type = file_path.suffix[1:].lower() if file_path.suffix else "text"
                    
                    file_info = FileInfo(
                        id=str(relative_path.with_suffix("")),
                        name=file_path.stem,
                        path=str(relative_path),
                        format=format_type,
                        extension=file_path.suffix[1:],
                        modified=datetime.fromtimestamp(
                            stats.st_mtime, tz=UTC
                        ).isoformat(),
                        size=stats.st_size,
                    )
                    
                    files.append(file_info)
                
                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")
                    continue
        
        files.sort(key=lambda x: x.modified, reverse=True)
        return files
    
    async def get_file_info(self, file_path: str) -> dict[str, Any]:
        """Get detailed file metadata.
        
        Args:
            file_path: Path to file
            
        Returns:
            File metadata dictionary
            
        Raises:
            FileOperationError: If file doesn't exist
        """
        try:
            path = self._resolve_path(file_path)
            
            if not path.exists():
                raise FileOperationError("get_file_info", file_path, "File not found")
            
            stat = path.stat()
            
            # Construct metadata
            metadata = {
                "path": str(path),
                "name": path.name,
                "extension": path.suffix.lstrip("."),
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime, tz=UTC).isoformat(),
                "is_file": path.is_file(),
                "is_directory": path.is_dir(),
                "is_symlink": path.is_symlink(),
                "exists": path.exists(),
            }
            
            return metadata
            
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError("get_file_info", file_path, str(e))
    
    # === Internal Helper Methods ===
    
    def _resolve_path(
        self,
        file_id: str,
        person_id: str | None = None,
        directory: str | None = None,
    ) -> Path:
        """Resolve the full file path.
        
        Args:
            file_id: File identifier or path
            person_id: Optional person context
            directory: Optional directory override
            
        Returns:
            Resolved Path object
        """
        # Start with base directory
        path = self.base_dir
        
        # Add directory if specified
        if directory:
            path = path / directory
        
        # Add person-specific subdirectory if specified
        if person_id:
            path = path / f"person_{person_id}"
        
        # Ensure directory exists
        path.mkdir(parents=True, exist_ok=True)
        
        # Add filename
        if not isinstance(path, Path):
            path = Path(path)
        return path / file_id
    
    async def _create_backup_if_exists(self, file_path: Path) -> Path | None:
        """Create backup of existing file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to backup file if created, None otherwise
        """
        if not file_path.exists():
            return None
        
        backup_path = self.backup_service.create_backup_name(file_path)
        
        # Copy file content
        content = await self.async_adapter.read_bytes_async(file_path)
        await self.async_adapter.write_bytes_async(backup_path, content)
        
        return backup_path