"""Person operations module.

Consolidates all person-related logic:
- Extraction from different formats
- Reference resolution (ID <-> label)
- Validation of person references and API keys
"""

from .operations import PersonExtractor, PersonReferenceResolver
from .validation import PersonValidator

__all__ = [
    "PersonExtractor",
    "PersonReferenceResolver",
    "PersonValidator",
]
