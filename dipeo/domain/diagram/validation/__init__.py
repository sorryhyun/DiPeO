"""Domain diagram validation service.

This module uses lazy imports to break circular dependencies between validation
and compilation modules. See README.md for architecture details.

Circular Dependency Problem:
  - validation needs DomainDiagramCompiler (to validate diagrams)
  - compilation needs validation.utils (for shared validation logic)

Solution:
  - Lazy imports via __getattr__ defer the import of service.py until needed
  - This breaks the circular dependency at module load time
  - utils.py remains importable by compilation modules

Usage:
  Always import from this module, not directly from service.py:
    from dipeo.domain.diagram.validation import validate_diagram  # Good
    from dipeo.domain.diagram.validation.service import validate_diagram  # Bad
"""


def __getattr__(name):
    """Lazy import validation functions to avoid circular dependency.

    This defers importing service.py (which imports DomainDiagramCompiler)
    until the function is actually called, allowing compilation modules to
    safely import validation.utils without triggering the circular import.
    """
    if name in [
        "collect_diagnostics",
        "validate_diagram",
        "validate_structure_only",
        "validate_connections",
    ]:
        from .service import (
            collect_diagnostics,
            validate_connections,
            validate_diagram,
            validate_structure_only,
        )

        globals()[name] = locals()[name]
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "collect_diagnostics",
    "validate_connections",
    "validate_diagram",
    "validate_structure_only",
]
