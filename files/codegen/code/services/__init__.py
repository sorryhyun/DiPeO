"""DiPeO Code Generation Services

This module provides shared services for code generation to reduce redundancy
and improve maintainability while preserving the distributed nature of the
current generator system.
"""

from .type_algebra import CoreTypeAlgebra, TypeExpression, TypeKind, ScalarType, ProjectionContext
from .type_projectors import PythonProjector, TypeScriptProjector, GraphQLProjector
from .ast_service import ASTService
from .template_service import TemplateService
from .constants import (
    KNOWN_ENUMS, TS_TO_PYTHON_TYPE_MAP, TS_TO_GRAPHQL_TYPE_MAP,
    PYTHON_TO_TS_TYPE_MAP, DEFAULT_VALUES, COMMON_IMPORTS,
    is_enum_type, get_python_import_for_type, sanitize_identifier
)

__all__ = [
    'CoreTypeAlgebra',
    'TypeExpression',
    'TypeKind',
    'ScalarType',
    'ProjectionContext',
    'PythonProjector',
    'TypeScriptProjector',
    'GraphQLProjector',
    'ASTService',
    'TemplateService',
    'KNOWN_ENUMS',
    'TS_TO_PYTHON_TYPE_MAP',
    'TS_TO_GRAPHQL_TYPE_MAP',
    'PYTHON_TO_TS_TYPE_MAP',
    'DEFAULT_VALUES',
    'COMMON_IMPORTS',
    'is_enum_type',
    'get_python_import_for_type',
    'sanitize_identifier',
]