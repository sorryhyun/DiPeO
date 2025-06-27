"""File operations domain service with validation and error handling."""

import logging
import os
from pathlib import Path
from typing import Any

from dipeo_core import FileOperationError, SupportsFile, ValidationError

log = logging.getLogger(__name__)


class FileOperationsDomainService:
    """File operations with validation and error handling."""

    def __init__(self, file_service: SupportsFile):
        self._file = file_service

    async def read_with_validation(
        self,
        path: str,
        allowed_extensions: list[str] | None = None,
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
            ValidationError: If file fails validation
            FileOperationError: If file operation fails
        """
        # Validate file extension
        if allowed_extensions:
            file_ext = Path(path).suffix.lower()
            if file_ext not in [ext.lower() for ext in allowed_extensions]:
                raise ValidationError(
                    f"File extension '{file_ext}' not allowed. "
                    f"Allowed extensions: {allowed_extensions}"
                )

        # Check if file exists
        if not await self._file_exists(path):
            raise FileOperationError(f"File not found: {path}")

        # Check file size
        try:
            file_size = await self._get_file_size(path)
            max_size_bytes = max_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                raise ValidationError(
                    f"File too large: {file_size / 1024 / 1024:.2f}MB "
                    f"(max {max_size_mb}MB)"
                )
        except Exception as e:
            log.warning(f"Could not check file size: {e}")

        # Read file
        try:
            content = await self._file.aread(path)
            return content
        except Exception as e:
            raise FileOperationError(f"Failed to read file: {e}")

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
                existing_content = await self._file.aread(path)
                backup_path = f"{path}{backup_suffix}"
                await self._file.write(backup_path, existing_content)
                log.info(f"Created backup at {backup_path}")
            except Exception as e:
                log.warning(f"Failed to create backup: {e}")

        # Write new content
        try:
            await self._file.write(path, content)
        except Exception as e:
            raise FileOperationError(f"Failed to write file: {e}")

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
        from datetime import datetime

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
                existing = await self._file.aread(path)
            except Exception:
                pass

        # Append with separator
        if existing and not existing.endswith(separator):
            existing += separator

        new_content = existing + entry + separator

        try:
            await self._file.write(path, new_content)
        except Exception as e:
            raise FileOperationError(f"Failed to append to file: {e}")

    async def read_json_safe(
        self,
        path: str,
        default: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Safely read JSON file with error handling.

        Args:
            path: JSON file path
            default: Default value if file doesn't exist or is invalid

        Returns:
            Parsed JSON data or default value
        """
        import json

        try:
            content = await self.read_with_validation(
                path,
                allowed_extensions=[".json"],
                max_size_mb=50.0,
            )
            return json.loads(content)
        except (FileOperationError, ValidationError):
            if default is not None:
                return default
            raise
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON in {path}: {e}")
            if default is not None:
                return default
            raise ValidationError(f"Invalid JSON file: {e}")

    async def write_json_pretty(
        self,
        path: str,
        data: dict[str, Any] | list[Any],
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
        import json

        try:
            content = json.dumps(data, indent=indent, sort_keys=sort_keys)
            await self.write_with_backup(path, content, create_backup=True)
        except Exception as e:
            raise FileOperationError(f"Failed to write JSON file: {e}")

    async def list_files_filtered(
        self,
        directory: str,
        extensions: list[str] | None = None,
        pattern: str | None = None,
        recursive: bool = False,
    ) -> list[str]:
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
            # Use built-in list if available
            if hasattr(self._file, "list"):
                all_files = await self._file.list(directory)
            else:
                # Fallback to os.listdir
                all_files = []
                for entry in os.listdir(directory):
                    entry_path = os.path.join(directory, entry)
                    if os.path.isfile(entry_path):
                        all_files.append(entry_path)

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
                    import fnmatch

                    if not fnmatch.fnmatch(path_obj.name, pattern):
                        continue

                filtered.append(file_path)

            return sorted(filtered)

        except Exception as e:
            raise FileOperationError(f"Failed to list files: {e}")

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
            raise FileOperationError(f"Source file not found: {source}")

        # Check destination
        if not overwrite and await self._file_exists(destination):
            raise FileOperationError(f"Destination file already exists: {destination}")

        try:
            # Read source
            content = await self._file.aread(source)

            # Write to destination
            await self._file.write(destination, content)

            # Validate if requested
            if validate_checksum:
                source_checksum = await self._calculate_checksum(source)
                dest_checksum = await self._calculate_checksum(destination)
                if source_checksum != dest_checksum:
                    raise FileOperationError(
                        "Copy validation failed: checksums don't match"
                    )

        except Exception as e:
            raise FileOperationError(f"Failed to copy file: {e}")

    async def _file_exists(self, path: str) -> bool:
        """Check if file exists."""
        try:
            if hasattr(self._file, "exists"):
                return await self._file.exists(path)
            # Try to read the file
            await self._file.aread(path)
            return True
        except Exception:
            return False

    async def _get_file_size(self, path: str) -> int:
        """Get file size in bytes."""
        try:
            # If file service has size method
            if hasattr(self._file, "size"):
                return await self._file.size(path)
            # Read file and get length (not efficient for large files)
            content = await self._file.aread(path)
            return len(content.encode("utf-8"))
        except Exception as e:
            raise FileOperationError(f"Failed to get file size: {e}")

    async def _calculate_checksum(self, path: str) -> str:
        """Calculate file checksum."""
        import hashlib

        try:
            content = await self._file.aread(path)
            return hashlib.md5(content.encode("utf-8")).hexdigest()
        except Exception as e:
            raise FileOperationError(f"Failed to calculate checksum: {e}")
