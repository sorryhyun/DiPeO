"""File validation service using unified validation framework."""

from pathlib import Path
from typing import Any

from dipeo.domain.base.exceptions import ValidationError
from dipeo.domain.validators.base_validator import BaseValidator, ValidationResult, ValidationWarning


class FileValidator(BaseValidator):
    """Validates files using the unified validation framework."""
    
    def __init__(self, 
                 allowed_extensions: list[str] | None = None,
                 max_size_mb: float = 10.0,
                 min_size_bytes: int = 0):
        """Initialize file validator with constraints.
        
        Args:
            allowed_extensions: List of allowed extensions (e.g., ['.txt', '.json'])
            max_size_mb: Maximum allowed file size in megabytes
            min_size_bytes: Minimum allowed file size in bytes
        """
        self.allowed_extensions = allowed_extensions
        self.max_size_mb = max_size_mb
        self.min_size_bytes = min_size_bytes
    
    # Convenience methods for backward compatibility
    def validate_extension(self, file_path: Path, allowed_extensions: list[str] | None = None) -> None:
        """Validate file extension (raises exception).
        
        Args:
            file_path: Path to validate
            allowed_extensions: Override allowed extensions
            
        Raises:
            ValidationError: If extension not allowed
        """
        extensions = allowed_extensions or self.allowed_extensions
        if not extensions:
            return
        
        file_ext = file_path.suffix.lower()
        allowed_lower = [ext.lower() for ext in extensions]
        
        if file_ext not in allowed_lower:
            raise ValidationError(
                f"File extension '{file_ext}' not allowed. "
                f"Allowed extensions: {extensions}"
            )
    
    def validate_size(self, file_size: int, max_size_mb: float | None = None) -> None:
        """Validate file size (raises exception).
        
        Args:
            file_size: Size in bytes
            max_size_mb: Override max size
            
        Raises:
            ValidationError: If size exceeds limit
        """
        max_mb = max_size_mb if max_size_mb is not None else self.max_size_mb
        max_bytes = max_mb * 1024 * 1024
        
        if file_size > max_bytes:
            raise ValidationError(
                f"File too large: {file_size / 1024 / 1024:.2f}MB "
                f"(max {max_mb}MB)"
            )
    
    def validate_filename_strict(self, filename: str) -> None:
        """Validate filename strictly (raises exception).
        
        Args:
            filename: Filename to validate
            
        Raises:
            ValidationError: If filename is invalid
        """
        # Use PathValidator to validate filename
        path_validator = PathValidator()
        result = path_validator.validate_filename(filename, strict=True)
        if result.errors:
            raise result.errors[0]
    
    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        """Perform file validation."""
        if isinstance(target, Path):
            self._validate_file_path(target, result)
        elif isinstance(target, str):
            self._validate_file_path(Path(target), result)
        elif isinstance(target, dict):
            # Validate file metadata
            self._validate_file_metadata(target, result)
        else:
            result.add_error(ValidationError("Target must be a Path, string path, or file metadata dict"))
    
    def _validate_file_path(self, file_path: Path, result: ValidationResult) -> None:
        """Validate a file path."""
        # Check if file exists
        if not file_path.exists():
            result.add_warning(ValidationWarning(f"File does not exist: {file_path}"))
            # Still validate the path structure
        
        # Validate extension
        if self.allowed_extensions:
            file_ext = file_path.suffix.lower()
            allowed_lower = [ext.lower() for ext in self.allowed_extensions]
            
            if file_ext not in allowed_lower:
                result.add_error(ValidationError(
                    f"File extension '{file_ext}' not allowed",
                    details={
                        "allowed_extensions": self.allowed_extensions,
                        "file": str(file_path)
                    }
                ))
        
        # Validate file name
        if not file_path.name:
            result.add_error(ValidationError("File must have a name"))
        
        # Check for potentially problematic characters
        problematic_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        for char in problematic_chars:
            if char in str(file_path):
                result.add_warning(ValidationWarning(
                    f"File path contains problematic character: '{char}'",
                    field_name="path"
                ))
        
        # If file exists, validate size
        if file_path.exists() and file_path.is_file():
            file_size = file_path.stat().st_size
            self._validate_file_size(file_size, str(file_path), result)
    
    def _validate_file_metadata(self, metadata: dict, result: ValidationResult) -> None:
        """Validate file metadata dictionary."""
        # Validate path if present
        if 'path' in metadata:
            self._validate_file_path(Path(metadata['path']), result)
        
        # Validate size if present
        if 'size' in metadata:
            size = metadata['size']
            if not isinstance(size, (int, float)):
                result.add_error(ValidationError("File size must be a number"))
            else:
                file_path = metadata.get('path', 'unknown')
                self._validate_file_size(int(size), file_path, result)
        
        # Validate content type if present
        if 'content_type' in metadata:
            content_type = metadata['content_type']
            if not isinstance(content_type, str):
                result.add_error(ValidationError("Content type must be a string"))
            elif not content_type:
                result.add_warning(ValidationWarning("Content type is empty"))
    
    def _validate_file_size(self, size_bytes: int, file_path: str, result: ValidationResult) -> None:
        """Validate file size."""
        # Check minimum size
        if size_bytes < self.min_size_bytes:
            result.add_error(ValidationError(
                f"File too small: {size_bytes} bytes < {self.min_size_bytes} bytes minimum",
                details={"file": file_path, "size": size_bytes}
            ))
        
        # Check maximum size
        max_size_bytes = self.max_size_mb * 1024 * 1024
        if size_bytes > max_size_bytes:
            result.add_error(ValidationError(
                f"File too large: {size_bytes / (1024*1024):.2f}MB > {self.max_size_mb}MB maximum",
                details={"file": file_path, "size": size_bytes}
            ))
        
        # Warn about large files
        if size_bytes > max_size_bytes * 0.8:
            result.add_warning(ValidationWarning(
                f"File is approaching size limit: {size_bytes / (1024*1024):.2f}MB",
                field_name="size"
            ))


