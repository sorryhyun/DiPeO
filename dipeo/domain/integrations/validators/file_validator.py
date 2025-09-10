"""File validation service using unified validation framework."""

from pathlib import Path
from typing import Any

from dipeo.domain.base.exceptions import ValidationError
from dipeo.domain.base.validator import BaseValidator, ValidationResult, ValidationWarning


class FileValidator(BaseValidator):
    """Validates files using the unified validation framework."""

    def __init__(
        self,
        allowed_extensions: list[str] | None = None,
        max_size_mb: float = 10.0,
        min_size_bytes: int = 0,
    ):
        self.allowed_extensions = allowed_extensions
        self.max_size_mb = max_size_mb
        self.min_size_bytes = min_size_bytes

    def validate_extension(
        self, file_path: Path, allowed_extensions: list[str] | None = None
    ) -> None:
        """Validate file extension (raises exception)."""
        extensions = allowed_extensions or self.allowed_extensions
        if not extensions:
            return

        file_ext = file_path.suffix.lower()
        allowed_lower = [ext.lower() for ext in extensions]

        if file_ext not in allowed_lower:
            raise ValidationError(
                f"File extension '{file_ext}' not allowed. " f"Allowed extensions: {extensions}"
            )

    def validate_size(self, file_size: int, max_size_mb: float | None = None) -> None:
        """Validate file size (raises exception)."""
        max_mb = max_size_mb if max_size_mb is not None else self.max_size_mb
        max_bytes = max_mb * 1024 * 1024

        if file_size > max_bytes:
            raise ValidationError(
                f"File too large: {file_size / 1024 / 1024:.2f}MB " f"(max {max_mb}MB)"
            )

    def validate_filename_strict(self, filename: str) -> None:
        """Validate filename strictly (raises exception)."""
        path_validator = PathValidator()
        result = path_validator.validate_filename(filename, strict=True)
        if result.errors:
            raise result.errors[0]

    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        if isinstance(target, Path):
            self._validate_file_path(target, result)
        elif isinstance(target, str):
            self._validate_file_path(Path(target), result)
        elif isinstance(target, dict):
            self._validate_file_metadata(target, result)
        else:
            result.add_error(
                ValidationError("Target must be a Path, string path, or file metadata dict")
            )

    def _validate_file_path(self, file_path: Path, result: ValidationResult) -> None:
        if not file_path.exists():
            result.add_warning(ValidationWarning(f"File does not exist: {file_path}"))

        if self.allowed_extensions:
            file_ext = file_path.suffix.lower()
            allowed_lower = [ext.lower() for ext in self.allowed_extensions]

            if file_ext not in allowed_lower:
                result.add_error(
                    ValidationError(
                        f"File extension '{file_ext}' not allowed",
                        details={
                            "allowed_extensions": self.allowed_extensions,
                            "file": str(file_path),
                        },
                    )
                )

        if not file_path.name:
            result.add_error(ValidationError("File must have a name"))

        problematic_chars = ["<", ">", ":", '"', "|", "?", "*", "\0"]
        for char in problematic_chars:
            if char in str(file_path):
                result.add_warning(
                    ValidationWarning(
                        f"File path contains problematic character: '{char}'", field_name="path"
                    )
                )

        if file_path.exists() and file_path.is_file():
            file_size = file_path.stat().st_size
            self._validate_file_size(file_size, str(file_path), result)

    def _validate_file_metadata(self, metadata: dict, result: ValidationResult) -> None:
        if "path" in metadata:
            self._validate_file_path(Path(metadata["path"]), result)

        if "size" in metadata:
            size = metadata["size"]
            if not isinstance(size, int | float):
                result.add_error(ValidationError("File size must be a number"))
            else:
                file_path = metadata.get("path", "unknown")
                self._validate_file_size(int(size), file_path, result)

        if "content_type" in metadata:
            content_type = metadata["content_type"]
            if not isinstance(content_type, str):
                result.add_error(ValidationError("Content type must be a string"))
            elif not content_type:
                result.add_warning(ValidationWarning("Content type is empty"))

    def _validate_file_size(
        self, size_bytes: int, file_path: str, result: ValidationResult
    ) -> None:
        if size_bytes < self.min_size_bytes:
            result.add_error(
                ValidationError(
                    f"File too small: {size_bytes} bytes < {self.min_size_bytes} bytes minimum",
                    details={"file": file_path, "size": size_bytes},
                )
            )

        max_size_bytes = self.max_size_mb * 1024 * 1024
        if size_bytes > max_size_bytes:
            result.add_error(
                ValidationError(
                    f"File too large: {size_bytes / (1024*1024):.2f}MB > {self.max_size_mb}MB maximum",
                    details={"file": file_path, "size": size_bytes},
                )
            )

        if size_bytes > max_size_bytes * 0.8:
            result.add_warning(
                ValidationWarning(
                    f"File is approaching size limit: {size_bytes / (1024*1024):.2f}MB",
                    field_name="size",
                )
            )


