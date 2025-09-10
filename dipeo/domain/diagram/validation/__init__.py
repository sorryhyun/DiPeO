"""Domain diagram validation service."""


# Lazy imports to avoid circular dependency with domain_compiler
def __getattr__(name):
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
