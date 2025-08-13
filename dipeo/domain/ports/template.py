# Template processing port - infrastructure must provide implementations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class TemplateResult:
    # Result of template processing with detailed feedback
    content: str
    missing_keys: list[str] = field(default_factory=list)
    used_keys: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class TemplateProcessorPort(Protocol):
    """Port for template processing functionality.
    
    Infrastructure layer must provide implementations for variable substitution,
    conditionals, loops, and other template processing features.
    """
    
    def process(self, template: str, context: dict[str, Any]) -> TemplateResult:
        """Process template and return detailed result including errors and missing keys."""
        ...
    
    def process_simple(self, template: str, context: dict[str, Any]) -> str:
        """Convenience method that returns just the processed content."""
        ...
    
    def process_single_brace(self, template: str, context: dict[str, Any]) -> str:
        """Process single brace variables {var} for arrow transformations."""
        ...
    
    def extract_variables(self, template: str) -> list[str]:
        """Extract all variable names from a template."""
        ...