"""Input resolution services for execution.

This module contains the interface-based input resolution system that separates
compile-time and runtime concerns for better maintainability and extensibility.

Key interfaces:
- CompileTimeResolver: Handles connection resolution at compile time
- RuntimeInputResolver: Resolves actual input values during execution
- NodeTypeStrategy: Provides node-type-specific behavior
- TransformationEngine: Applies data transformations

The system uses adapters for backward compatibility during migration.
"""

__all__ = []