class PathValidator(BaseValidator):
    """Validates file paths for security and correctness."""

    def __init__(self, base_dir: Path | None = None, allow_absolute: bool = False):
        self.base_dir = base_dir
        self.allow_absolute = allow_absolute

    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        if isinstance(target, Path):
            path = target
        elif isinstance(target, str):
            path = Path(target)
        else:
            result.add_error(ValidationError("Target must be a Path or string"))
            return

        try:
            resolved = path.resolve()

            if resolved.is_absolute() and not self.allow_absolute:
                result.add_error(
                    ValidationError("Absolute paths not allowed", details={"path": str(path)})
                )

            if self.base_dir and resolved.is_absolute():
                base_resolved = self.base_dir.resolve()
                try:
                    resolved.relative_to(base_resolved)
                except ValueError:
                    result.add_error(
                        ValidationError(
                            "Path is outside allowed base directory",
                            details={"path": str(path), "base_dir": str(self.base_dir)},
                        )
                    )

        except Exception as e:
            result.add_error(ValidationError(f"Invalid path: {e!s}", details={"path": str(target)}))

        suspicious_patterns = ["..", "~/", "./", "//", "\\\\"]
        path_str = str(path)
        for pattern in suspicious_patterns:
            if pattern in path_str:
                result.add_warning(
                    ValidationWarning(
                        f"Path contains suspicious pattern: '{pattern}'",
                        field_name="path",
                        details={"pattern": pattern, "path": path_str},
                    )
                )

    def validate_filename(self, filename: str, strict: bool = True) -> ValidationResult:
        """Validate a filename for security and correctness."""
        result = ValidationResult()

        if not filename:
            result.add_error(ValidationError("Filename cannot be empty"))
            return result

        invalid_chars = ["/", "\\", "\0"]
        for char in invalid_chars:
            if char in filename:
                result.add_error(
                    ValidationError(
                        f"Invalid filename: contains '{char}'", details={"filename": filename}
                    )
                )

        if ".." in filename:
            result.add_error(
                ValidationError(
                    "Filename cannot contain directory traversal patterns",
                    details={"filename": filename},
                )
            )

        if strict:
            windows_invalid = '<>:"|?*'
            for char in windows_invalid:
                if char in filename:
                    result.add_warning(
                        ValidationWarning(
                            f"Filename contains character that may cause issues on Windows: '{char}'",
                            field_name="filename",
                        )
                    )

            if filename.startswith(".") or filename.endswith("."):
                result.add_warning(
                    ValidationWarning(
                        "Filename starts or ends with a dot, which may be hidden on some systems",
                        field_name="filename",
                    )
                )

            if filename.startswith(" ") or filename.endswith(" "):
                result.add_warning(
                    ValidationWarning(
                        "Filename starts or ends with a space, which may cause issues",
                        field_name="filename",
                    )
                )

        return result
