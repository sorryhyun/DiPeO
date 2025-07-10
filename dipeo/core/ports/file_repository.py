# Infrastructure implementation for file I/O operations.

import logging
import os
from pathlib import Path
from typing import Any

from dipeo.core import FileOperationError
from dipeo.core.ports import FileServicePort
from dipeo.domain.services.file.file_domain_service import FileDomainService

log = logging.getLogger(__name__)


class FileRepository(FileServicePort):
    """Infrastructure service for file I/O operations.
    
    This service handles all file system interactions.
    Business logic is delegated to FileDomainService.
    """

    def __init__(self, domain_service: FileDomainService):
        self.domain_service = domain_service

    async def aread(self, path: str, encoding: str = "utf-8") -> str:
        """Read file content asynchronously.
        
        Pure I/O operation.
        """
        try:
            # Could use aiofiles here for true async
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            raise FileOperationError(f"File not found: {path}")
        except Exception as e:
            raise FileOperationError(f"Failed to read file: {e}")

    async def write(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """Write content to file asynchronously.
        
        Pure I/O operation.
        """
        try:
            # Ensure directory exists
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w", encoding=encoding) as f:
                f.write(content)
        except Exception as e:
            raise FileOperationError(f"Failed to write file: {e}")

    async def exists(self, path: str) -> bool:
        """Check if file exists.
        
        Pure I/O operation.
        """
        return Path(path).exists()

    async def size(self, path: str) -> int:
        """Get file size in bytes.
        
        Pure I/O operation.
        """
        try:
            return Path(path).stat().st_size
        except Exception as e:
            raise FileOperationError(f"Failed to get file size: {e}")

    async def list(self, directory: str, recursive: bool = False) -> list[str]:
        """List files in directory.
        
        Pure I/O operation.
        """
        try:
            path = Path(directory)
            if not path.exists():
                return []
                
            if recursive:
                return [str(p) for p in path.rglob("*") if p.is_file()]
            else:
                return [str(p) for p in path.iterdir() if p.is_file()]
        except Exception as e:
            raise FileOperationError(f"Failed to list directory: {e}")

    async def delete(self, path: str) -> None:
        """Delete file.
        
        Pure I/O operation.
        """
        try:
            Path(path).unlink()
        except FileNotFoundError:
            raise FileOperationError(f"File not found: {path}")
        except Exception as e:
            raise FileOperationError(f"Failed to delete file: {e}")

    async def get_metadata(self, path: str) -> dict[str, Any]:
        """Get file metadata.
        
        I/O operation to read file stats.
        """
        try:
            path_obj = Path(path)
            stats = path_obj.stat()
            
            # Use domain service to construct metadata
            return self.domain_service.construct_file_metadata(
                path=path,
                size=stats.st_size,
                modified_time=stats.st_mtime,
                created_time=getattr(stats, 'st_birthtime', None) or stats.st_ctime
            )
        except Exception as e:
            raise FileOperationError(f"Failed to get file metadata: {e}")


class FileOperationsService:
    """Higher-level file operations service that combines repository and domain logic."""

    def __init__(self, repository: FileRepository, domain_service: FileDomainService):
        self.repository = repository
        self.domain_service = domain_service

    async def read_with_validation(
        self,
        path: str,
        allowed_extensions: list[str] | None = None,
        max_size_mb: float = 10.0,
        encoding: str = "utf-8",
    ) -> str:
        """Read file with validation."""
        # Validate extension
        self.domain_service.validate_file_extension(path, allowed_extensions)
        
        # Check file exists
        if not await self.repository.exists(path):
            raise FileOperationError(f"File not found: {path}")
            
        # Check file size
        file_size = await self.repository.size(path)
        self.domain_service.validate_file_size(file_size, max_size_mb)
        
        # Read content
        return await self.repository.aread(path, encoding)

    async def write_with_backup(
        self,
        path: str,
        content: str,
        create_backup: bool = True,
        backup_suffix: str = ".bak",
    ) -> None:
        """Write file with optional backup."""
        # Create backup if requested and file exists
        if create_backup and await self.repository.exists(path):
            try:
                existing_content = await self.repository.aread(path)
                backup_path = self.domain_service.create_backup_filename(path, backup_suffix)
                await self.repository.write(backup_path, existing_content)
                log.info(f"Created backup at {backup_path}")
            except Exception as e:
                log.warning(f"Failed to create backup: {e}")
                
        # Write new content
        await self.repository.write(path, content)

    async def append_with_timestamp(
        self,
        path: str,
        content: str,
        separator: str = "\n",
        add_timestamp: bool = True,
    ) -> None:
        """Append content to file with optional timestamp."""
        # Format new entry
        new_entry = self.domain_service.format_log_entry(content, add_timestamp, separator)
        
        # Read existing content if file exists
        existing = ""
        if await self.repository.exists(path):
            try:
                existing = await self.repository.aread(path)
            except Exception:
                pass
                
        # Merge content
        merged_content = self.domain_service.merge_log_content(existing, new_entry, separator)
        
        # Write merged content
        await self.repository.write(path, merged_content)

    async def read_json_safe(
        self,
        path: str,
        default: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Safely read and parse JSON file."""
        try:
            content = await self.read_with_validation(
                path,
                allowed_extensions=[".json"],
                max_size_mb=50.0,
            )
            return self.domain_service.parse_json_safe(content)
        except (FileOperationError, ValidationError):
            if default is not None:
                return default
            raise

    async def write_json_pretty(
        self,
        path: str,
        data: dict[str, Any] | list[Any],
        indent: int = 2,
        sort_keys: bool = True,
    ) -> None:
        """Write JSON file with pretty formatting."""
        content = self.domain_service.format_json_pretty(data, indent, sort_keys)
        await self.write_with_backup(path, content, create_backup=True)

    async def list_files_filtered(
        self,
        directory: str,
        extensions: list[str] | None = None,
        pattern: str | None = None,
        recursive: bool = False,
    ) -> list[str]:
        """List files with filtering."""
        # Get all files from repository
        all_files = await self.repository.list(directory, recursive)
        
        # Apply filters using domain service
        return self.domain_service.filter_files_by_criteria(all_files, extensions, pattern)

    async def copy_with_validation(
        self,
        source: str,
        destination: str,
        overwrite: bool = False,
        validate_checksum: bool = False,
    ) -> None:
        """Copy file with validation."""
        # Validate operation
        source_exists = await self.repository.exists(source)
        dest_exists = await self.repository.exists(destination)
        self.domain_service.validate_copy_operation(source_exists, dest_exists, overwrite)
        
        # Read source content
        content = await self.repository.aread(source)
        
        # Write to destination
        await self.repository.write(destination, content)
        
        # Validate checksum if requested
        if validate_checksum:
            source_checksum = self.domain_service.calculate_checksum(content)
            dest_content = await self.repository.aread(destination)
            dest_checksum = self.domain_service.calculate_checksum(dest_content)
            self.domain_service.validate_checksum_match(source_checksum, dest_checksum)