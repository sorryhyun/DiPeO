"""File validation utilities."""

import logging
from pathlib import Path
from typing import Optional

from dipeo_core import ValidationError

logger = logging.getLogger(__name__)


class FileValidator:
    """Validates files based on various criteria."""
    
    @staticmethod
    def validate_extension(
        file_path: Path,
        allowed_extensions: Optional[list[str]] = None
    ) -> None:
        """Validate file extension against allowed list."""
        if not allowed_extensions:
            return
        
        file_ext = file_path.suffix.lower()
        allowed_lower = [ext.lower() for ext in allowed_extensions]
        
        if file_ext not in allowed_lower:
            raise ValidationError(
                f"File extension '{file_ext}' not allowed. "
                f"Allowed extensions: {allowed_extensions}"
            )
    
    @staticmethod
    def validate_size(
        file_size: int,
        max_size_mb: float = 10.0
    ) -> None:
        """Validate file size against maximum."""
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise ValidationError(
                f"File too large: {file_size / 1024 / 1024:.2f}MB "
                f"(max {max_size_mb}MB)"
            )
    
    @staticmethod
    def validate_path_safety(
        file_path: str,
        base_dir: Optional[Path] = None
    ) -> None:
        """Validate path doesn't contain directory traversal attempts."""
        # Check for path traversal patterns
        if ".." in file_path or file_path.startswith("/"):
            raise ValidationError(f"Invalid file path: {file_path}")
        
        # If base_dir provided, ensure resolved path is within it
        if base_dir:
            try:
                resolved = (base_dir / file_path).resolve()
                base_resolved = base_dir.resolve()
                
                if not str(resolved).startswith(str(base_resolved)):
                    raise ValidationError(
                        f"Path '{file_path}' would escape base directory"
                    )
            except Exception as e:
                raise ValidationError(f"Invalid path: {e}")
    
    @staticmethod
    def validate_filename(filename: str) -> None:
        """Validate filename doesn't contain invalid characters."""
        # Check for path separators and other invalid characters
        invalid_chars = ['/', '\\', '..', '\0']
        
        for char in invalid_chars:
            if char in filename:
                raise ValidationError(
                    f"Invalid filename: contains '{char}'"
                )