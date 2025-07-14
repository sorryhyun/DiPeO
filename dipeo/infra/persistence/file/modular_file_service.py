"""Modular file service using composition of focused components."""

import hashlib
import json
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
from dipeo.domain.file.services import FileValidator as DomainFileValidator

from .async_adapter import AsyncFileAdapter
from .file_info import FileInfo
from .handlers.registry import FormatHandlerRegistry

logger = logging.getLogger(__name__)


class ModularFileService(BaseService, FileServicePort):
    
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
        logger.info(f"ModularFileService initialized with base_dir: {self.base_dir}")
    
    # === Basic Operations (SupportsFile Protocol) ===
    
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
    
    # === Enhanced Operations ===
    
    async def read_with_validation(
        self,
        path: str,
        allowed_extensions: list[str] | None = None,
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
    
    # === Additional Operations from FileOperationsService ===
    
    async def append_to_file(
        self,
        file_path: str,
        content: str,
        add_timestamp: bool = True,
        separator: str = "\n",
        encoding: str = "utf-8",
    ) -> None:
        """Append content to file with optional timestamp.
        
        Args:
            file_path: Target file path
            content: Content to append
            add_timestamp: Whether to add timestamp to entry
            separator: Line separator
            encoding: File encoding
            
        Raises:
            FileOperationError: On append failures
        """
        try:
            path = self._resolve_path(file_path)
            
            # Format entry with timestamp if requested
            if add_timestamp:
                timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
                entry = f"[{timestamp}] {content}"
            else:
                entry = content
            
            # Add separator
            if not entry.endswith(separator):
                entry += separator
            
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Append to file
            await self.async_adapter.append_text_async(path, entry, encoding)
            
        except Exception as e:
            raise FileOperationError("append", file_path, str(e))
    
    async def copy_file(
        self,
        source_path: str,
        destination_path: str,
        overwrite: bool = False,
        verify_checksum: bool = True,
    ) -> None:
        """Copy file from source to destination with optional checksum verification.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            overwrite: Whether to overwrite existing file
            verify_checksum: Whether to verify copy integrity
            
        Raises:
            FileOperationError: On copy failures
        """
        try:
            src_path = self._resolve_path(source_path)
            dst_path = self._resolve_path(destination_path)
            
            # Validate source exists
            if not src_path.exists():
                raise FileOperationError("copy", source_path, "Source file not found")
            
            # Check destination
            if dst_path.exists() and not overwrite:
                raise FileOperationError(
                    "copy", destination_path, "Destination file already exists and overwrite is False"
                )
            
            # Ensure destination directory exists
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            await self.async_adapter.copy_file_async(src_path, dst_path)
            
            # Verify checksum if requested
            if verify_checksum:
                src_content = await self.async_adapter.read_bytes_async(src_path)
                dst_content = await self.async_adapter.read_bytes_async(dst_path)
                
                src_checksum = hashlib.md5(src_content).hexdigest()
                dst_checksum = hashlib.md5(dst_content).hexdigest()
                
                if src_checksum != dst_checksum:
                    raise FileOperationError(
                        "copy", f"{source_path} -> {destination_path}", 
                        f"Checksum validation failed: {src_checksum} != {dst_checksum}"
                    )
            
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError("copy", f"{source_path} -> {destination_path}", str(e))
    
    async def delete_file(
        self,
        file_path: str,
        create_backup: bool = False,
    ) -> None:
        """Delete file with optional backup.
        
        Args:
            file_path: File to delete
            create_backup: Whether to create backup before deletion
            
        Raises:
            FileOperationError: On deletion failures
        """
        try:
            path = self._resolve_path(file_path)
            
            if not path.exists():
                raise FileOperationError("delete", file_path, "File not found")
            
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_path = await self._create_backup_if_exists(path)
                if backup_path:
                    logger.info(f"Created backup before deletion: {backup_path}")
            
            # Delete file
            await self.async_adapter.delete_file_async(path)
            
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError("delete", file_path, str(e))
    
    async def read_json(
        self,
        file_path: str,
        encoding: str = "utf-8",
    ) -> dict[str, Any] | list[Any]:
        """Read and parse JSON file.
        
        Args:
            file_path: Path to JSON file
            encoding: File encoding
            
        Returns:
            Parsed JSON data
            
        Raises:
            FileOperationError: On read or parse failures
        """
        try:
            result = self.read(file_path)
            if not result["success"]:
                raise FileOperationError("read_json", file_path, result.get('error', 'Unknown error'))
            
            # Parse JSON
            try:
                return json.loads(result["raw_content"])
            except json.JSONDecodeError as e:
                raise FileOperationError("read_json", file_path, f"Invalid JSON content: {e}")
            
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError("read_json", file_path, str(e))
    
    async def write_json(
        self,
        file_path: str,
        data: dict[str, Any] | list[Any],
        indent: int = 2,
        sort_keys: bool = True,
        encoding: str = "utf-8",
        create_backup: bool = False,
    ) -> None:
        """Write data as JSON to file.
        
        Args:
            file_path: Target file path
            data: Data to write
            indent: JSON indentation
            sort_keys: Whether to sort keys
            encoding: File encoding
            create_backup: Whether to create backup
            
        Raises:
            FileOperationError: On write failures
        """
        try:
            # Format JSON
            content = json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
            
            # Write to file
            result = await self.write(
                file_id=file_path,
                content=content,
            )
            
            if not result["success"]:
                raise FileOperationError("write_json", file_path, result.get('error', 'Unknown error'))
            
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError("write_json", file_path, str(e))
    
    async def get_file_info(
        self,
        file_path: str,
    ) -> dict[str, Any]:
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
        # Ensure path is a Path object
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