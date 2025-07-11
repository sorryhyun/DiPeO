# Type definitions for template processing

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class TemplateContext:
    # Context for template processing
    variables: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TemplateResult:
    # Result of template processing
    content: str
    missing_keys: List[str] = field(default_factory=list)
    used_keys: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)