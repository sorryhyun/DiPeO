"""Modular file service using composition of focused components."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dipeo.core import (
    BaseService,
    FileOperationError, 
    SupportsFile,
    handle_file_operation,
)
from dipeo.core.base.file_protocol import FileServiceProtocol
from dipeo.core.ports.file_service import FileServicePort

from .handlers.registry import FormatHandlerRegistry
from .validation import FileValidator
from .async_adapter import AsyncFileAdapter
from .file_info import FileInfo

logger = logging.getLogger(__name__)


class ModularFileService(BaseService, SupportsFile, FileServiceProtocol, FileServicePort):
    """Modular file service that composes focused components.
    
    This service uses:
    - FormatHandlerRegistry for format-specific operations
    - FileValidator for validation logic
    - AsyncFileAdapter for async/sync bridging
    
    Implements SupportsFile, FileServiceProtocol, and FileServicePort for compatibility.
    """
    
    def __init__(
        self,
        base_dir: Optional[Union[str, Path]] = None,
        format_registry: Optional[FormatHandlerRegistry] = None,
        validator: Optional[FileValidator] = None,
        async_adapter: Optional[AsyncFileAdapter] = None,
    ):
        """Initialize with optional component overrides.
        
        Args:
            base_dir: Base directory for file operations
            format_registry: Registry for format-specific handlers
            validator: Validator for file operations
            async_adapter: Adapter for async/sync operations
        """
        super().__init__()
        
        # Base directory setup
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Component setup with defaults
        self.formats = format_registry or FormatHandlerRegistry()
        self.validator = validator or FileValidator()
        self.async_adapter = async_adapter or AsyncFileAdapter()
    
    async def initialize(self) -> None:
        """Initialize the service."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ModularFileService initialized with base_dir: {self.base_dir}")
    
    # === Basic Operations (SupportsFile Protocol) ===
    
    @handle_file_operation("read")
    def read(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
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
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
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
        self, content: bytes, filename: str, target_path: Optional[str] = None
    ) -> Dict[str, Any]:
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
            self.validator.validate_filename(filename)
            
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
    
    # === Enhanced Operations (FileServiceProtocol) ===
    
    async def read_with_validation(
        self,
        path: str,
        allowed_extensions: Optional[List[str]] = None,
        max_size_mb: float = 10.0,
        encoding: str = "utf-8",
    ) -> str:
        """Read file with validation.
        
        Args:
            path: Path to the file to read
            allowed_extensions: List of allowed file extensions
            max_size_mb: Maximum file size in MB
            encoding: Text encoding (not used, kept for compatibility)
            
        Returns:
            File content as string
            
        Raises:
            FileOperationError: If validation fails or file cannot be read
        """
        file_path = self._resolve_path(path)
        
        # Validate extension
        self.validator.validate_extension(file_path, allowed_extensions)
        
        # Check existence
        if not await self.file_exists(path):
            raise FileOperationError(f"File not found: {path}")
        
        # Validate size
        file_size = await self.get_file_size(path)
        self.validator.validate_size(file_size, max_size_mb)
        
        # Read file
        result = self.read(path)
        if not result["success"]:
            raise FileOperationError(f"Failed to read file: {result.get('error')}")
        
        return result.get("raw_content", "")
    
    async def write_with_backup(
        self,
        path: str,
        content: str,
        create_backup: bool = True,
        backup_suffix: str = ".bak",
    ) -> None:
        """Write file with optional backup.
        
        Args:
            path: Path to the file to write
            content: Content to write
            create_backup: Whether to create a backup of existing file
            backup_suffix: Suffix to append to backup filename
            
        Raises:
            FileOperationError: If file cannot be written
        """
        if create_backup and await self.file_exists(path):
            # Read existing content
            existing_result = self.read(path)
            if existing_result["success"]:
                backup_path = f"{path}{backup_suffix}"
                await self.write(backup_path, content=existing_result["raw_content"])
                logger.info(f"Created backup at {backup_path}")
        
        # Write new content
        result = await self.write(path, content=content)
        if not result["success"]:
            raise FileOperationError(f"Failed to write file: {result.get('error')}")
    
    # === Utility Methods ===
    
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
    
    async def list_files(self, directory: Optional[str] = None) -> List[FileInfo]:
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
                    handler = self.formats.get_handler(file_path)
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
    
    # === Internal Helper Methods ===
    
    def _resolve_path(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
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
        return path / file_id
    
    async def _create_backup_if_exists(self, file_path: Path) -> Optional[Path]:
        """Create backup of existing file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to backup file if created, None otherwise
        """
        if not file_path.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".{timestamp}.bak")
        
        # Copy file content
        content = await self.async_adapter.read_bytes_async(file_path)
        await self.async_adapter.write_bytes_async(backup_path, content)
        
        return backup_path