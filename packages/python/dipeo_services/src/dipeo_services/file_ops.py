"""File operations service with validation and error handling."""

import hashlib
import json
import logging
import os
import fnmatch
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .file import SimpleFileService


logger = logging.getLogger(__name__)


class SimpleFileOperationsService:
    """File operations with validation and error handling."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize with a base file service."""
        self._file = SimpleFileService(base_dir)
        self.base_dir = self._file.base_dir

    async def read_with_validation(
        self,
        path: str,
        allowed_extensions: Optional[List[str]] = None,
        max_size_mb: float = 10.0,
        encoding: str = "utf-8",
    ) -> str:
        """Read file with validation and error handling.

        Args:
            path: File path to read
            allowed_extensions: List of allowed file extensions (e.g., ['.txt', '.json'])
            max_size_mb: Maximum file size in megabytes
            encoding: File encoding

        Returns:
            File content as string

        Raises:
            ValueError: If file fails validation
            IOError: If file operation fails
        """
        # Validate file extension
        if allowed_extensions:
            file_ext = Path(path).suffix.lower()
            if file_ext not in [ext.lower() for ext in allowed_extensions]:
                raise ValueError(
                    f"File extension '{file_ext}' not allowed. "
                    f"Allowed extensions: {allowed_extensions}"
                )

        # Check if file exists
        if not await self._file_exists(path):
            raise IOError(f"File not found: {path}")

        # Check file size
        try:
            file_size = await self._get_file_size(path)
            max_size_bytes = max_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                raise ValueError(
                    f"File too large: {file_size / 1024 / 1024:.2f}MB "
                    f"(max {max_size_mb}MB)"
                )
        except Exception as e:
            logger.warning(f"Could not check file size: {e}")

        # Read file
        result = self._file.read(path)
        if not result["success"]:
            raise IOError(f"Failed to read file: {result.get('error')}")
        
        return result.get("raw_content", "")

    async def write_with_backup(
        self,
        path: str,
        content: str,
        create_backup: bool = True,
        backup_suffix: str = ".bak",
    ) -> None:
        """Write file with optional backup of existing file.

        Args:
            path: File path to write
            content: Content to write
            create_backup: Whether to create backup of existing file
            backup_suffix: Suffix for backup file
        """
        # Create backup if file exists
        if create_backup and await self._file_exists(path):
            try:
                existing_result = self._file.read(path)
                if existing_result["success"]:
                    backup_path = f"{path}{backup_suffix}"
                    await self._file.write(backup_path, content=existing_result["raw_content"])
                    logger.info(f"Created backup at {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")

        # Write new content
        result = await self._file.write(path, content=content)
        if not result["success"]:
            raise IOError(f"Failed to write file: {result.get('error')}")

    async def append_with_timestamp(
        self,
        path: str,
        content: str,
        separator: str = "\n",
        add_timestamp: bool = True,
    ) -> None:
        """Append content to file with optional timestamp.

        Args:
            path: File path to append to
            content: Content to append
            separator: Separator between entries
            add_timestamp: Whether to add timestamp to entry
        """
        # Prepare content with timestamp
        if add_timestamp:
            timestamp = datetime.utcnow().isoformat()
            entry = f"[{timestamp}] {content}"
        else:
            entry = content

        # Read existing content if file exists
        existing = ""
        if await self._file_exists(path):
            try:
                result = self._file.read(path)
                if result["success"]:
                    existing = result.get("raw_content", "")
            except Exception:
                pass

        # Append with separator
        if existing and not existing.endswith(separator):
            existing += separator

        new_content = existing + entry + separator

        result = await self._file.write(path, content=new_content)
        if not result["success"]:
            raise IOError(f"Failed to append to file: {result.get('error')}")

    async def read_json_safe(
        self,
        path: str,
        default: Optional[Union[Dict[str, Any], List[Any]]] = None,
    ) -> Union[Dict[str, Any], List[Any]]:
        """Safely read JSON file with error handling.

        Args:
            path: JSON file path
            default: Default value if file doesn't exist or is invalid

        Returns:
            Parsed JSON data or default value
        """
        try:
            content = await self.read_with_validation(
                path,
                allowed_extensions=[".json"],
                max_size_mb=50.0,
            )
            return json.loads(content)
        except (IOError, ValueError):
            if default is not None:
                return default
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {path}: {e}")
            if default is not None:
                return default
            raise ValueError(f"Invalid JSON file: {e}")

    async def write_json_pretty(
        self,
        path: str,
        data: Union[Dict[str, Any], List[Any]],
        indent: int = 2,
        sort_keys: bool = True,
    ) -> None:
        """Write JSON file with pretty formatting.

        Args:
            path: JSON file path
            data: Data to write
            indent: Indentation level
            sort_keys: Whether to sort dictionary keys
        """
        try:
            content = json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
            await self.write_with_backup(path, content, create_backup=True)
        except Exception as e:
            raise IOError(f"Failed to write JSON file: {e}")

    async def list_files_filtered(
        self,
        directory: str,
        extensions: Optional[List[str]] = None,
        pattern: Optional[str] = None,
        recursive: bool = False,
    ) -> List[str]:
        """List files in directory with filtering.

        Args:
            directory: Directory path
            extensions: Filter by file extensions
            pattern: Filter by filename pattern (glob-style)
            recursive: Whether to search recursively

        Returns:
            List of file paths matching filters
        """
        try:
            # Resolve full directory path
            full_dir = self.base_dir / directory if not os.path.isabs(directory) else Path(directory)
            
            if not full_dir.exists():
                return []
            
            # Get all files
            if recursive:
                all_files = [str(p) for p in full_dir.rglob("*") if p.is_file()]
            else:
                all_files = [str(p) for p in full_dir.iterdir() if p.is_file()]

            # Apply filters
            filtered = []
            for file_path in all_files:
                path_obj = Path(file_path)

                # Check extension
                if extensions:
                    if path_obj.suffix.lower() not in [
                        ext.lower() for ext in extensions
                    ]:
                        continue

                # Check pattern
                if pattern:
                    if not fnmatch.fnmatch(path_obj.name, pattern):
                        continue

                filtered.append(file_path)

            return sorted(filtered)

        except Exception as e:
            raise IOError(f"Failed to list files: {e}")

    async def copy_with_validation(
        self,
        source: str,
        destination: str,
        overwrite: bool = False,
        validate_checksum: bool = False,
    ) -> None:
        """Copy file with validation.

        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing file
            validate_checksum: Whether to validate checksum after copy
        """
        # Check source exists
        if not await self._file_exists(source):
            raise IOError(f"Source file not found: {source}")

        # Check destination
        if not overwrite and await self._file_exists(destination):
            raise IOError(f"Destination file already exists: {destination}")

        try:
            # Read source
            result = self._file.read(source)
            if not result["success"]:
                raise IOError(f"Failed to read source: {result.get('error')}")
            
            content = result.get("raw_content", "")

            # Write to destination
            write_result = await self._file.write(destination, content=content)
            if not write_result["success"]:
                raise IOError(f"Failed to write destination: {write_result.get('error')}")

            # Validate if requested
            if validate_checksum:
                source_checksum = await self._calculate_checksum(source)
                dest_checksum = await self._calculate_checksum(destination)
                if source_checksum != dest_checksum:
                    raise IOError(
                        "Copy validation failed: checksums don't match"
                    )

        except Exception as e:
            if isinstance(e, IOError):
                raise
            raise IOError(f"Failed to copy file: {e}")

    async def _file_exists(self, path: str) -> bool:
        """Check if file exists."""
        result = self._file.read(path)
        return result["success"]

    async def _get_file_size(self, path: str) -> int:
        """Get file size in bytes."""
        result = self._file.read(path)
        if result["success"]:
            return result.get("size", 0)
        raise IOError(f"Failed to get file size: {result.get('error')}")

    async def _calculate_checksum(self, path: str) -> str:
        """Calculate file checksum."""
        try:
            result = self._file.read(path)
            if not result["success"]:
                raise IOError(f"Failed to read file: {result.get('error')}")
            
            content = result.get("raw_content", "")
            return hashlib.md5(content.encode("utf-8")).hexdigest()
        except Exception as e:
            raise IOError(f"Failed to calculate checksum: {e}")