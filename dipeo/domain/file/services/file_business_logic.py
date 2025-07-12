"""File business logic - pure functions for file operations."""

import fnmatch
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

from dipeo.core import ValidationError
from dipeo.domain.file.value_objects import (
    Checksum,
    ChecksumAlgorithm,
    FileExtension,
    FileSize,
)

log = logging.getLogger(__name__)


class FileBusinessLogic:
    """Pure business logic for file operations and validation."""

    def validate_file_size(self, size_bytes: int, max_size_mb: float) -> None:
        """Validate file size against maximum allowed."""
        size = FileSize(size_bytes)
        max_size = FileSize(int(max_size_mb * 1024 * 1024))
        
        if not size.is_within_limit(max_size.bytes):
            raise ValidationError(
                f"File too large: {size.human_readable()} "
                f"(max {max_size.human_readable()})"
            )

    def validate_file_extension(
        self,
        file_path: str,
        allowed_extensions: Optional[list[str]] = None
    ) -> None:
        """Validate file extension against allowed list."""
        if not allowed_extensions:
            return
        
        extension = FileExtension(Path(file_path).suffix)
        
        # Ensure all allowed extensions have dots
        normalized_allowed = {
            ext if ext.startswith('.') else f'.{ext}'
            for ext in allowed_extensions
        }
        
        if not extension.is_allowed(normalized_allowed):
            raise ValidationError(
                f"File extension '{extension}' not allowed. "
                f"Allowed extensions: {sorted(normalized_allowed)}"
            )

    def create_backup_filename(self, original_path: str, suffix: str = ".bak") -> str:
        """Generate backup filename from original path."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = Path(original_path)
        extension = FileExtension(path.suffix) if path.suffix else None
        
        # Format: original_path.backup.timestamp.extension
        if extension:
            return f"{original_path}.backup.{timestamp}{extension}"
        else:
            return f"{original_path}.backup.{timestamp}"

    def format_log_entry(
        self,
        content: str,
        add_timestamp: bool = True,
        separator: str = "\n"
    ) -> str:
        """Format content for appending to log file."""
        if add_timestamp:
            timestamp = datetime.utcnow().isoformat()
            entry = f"[{timestamp}] {content}"
        else:
            entry = content
            
        return entry + separator

    def merge_log_content(
        self,
        existing_content: str,
        new_entry: str,
        separator: str = "\n"
    ) -> str:
        """Merge new log entry with existing content."""
        if existing_content and not existing_content.endswith(separator):
            existing_content += separator
            
        return existing_content + new_entry

    def parse_json_safe(self, content: str) -> Union[dict[str, Any], list[Any]]:
        """Parse JSON content safely."""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON: {e}")
            raise ValidationError(f"Invalid JSON content: {e}")

    def format_json_pretty(
        self,
        data: Union[dict[str, Any], list[Any]],
        indent: int = 2,
        sort_keys: bool = True
    ) -> str:
        """Format data as pretty-printed JSON."""
        return json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)

    def filter_files_by_criteria(
        self,
        file_paths: list[str],
        extensions: Optional[list[str]] = None,
        pattern: Optional[str] = None
    ) -> list[str]:
        """Filter file paths by extension and pattern."""
        filtered = []
        
        for file_path in file_paths:
            path_obj = Path(file_path)
            
            # Check extension filter
            if extensions:
                file_ext = FileExtension(path_obj.suffix) if path_obj.suffix else None
                normalized_extensions = {
                    ext if ext.startswith('.') else f'.{ext}'
                    for ext in extensions
                }
                if not file_ext or not file_ext.is_allowed(normalized_extensions):
                    continue
                    
            # Check pattern filter
            if pattern:
                if not fnmatch.fnmatch(path_obj.name, pattern):
                    continue
                    
            filtered.append(file_path)
            
        return sorted(filtered)

    def calculate_checksum(
        self,
        content: Union[str, bytes],
        algorithm: ChecksumAlgorithm = ChecksumAlgorithm.MD5
    ) -> str:
        """Calculate checksum of content."""
        checksum = Checksum.compute(content, algorithm)
        return checksum.value

    def calculate_file_checksum(
        self,
        file_path: str,
        algorithm: ChecksumAlgorithm = ChecksumAlgorithm.MD5
    ) -> Checksum:
        """Calculate checksum for a file."""
        return Checksum.compute_file(file_path, algorithm)

    def validate_copy_operation(
        self,
        source_exists: bool,
        destination_exists: bool,
        overwrite: bool = False
    ) -> None:
        """Validate file copy operation parameters."""
        if not source_exists:
            raise ValidationError("Source file does not exist")
            
        if destination_exists and not overwrite:
            raise ValidationError("Destination file already exists and overwrite is False")

    def validate_checksum_match(
        self,
        source_checksum: str,
        destination_checksum: str,
        algorithm: ChecksumAlgorithm = ChecksumAlgorithm.MD5
    ) -> None:
        """Validate that checksums match."""
        source = Checksum(source_checksum, algorithm)
        destination = Checksum(destination_checksum, algorithm)
        
        if source.value.lower() != destination.value.lower():
            raise ValidationError(
                f"Checksum validation failed: {source.short_value} != {destination.short_value}"
            )

    def construct_file_metadata(
        self,
        path: str,
        size: int,
        modified_time: float,
        created_time: Optional[float] = None
    ) -> dict[str, Any]:
        """Construct file metadata dictionary."""
        path_obj = Path(path)
        file_size = FileSize(size)
        extension = FileExtension(path_obj.suffix) if path_obj.suffix else None
        
        metadata = {
            "path": path,
            "name": path_obj.name,
            "extension": extension.without_dot if extension else "",
            "size_bytes": file_size.bytes,
            "size_mb": file_size.megabytes,
            "size_human": file_size.human_readable(),
            "modified": datetime.fromtimestamp(modified_time).isoformat(),
        }
        
        if created_time is not None:
            metadata["created"] = datetime.fromtimestamp(created_time).isoformat()
            
        return metadata

    def is_text_file(self, file_path: str) -> bool:
        """Check if file is likely a text file based on extension."""
        path_obj = Path(file_path)
        if not path_obj.suffix:
            return False
            
        extension = FileExtension(path_obj.suffix)
        return extension.is_text_format

    def get_file_size_category(self, size_bytes: int) -> str:
        """Categorize file size."""
        size = FileSize(size_bytes)
        
        if size.bytes == 0:
            return "empty"
        elif size.kilobytes < 10:
            return "tiny"
        elif size.megabytes < 1:
            return "small"
        elif size.megabytes < 10:
            return "medium"
        elif size.megabytes < 100:
            return "large"
        else:
            return "very_large"