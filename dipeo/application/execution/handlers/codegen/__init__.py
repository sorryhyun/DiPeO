"""
Codegen Handler Package

This package consolidates code-generation oriented handlers for organizational clarity.
These handlers work together to enable DiPeO's code generation capabilities:

- template.py: Template rendering with Jinja2
- typescript_ast.py: TypeScript AST parsing and extraction
- ir_builder.py: Intermediate representation building
- schema_validator.py: JSON schema validation

This is an organizational grouping only - the architecture remains unchanged.
Each handler continues to use infrastructure services for their actual work.
"""

from .ir_builder import IrBuilderNodeHandler
from .schema_validator import JsonSchemaValidatorNodeHandler
from .template import TemplateJobNodeHandler
from .typescript_ast import TypescriptAstNodeHandler

__all__ = [
    "IrBuilderNodeHandler",
    "JsonSchemaValidatorNodeHandler",
    "TemplateJobNodeHandler",
    "TypescriptAstNodeHandler",
]
