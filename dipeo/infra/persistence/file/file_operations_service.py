"""Advanced file operations service."""

import hashlib
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dipeo.core import FileOperationError, handle_file_operation

logger = logging.getLogger(__name__)


class FileOperationsService:
    """Service for advanced file operations (copy, append, delete, etc.)."""
    
    def __init__(self, file_service, async_adapter):
        """Initialize with dependencies.
        
        Args:
            file_service: Core file service for basic operations
            async_adapter: Async file adapter for low-level operations
        """
        self.file_service = file_service
        self.async_adapter = async_adapter
    
    @handle_file_operation("append")
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
            path = self.file_service._resolve_path(file_path)
            
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
    
    @handle_file_operation("copy")
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
            src_path = self.file_service._resolve_path(source_path)
            dst_path = self.file_service._resolve_path(destination_path)
            
            # Validate source exists
            if not src_path.exists():
                raise FileOperationError("copy", source_path, "Source file not found")
            
            # Check destination
            if dst_path.exists() and not overwrite:
                raise FileOperationError(
                    "copy", destination_path, 
                    "Destination file already exists and overwrite is False"
                )
            
            # Ensure destination directory exists
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            await self.async_adapter.copy_file_async(src_path, dst_path)
            
            # Verify checksum if requested
            if verify_checksum:
                await self._verify_file_checksum(src_path, dst_path)
            
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError("copy", f"{source_path} -> {destination_path}", str(e))
    
    @handle_file_operation("delete")
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
            path = self.file_service._resolve_path(file_path)
            
            if not path.exists():
                raise FileOperationError("delete", file_path, "File not found")
            
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_path = await self.file_service._create_backup_if_exists(path)
                if backup_path:
                    logger.info(f"Created backup before deletion: {backup_path}")
            
            # Delete file
            await self.async_adapter.delete_file_async(path)
            
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError("delete", file_path, str(e))
    
    @handle_file_operation("move")
    async def move_file(
        self,
        source_path: str,
        destination_path: str,
        overwrite: bool = False,
    ) -> None:
        """Move file from source to destination.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            overwrite: Whether to overwrite existing file
            
        Raises:
            FileOperationError: On move failures
        """
        try:
            # Copy file first
            await self.copy_file(source_path, destination_path, overwrite)
            
            # Then delete original
            await self.delete_file(source_path, create_backup=False)
            
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError("move", f"{source_path} -> {destination_path}", str(e))
    
    async def batch_copy(
        self,
        file_mappings: dict[str, str],
        overwrite: bool = False,
        continue_on_error: bool = False,
    ) -> dict[str, Any]:
        """Copy multiple files in batch.
        
        Args:
            file_mappings: Dictionary mapping source to destination paths
            overwrite: Whether to overwrite existing files
            continue_on_error: Whether to continue on individual failures
            
        Returns:
            Dictionary with results for each file
        """
        results = {}
        
        for source, destination in file_mappings.items():
            try:
                await self.copy_file(source, destination, overwrite)
                results[source] = {"success": True, "destination": destination}
            except Exception as e:
                results[source] = {"success": False, "error": str(e)}
                if not continue_on_error:
                    break
        
        return results
    
    async def _verify_file_checksum(self, src_path: Path, dst_path: Path) -> None:
        """Verify file checksums match.
        
        Args:
            src_path: Source file path
            dst_path: Destination file path
            
        Raises:
            FileOperationError: If checksums don't match
        """
        src_content = await self.async_adapter.read_bytes_async(src_path)
        dst_content = await self.async_adapter.read_bytes_async(dst_path)
        
        src_checksum = hashlib.md5(src_content).hexdigest()
        dst_checksum = hashlib.md5(dst_content).hexdigest()
        
        if src_checksum != dst_checksum:
            raise FileOperationError(
                "copy", f"{src_path} -> {dst_path}", 
                f"Checksum validation failed: {src_checksum} != {dst_checksum}"
            )