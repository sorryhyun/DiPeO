"""Modular file service using composition of focused components."""

import logging
from pathlib import Path
from typing import Any

from dipeo.core import FileOperationError
from dipeo.core.ports.file_service import FileServicePort
from dipeo.domain.file.services import BackupService
from dipeo.domain.validators import FileValidator as DomainFileValidator

from .async_adapter import AsyncFileAdapter
from .base_file_service import BaseFileService
from .file_info import FileInfo
from .file_operations_service import FileOperationsService
from .handlers.registry import FormatHandlerRegistry
from .json_file_service import JsonFileService
from .prompt_file_service import PromptFileService

logger = logging.getLogger(__name__)


class ModularFileService(FileServicePort):
    """Facade that combines specialized file services."""
    
    def __init__(
        self,
        base_dir: str | Path | None = None,
        format_registry: FormatHandlerRegistry | None = None,
        async_adapter: AsyncFileAdapter | None = None,
        backup_service: BackupService | None = None,
        validator: DomainFileValidator | None = None,
    ):
        # Initialize base service
        self.base = BaseFileService(
            base_dir=base_dir,
            format_registry=format_registry,
            async_adapter=async_adapter,
            backup_service=backup_service,
            validator=validator,
        )
        
        # Initialize specialized services
        self.json = JsonFileService(self.base)
        self.prompts = PromptFileService(self.base, base_dir=self.base.base_dir)
        self.operations = FileOperationsService(self.base, self.base.async_adapter)
        
        # Expose commonly used properties for compatibility
        self.base_dir = self.base.base_dir
        self.formats = self.base.formats
        self.async_adapter = self.base.async_adapter
        self.backup_service = self.base.backup_service
        self.validator = self.base.validator
    
    async def initialize(self) -> None:
        """Initialize the service."""
        await self.base.initialize()
    
    # === Delegate Core Operations to Base Service ===
    
    def read(
        self,
        file_id: str,
        person_id: str | None = None,
        directory: str | None = None,
    ) -> dict[str, Any]:
        """Read a file synchronously."""
        return self.base.read(file_id, person_id, directory)
    
    async def write(
        self,
        file_id: str,
        person_id: str | None = None,
        directory: str | None = None,
        content: str | None = None,
        create_backup: bool = True,
    ) -> dict[str, Any]:
        """Write content to a file asynchronously."""
        return await self.base.write(file_id, person_id, directory, content, create_backup)
    
    async def save_file(
        self, content: bytes, filename: str, target_path: str | None = None,
        create_backup: bool = True
    ) -> dict[str, Any]:
        """Save binary content to a file."""
        return await self.base.save_file(content, filename, target_path, create_backup)
    
    async def file_exists(self, path: str) -> bool:
        """Check if file exists."""
        return await self.base.file_exists(path)
    
    async def get_file_size(self, path: str) -> int:
        """Get file size in bytes."""
        return await self.base.get_file_size(path)
    
    async def list_files(self, directory: str | None = None) -> list[FileInfo]:
        """List files with detailed information."""
        return await self.base.list_files(directory)
    
    async def get_file_info(self, file_path: str) -> dict[str, Any]:
        """Get detailed file metadata."""
        return await self.base.get_file_info(file_path)
    
    # === Enhanced Operations (with validation) ===
    
    async def read_with_validation(
        self,
        path: str,
        allowed_extensions: list[str] | None = None,
        max_size_mb: float = 10.0,
        encoding: str = "utf-8",
    ) -> str:
        """Read file with validation."""
        file_path = self.base._resolve_path(path)
        
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
        """Write file with optional backup."""
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
    
    # === Delegate JSON Operations ===
    
    async def read_json(
        self,
        file_path: str,
        encoding: str = "utf-8",
    ) -> dict[str, Any] | list[Any]:
        """Read and parse JSON file."""
        return await self.json.read_json(file_path, encoding)
    
    async def write_json(
        self,
        file_path: str,
        data: dict[str, Any] | list[Any],
        indent: int = 2,
        sort_keys: bool = True,
        encoding: str = "utf-8",
        create_backup: bool = False,
    ) -> None:
        """Write data as JSON to file."""
        await self.json.write_json(
            file_path, data, indent, sort_keys, encoding, create_backup
        )
    
    # === Delegate Prompt Operations ===
    
    async def list_prompt_files(self) -> list[dict[str, Any]]:
        """List all prompt files in the prompts directory."""
        return await self.prompts.list_prompt_files()
    
    async def read_prompt_file(self, filename: str) -> dict[str, Any]:
        """Read a prompt file from the prompts directory."""
        return await self.prompts.read_prompt_file(filename)
    
    # === Delegate Advanced Operations ===
    
    async def append_to_file(
        self,
        file_path: str,
        content: str,
        add_timestamp: bool = True,
        separator: str = "\n",
        encoding: str = "utf-8",
    ) -> None:
        """Append content to file with optional timestamp."""
        await self.operations.append_to_file(
            file_path, content, add_timestamp, separator, encoding
        )
    
    async def copy_file(
        self,
        source_path: str,
        destination_path: str,
        overwrite: bool = False,
        verify_checksum: bool = True,
    ) -> None:
        """Copy file from source to destination with optional checksum verification."""
        await self.operations.copy_file(
            source_path, destination_path, overwrite, verify_checksum
        )
    
    async def delete_file(
        self,
        file_path: str,
        create_backup: bool = False,
    ) -> None:
        """Delete file with optional backup."""
        await self.operations.delete_file(file_path, create_backup)
    
    # === Internal Helper Methods (for compatibility) ===
    
    def _resolve_path(
        self,
        file_id: str,
        person_id: str | None = None,
        directory: str | None = None,
    ) -> Path:
        """Resolve the full file path."""
        return self.base._resolve_path(file_id, person_id, directory)
    
    async def _create_backup_if_exists(self, file_path: Path) -> Path | None:
        """Create backup of existing file."""
        return await self.base._create_backup_if_exists(file_path)