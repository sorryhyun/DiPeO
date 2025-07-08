# Refactored file domain service - contains only business logic, no I/O.

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from dipeo.core import ValidationError

log = logging.getLogger(__name__)


class FileDomainService:
    """Domain service for file-related business logic and validation.
    
    This service contains only business logic - no I/O operations.
    All file content and metadata are passed in as parameters.
    """

    def validate_file_size(self, size_bytes: int, max_size_mb: float) -> None:
        """Validate file size against maximum allowed.
        
        Raises:
            ValidationError: If file exceeds size limit
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        if size_bytes > max_size_bytes:
            raise ValidationError(
                f"File too large: {size_bytes / 1024 / 1024:.2f}MB "
                f"(max {max_size_mb}MB)"
            )

    def validate_file_extension(
        self,
        file_path: str,
        allowed_extensions: list[str] | None
    ) -> None:
        """Validate file extension against allowed list.
        
        Raises:
            ValidationError: If extension not allowed
        """
        if not allowed_extensions:
            return
            
        file_ext = Path(file_path).suffix.lower()
        allowed_lower = [ext.lower() for ext in allowed_extensions]
        
        if file_ext not in allowed_lower:
            raise ValidationError(
                f"File extension '{file_ext}' not allowed. "
                f"Allowed extensions: {allowed_extensions}"
            )

    def create_backup_filename(self, original_path: str, suffix: str = ".bak") -> str:
        """Generate backup filename from original path.
        
        Pure string manipulation - no I/O.
        """
        from datetime import timezone
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = Path(original_path)
        extension = path.suffix
        
        # Format: original_path.backup.timestamp.extension
        # Test expects: /path/to/file.txt.backup.timestamp.txt
        return f"{original_path}.backup.{timestamp}{extension}"

    def format_log_entry(
        self,
        content: str,
        add_timestamp: bool = True,
        separator: str = "\n"
    ) -> str:
        """Format content for appending to log file.
        
        Pure transformation - no I/O.
        """
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
        """Merge new log entry with existing content.
        
        Pure string manipulation.
        """
        if existing_content and not existing_content.endswith(separator):
            existing_content += separator
            
        return existing_content + new_entry

    def parse_json_safe(self, content: str) -> dict[str, Any] | list[Any]:
        """Parse JSON content safely.
        
        Raises:
            ValidationError: If JSON is invalid
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON: {e}")
            raise ValidationError(f"Invalid JSON content: {e}")

    def format_json_pretty(
        self,
        data: dict[str, Any] | list[Any],
        indent: int = 2,
        sort_keys: bool = True
    ) -> str:
        """Format data as pretty-printed JSON.
        
        Pure transformation.
        """
        return json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)

    def filter_files_by_criteria(
        self,
        file_paths: list[str],
        extensions: list[str] | None = None,
        pattern: str | None = None
    ) -> list[str]:
        """Filter file paths by extension and pattern.
        
        Pure filtering logic - no I/O.
        """
        filtered = []
        
        for file_path in file_paths:
            path_obj = Path(file_path)
            
            # Check extension filter
            if extensions:
                if path_obj.suffix.lower() not in [ext.lower() for ext in extensions]:
                    continue
                    
            # Check pattern filter
            if pattern:
                import fnmatch
                if not fnmatch.fnmatch(path_obj.name, pattern):
                    continue
                    
            filtered.append(file_path)
            
        return sorted(filtered)

    def calculate_checksum(self, content: str | bytes) -> str:
        """Calculate MD5 checksum of content.
        
        Pure computation - no I/O.
        """
        if isinstance(content, str):
            content = content.encode("utf-8")
            
        return hashlib.md5(content).hexdigest()

    def validate_copy_operation(
        self,
        source_exists: bool,
        destination_exists: bool,
        overwrite: bool = False
    ) -> None:
        """Validate file copy operation parameters.
        
        Raises:
            ValidationError: If operation is invalid
        """
        if not source_exists:
            raise ValidationError("Source file does not exist")
            
        if destination_exists and not overwrite:
            raise ValidationError("Destination file already exists and overwrite is False")

    def validate_checksum_match(
        self,
        source_checksum: str,
        destination_checksum: str
    ) -> None:
        """Validate that checksums match.
        
        Raises:
            ValidationError: If checksums don't match
        """
        if source_checksum != destination_checksum:
            raise ValidationError(
                f"Checksum validation failed: {source_checksum} != {destination_checksum}"
            )

    def construct_file_metadata(
        self,
        path: str,
        size: int,
        modified_time: float,
        created_time: float | None = None
    ) -> dict[str, Any]:
        """Construct file metadata dictionary.
        
        Pure transformation.
        """
        path_obj = Path(path)
        
        metadata = {
            "path": path,
            "name": path_obj.name,
            "extension": path_obj.suffix.lstrip("."),
            "size_bytes": size,
            "size_mb": size / (1024 * 1024),
            "modified": datetime.fromtimestamp(modified_time).isoformat(),
        }
        
        if created_time is not None:
            metadata["created"] = datetime.fromtimestamp(created_time).isoformat()
            
        return metadata