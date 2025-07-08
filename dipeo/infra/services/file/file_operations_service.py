"""Infrastructure service for file operations.

This service handles file I/O operations and delegates business logic to FileDomainService.
It follows the hexagonal architecture pattern where infrastructure depends on domain.
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Any

import aiofiles
from dipeo.core import ServiceError, ValidationError
from dipeo.domain.services.file.file_domain_service import FileDomainService

log = logging.getLogger(__name__)


class FileOperationsService:
    """Infrastructure service that handles file operations.
    
    This service combines:
    - Actual file I/O operations (reading, writing, copying, etc.)
    - FileDomainService for business logic and validation
    
    It implements the adapter pattern, providing concrete file system operations
    while using domain logic for validation and transformations.
    """

    def __init__(self, domain_service: FileDomainService):
        """Initialize file operations service.
        
        Args:
            domain_service: Domain service for business logic
        """
        self.domain_service = domain_service

    async def read_file(
        self,
        file_path: str,
        encoding: str = "utf-8"
    ) -> str:
        """Read file content.
        
        Args:
            file_path: Path to file
            encoding: File encoding
            
        Returns:
            File content as string
            
        Raises:
            ServiceError: On read failures
        """
        try:
            async with aiofiles.open(file_path, mode="r", encoding=encoding) as f:
                return await f.read()
        except FileNotFoundError:
            raise ServiceError(f"File not found: {file_path}")
        except Exception as e:
            raise ServiceError(f"Failed to read file {file_path}: {e}")

    async def write_file(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
        create_backup: bool = False
    ) -> None:
        """Write content to file.
        
        Args:
            file_path: Target file path
            content: Content to write
            encoding: File encoding
            create_backup: Whether to create backup of existing file
            
        Raises:
            ServiceError: On write failures
        """
        try:
            # Create backup if requested and file exists
            if create_backup and os.path.exists(file_path):
                backup_path = self.domain_service.create_backup_filename(file_path)
                shutil.copy2(file_path, backup_path)
                log.info(f"Created backup: {backup_path}")
                
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            async with aiofiles.open(file_path, mode="w", encoding=encoding) as f:
                await f.write(content)
                
        except Exception as e:
            raise ServiceError(f"Failed to write file {file_path}: {e}")

    async def append_to_file(
        self,
        file_path: str,
        content: str,
        add_timestamp: bool = True,
        separator: str = "\n",
        encoding: str = "utf-8"
    ) -> None:
        """Append content to file (useful for logs).
        
        Args:
            file_path: Target file path
            content: Content to append
            add_timestamp: Whether to add timestamp to entry
            separator: Line separator
            encoding: File encoding
            
        Raises:
            ServiceError: On append failures
        """
        try:
            # Format entry using domain service
            entry = self.domain_service.format_log_entry(
                content=content,
                add_timestamp=add_timestamp,
                separator=separator
            )
            
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Append to file
            async with aiofiles.open(file_path, mode="a", encoding=encoding) as f:
                await f.write(entry)
                
        except Exception as e:
            raise ServiceError(f"Failed to append to file {file_path}: {e}")

    async def copy_file(
        self,
        source_path: str,
        destination_path: str,
        overwrite: bool = False,
        verify_checksum: bool = True
    ) -> None:
        """Copy file from source to destination.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            overwrite: Whether to overwrite existing file
            verify_checksum: Whether to verify copy integrity
            
        Raises:
            ServiceError: On copy failures
        """
        try:
            # Validate operation using domain service
            self.domain_service.validate_copy_operation(
                source_exists=os.path.exists(source_path),
                destination_exists=os.path.exists(destination_path),
                overwrite=overwrite
            )
            
            # Ensure destination directory exists
            Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            await asyncio.to_thread(shutil.copy2, source_path, destination_path)
            
            # Verify checksum if requested
            if verify_checksum:
                source_content = await self.read_file(source_path)
                dest_content = await self.read_file(destination_path)
                
                source_checksum = self.domain_service.calculate_checksum(source_content)
                dest_checksum = self.domain_service.calculate_checksum(dest_content)
                
                self.domain_service.validate_checksum_match(
                    source_checksum=source_checksum,
                    destination_checksum=dest_checksum
                )
                
        except Exception as e:
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(f"Failed to copy file from {source_path} to {destination_path}: {e}")

    async def delete_file(
        self,
        file_path: str,
        create_backup: bool = False
    ) -> None:
        """Delete file.
        
        Args:
            file_path: File to delete
            create_backup: Whether to create backup before deletion
            
        Raises:
            ServiceError: On deletion failures
        """
        try:
            if not os.path.exists(file_path):
                raise ServiceError(f"File not found: {file_path}")
                
            # Create backup if requested
            if create_backup:
                backup_path = self.domain_service.create_backup_filename(file_path)
                shutil.copy2(file_path, backup_path)
                log.info(f"Created backup before deletion: {backup_path}")
                
            # Delete file
            await asyncio.to_thread(os.remove, file_path)
            
        except Exception as e:
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(f"Failed to delete file {file_path}: {e}")

    async def list_files(
        self,
        directory: str,
        extensions: list[str] | None = None,
        pattern: str | None = None,
        recursive: bool = False
    ) -> list[str]:
        """List files in directory with optional filtering.
        
        Args:
            directory: Directory to list
            extensions: Filter by file extensions
            pattern: Filter by filename pattern
            recursive: Whether to search recursively
            
        Returns:
            List of file paths
            
        Raises:
            ServiceError: On listing failures
        """
        try:
            if not os.path.exists(directory):
                raise ServiceError(f"Directory not found: {directory}")
                
            # Get all files
            file_paths = []
            
            if recursive:
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_paths.append(os.path.join(root, file))
            else:
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    if os.path.isfile(item_path):
                        file_paths.append(item_path)
                        
            # Filter using domain service
            return self.domain_service.filter_files_by_criteria(
                file_paths=file_paths,
                extensions=extensions,
                pattern=pattern
            )
            
        except Exception as e:
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(f"Failed to list files in {directory}: {e}")

    async def read_json(
        self,
        file_path: str,
        encoding: str = "utf-8"
    ) -> dict[str, Any] | list[Any]:
        """Read and parse JSON file.
        
        Args:
            file_path: Path to JSON file
            encoding: File encoding
            
        Returns:
            Parsed JSON data
            
        Raises:
            ServiceError: On read or parse failures
        """
        content = await self.read_file(file_path, encoding)
        return self.domain_service.parse_json_safe(content)

    async def write_json(
        self,
        file_path: str,
        data: dict[str, Any] | list[Any],
        indent: int = 2,
        sort_keys: bool = True,
        encoding: str = "utf-8",
        create_backup: bool = False
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
            ServiceError: On write failures
        """
        # Format JSON using domain service
        content = self.domain_service.format_json_pretty(
            data=data,
            indent=indent,
            sort_keys=sort_keys
        )
        
        # Write to file
        await self.write_file(
            file_path=file_path,
            content=content,
            encoding=encoding,
            create_backup=create_backup
        )

    async def get_file_info(
        self,
        file_path: str
    ) -> dict[str, Any]:
        """Get file metadata.
        
        Args:
            file_path: Path to file
            
        Returns:
            File metadata dictionary
            
        Raises:
            ServiceError: If file doesn't exist
        """
        try:
            if not os.path.exists(file_path):
                raise ServiceError(f"File not found: {file_path}")
                
            stat = os.stat(file_path)
            
            # Construct metadata using domain service
            return self.domain_service.construct_file_metadata(
                path=file_path,
                size=stat.st_size,
                modified_time=stat.st_mtime,
                created_time=getattr(stat, "st_birthtime", None)  # Not available on all systems
            )
            
        except Exception as e:
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(f"Failed to get file info for {file_path}: {e}")

    async def validate_file(
        self,
        file_path: str,
        max_size_mb: float | None = None,
        allowed_extensions: list[str] | None = None
    ) -> None:
        """Validate file against criteria.
        
        Args:
            file_path: File to validate
            max_size_mb: Maximum file size in MB
            allowed_extensions: Allowed file extensions
            
        Raises:
            ValidationError: If validation fails
            ServiceError: If file doesn't exist
        """
        try:
            if not os.path.exists(file_path):
                raise ServiceError(f"File not found: {file_path}")
                
            # Validate extension
            self.domain_service.validate_file_extension(
                file_path=file_path,
                allowed_extensions=allowed_extensions
            )
            
            # Validate size
            if max_size_mb is not None:
                size_bytes = os.path.getsize(file_path)
                self.domain_service.validate_file_size(
                    size_bytes=size_bytes,
                    max_size_mb=max_size_mb
                )
                
        except Exception as e:
            if isinstance(e, (ServiceError, ValidationError)):
                raise
            raise ServiceError(f"Failed to validate file {file_path}: {e}")