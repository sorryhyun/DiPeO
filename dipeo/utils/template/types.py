# Type definitions for template processing

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TemplateContext:
    # Context for template processing
    variables: dict[str, Any]
    metadata: dict[str, Any] | None = None


@dataclass
class TemplateResult:
    # Result of template processing
    content: str
    missing_keys: list[str] = field(default_factory=list)
    used_keys: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)