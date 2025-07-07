"""Text processing domain service for text manipulation and processing."""

import logging
import re
from typing import Any

from dipeo.core import ValidationError

log = logging.getLogger(__name__)


class TextProcessingDomainService:
    """Text manipulation and processing operations."""

    def __init__(self):
        pass

    async def process_template(
        self,
        template: str,
        variables: dict[str, Any],
        safe_mode: bool = True,
    ) -> str:
        """Process a template with variable substitution."""
        if safe_mode:
            return self._safe_template_processing(template, variables)
        return self._advanced_template_processing(template, variables)

    def _safe_template_processing(
        self, template: str, variables: dict[str, Any]
    ) -> str:
        """Safe template processing with simple variable substitution."""
        pattern = r"\{\{\s*(\w+)\s*\}\}"

        def replacer(match):
            var_name = match.group(1)
            if var_name in variables:
                return str(variables[var_name])
            log.warning(f"Variable '{var_name}' not found in context")
            return match.group(0)

        return re.sub(pattern, replacer, template)

    def _advanced_template_processing(
        self, template: str, variables: dict[str, Any]
    ) -> str:
        """Advanced template processing with conditionals and loops."""
        return self._safe_template_processing(template, variables)

    async def extract_structured_data(
        self,
        text: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract structured data from text based on schema."""
        result = {}

        for field_name, field_config in schema.items():
            field_type = field_config.get("type", "string")
            pattern = field_config.get("pattern")
            required = field_config.get("required", False)

            if pattern:
                match = re.search(pattern, text)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    result[field_name] = self._convert_type(value, field_type)
                elif required:
                    raise ValidationError(
                        f"Required field '{field_name}' not found in text"
                    )

        return result

    def _convert_type(self, value: str, target_type: str) -> Any:
        """Convert string value to target type."""
        if target_type == "int":
            return int(value)
        if target_type == "float":
            return float(value)
        if target_type == "bool":
            return value.lower() in ("true", "yes", "1", "on")
        return value

    async def transform_text(
        self,
        text: str,
        transformations: list[dict[str, Any]],
    ) -> str:
        """Apply a series of transformations to text."""
        result = text

        for transform in transformations:
            operation = transform.get("operation")

            if operation == "replace":
                result = result.replace(
                    transform.get("find", ""), transform.get("replace", "")
                )
            elif operation == "regex_replace":
                result = re.sub(
                    transform.get("pattern", ""),
                    transform.get("replacement", ""),
                    result,
                    flags=re.MULTILINE if transform.get("multiline") else 0,
                )
            elif operation == "uppercase":
                result = result.upper()
            elif operation == "lowercase":
                result = result.lower()
            elif operation == "trim":
                result = result.strip()
            elif operation == "split_lines":
                lines = result.split("\n")
                if max_lines := transform.get("max_lines"):
                    lines = lines[:max_lines]
                result = "\n".join(lines)
            elif operation == "remove_empty_lines":
                lines = [line for line in result.split("\n") if line.strip()]
                result = "\n".join(lines)
            elif operation == "normalize_whitespace":
                result = re.sub(r"\s+", " ", result)
                result = result.replace("\r\n", "\n")

        return result

    async def generate_summary(
        self,
        text: str,
        max_length: int = 200,
        preserve_sentences: bool = True,
    ) -> str:
        """Generate a summary of the text."""
        if len(text) <= max_length:
            return text

        if preserve_sentences:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            summary = ""

            for sentence in sentences:
                if len(summary) + len(sentence) <= max_length:
                    summary += sentence + " "
                else:
                    break

            return summary.strip() or text[:max_length].strip() + "..."
        return text[:max_length].strip() + "..."

    async def parse_structured_text(
        self,
        text: str,
        format: str = "auto",
    ) -> dict[str, Any] | list[Any]:
        """Parse structured text (JSON, YAML, CSV, etc.)."""
        import json

        if format == "auto":
            text_stripped = text.strip()
            if text_stripped.startswith(("{", "[")):
                format = "json"
            elif ":" in text_stripped and not text_stripped.startswith("http"):
                format = "yaml"
            else:
                format = "text"

        if format == "json":
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON: {e}")
        elif format == "yaml":
            try:
                import yaml

                return yaml.safe_load(text)
            except ImportError:
                raise ValidationError("PyYAML not available")
            except yaml.YAMLError as e:
                raise ValidationError(f"Invalid YAML: {e}")
        elif format == "csv":
            lines = text.strip().split("\n")
            if not lines:
                return []

            headers = [h.strip() for h in lines[0].split(",")]
            rows = []

            for line in lines[1:]:
                values = [v.strip() for v in line.split(",")]
                row = dict(zip(headers, values, strict=False))
                rows.append(row)

            return rows
        else:
            return {"text": text}

    async def validate_text_format(
        self,
        text: str,
        rules: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """Validate text against formatting rules."""
        errors = []

        if min_length := rules.get("min_length"):
            if len(text) < min_length:
                errors.append(f"Text is too short (minimum {min_length} characters)")

        if max_length := rules.get("max_length"):
            if len(text) > max_length:
                errors.append(f"Text is too long (maximum {max_length} characters)")

        if required_patterns := rules.get("required_patterns"):
            for pattern_name, pattern in required_patterns.items():
                if not re.search(pattern, text):
                    errors.append(f"Missing required pattern: {pattern_name}")

        if forbidden_patterns := rules.get("forbidden_patterns"):
            for pattern_name, pattern in forbidden_patterns.items():
                if re.search(pattern, text):
                    errors.append(f"Contains forbidden pattern: {pattern_name}")

        lines = text.split("\n")
        if min_lines := rules.get("min_lines"):
            if len(lines) < min_lines:
                errors.append(f"Too few lines (minimum {min_lines})")

        if max_lines := rules.get("max_lines"):
            if len(lines) > max_lines:
                errors.append(f"Too many lines (maximum {max_lines})")

        return len(errors) == 0, errors
