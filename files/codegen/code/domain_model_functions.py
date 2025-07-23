"""Domain model functions - refactored modular version.

This module provides backwards compatibility by re-exporting functions
from their new modular locations.
"""

# Import readers
from .readers.glob_files import glob_typescript_files
from .readers.typescript_reader import read_typescript_files
from .readers.source_extractor import extract_source

# Import generators
from .generators.pydantic_generator import generate_pydantic_models
from .generators.conversions_generator import generate_conversions
from .generators.zod_generator import generate_zod_schemas
from .generators.graphql_generator import generate_graphql_schema
from .generators.json_schema_generator import generate_json_schemas


# Export all functions for backward compatibility
__all__ = [
    'glob_typescript_files',
    'read_typescript_files',
    'extract_source',
    'generate_pydantic_models',
    'generate_conversions',
    'generate_zod_schemas',
    'generate_graphql_schema',
    'generate_json_schemas',
]