class PathValidator(BaseValidator):
    """Validates file paths for security and correctness."""
    
    def __init__(self, base_dir: Path | None = None, allow_absolute: bool = False):
        """Initialize path validator.
        
        Args:
            base_dir: Base directory for relative path validation
            allow_absolute: Whether to allow absolute paths
        """
        self.base_dir = base_dir
        self.allow_absolute = allow_absolute
    
    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        """Perform path validation."""
        if isinstance(target, Path):
            path = target
        elif isinstance(target, str):
            path = Path(target)
        else:
            result.add_error(ValidationError("Target must be a Path or string"))
            return
        
        # Check for path traversal attempts
        try:
            # Resolve to catch .. traversals
            resolved = path.resolve()
            
            # Check if absolute path is allowed
            if resolved.is_absolute() and not self.allow_absolute:
                result.add_error(ValidationError(
                    "Absolute paths not allowed",
                    details={"path": str(path)}
                ))
            
            # Check if path is within base directory
            if self.base_dir and resolved.is_absolute():
                base_resolved = self.base_dir.resolve()
                try:
                    resolved.relative_to(base_resolved)
                except ValueError:
                    result.add_error(ValidationError(
                        "Path is outside allowed base directory",
                        details={
                            "path": str(path),
                            "base_dir": str(self.base_dir)
                        }
                    ))
            
        except Exception as e:
            result.add_error(ValidationError(
                f"Invalid path: {e!s}",
                details={"path": str(target)}
            ))
        
        # Check for suspicious patterns
        suspicious_patterns = ['..', '~/', './', '//', '\\\\']
        path_str = str(path)
        for pattern in suspicious_patterns:
            if pattern in path_str:
                result.add_warning(ValidationWarning(
                    f"Path contains suspicious pattern: '{pattern}'",
                    field_name="path",
                    details={"pattern": pattern, "path": path_str}
                ))
    
    def validate_filename(self, filename: str, strict: bool = True) -> ValidationResult:
        """Validate a filename for security and correctness.
        
        Args:
            filename: Filename to validate
            strict: If True, use stricter validation rules
            
        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult()
        
        # Check for empty filename
        if not filename:
            result.add_error(ValidationError("Filename cannot be empty"))
            return result
        
        # Check for path separators and null bytes
        invalid_chars = ['/', '\\', '\0']
        for char in invalid_chars:
            if char in filename:
                result.add_error(ValidationError(
                    f"Invalid filename: contains '{char}'",
                    details={"filename": filename}
                ))
        
        # Check for directory traversal
        if '..' in filename:
            result.add_error(ValidationError(
                "Filename cannot contain directory traversal patterns",
                details={"filename": filename}
            ))
        
        # Additional strict checks
        if strict:
            # Check for problematic characters on Windows
            windows_invalid = '<>:"|?*'
            for char in windows_invalid:
                if char in filename:
                    result.add_warning(ValidationWarning(
                        f"Filename contains character that may cause issues on Windows: '{char}'",
                        field_name="filename"
                    ))
            
            # Check for leading/trailing dots or spaces
            if filename.startswith('.') or filename.endswith('.'):
                result.add_warning(ValidationWarning(
                    "Filename starts or ends with a dot, which may be hidden on some systems",
                    field_name="filename"
                ))
            
            if filename.startswith(' ') or filename.endswith(' '):
                result.add_warning(ValidationWarning(
                    "Filename starts or ends with a space, which may cause issues",
                    field_name="filename"
                ))
        
        return result