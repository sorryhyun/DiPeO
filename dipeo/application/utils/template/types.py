# Type definitions for template processing

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TemplateResult:
    # Result of template processing with detailed feedback
    content: str
    missing_keys: list[str] = field(default_factory=list)
    used_keys: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)