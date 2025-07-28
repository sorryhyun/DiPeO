"""Python domain models generator module."""

from .python_models_generator import (
    combine_ast_data,
    generate_python_models,
    generate_summary,
    # Backward compatibility
    main
)

__all__ = [
    'combine_ast_data',
    'generate_python_models',
    'generate_summary',
    'main'
]