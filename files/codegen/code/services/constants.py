"""Shared constants for code generation

Consolidates common constants used across multiple generators to reduce
duplication and ensure consistency.
"""

from typing import Dict, Set, Optional

# Known enum types that should be imported from enums module
KNOWN_ENUMS: Set[str] = {
    'MemoryProfile',
    'ToolSelection', 
    'SupportedLanguage',
    'HttpMethod',
    'DBBlockSubType',
    'HookType',
    'NotionOperation',
    'HookTriggerMode',
    'ContentType',
    'DiagramFormat',
    'MemoryView',
    'NodeLifecyclePhase',
    'ValidationMode',
    'ExecutionMode',
    'ErrorHandlingStrategy',
    'CacheStrategy',
}

# Basic type mappings from generic/TypeScript to Python
TS_TO_PYTHON_TYPE_MAP: Dict[str, str] = {
    # Basic types
    'string': 'str',
    'text': 'str',
    'integer': 'int',
    'int': 'int',
    'number': 'float',  # Note: some generators use 'int' for 'number'
    'float': 'float',
    'double': 'float',
    'boolean': 'bool',
    'bool': 'bool',
    'object': 'Dict[str, Any]',
    'dict': 'Dict[str, Any]',
    'array': 'List[Any]',
    'list': 'List[Any]',
    'any': 'Any',
    'unknown': 'Any',
    'null': 'None',
    'undefined': 'None',
    'void': 'None',
    'never': 'Any',  # TypeScript never type
    
    # Complex types
    'JSON': 'Dict[str, Any]',
    'JsonValue': 'Any',
    'Record': 'Dict[str, Any]',
}

# TypeScript to GraphQL type mappings
TS_TO_GRAPHQL_TYPE_MAP: Dict[str, str] = {
    'string': 'String',
    'text': 'String',
    'integer': 'Int',
    'int': 'Int',
    'number': 'Float',
    'float': 'Float',
    'double': 'Float',
    'boolean': 'Boolean',
    'bool': 'Boolean',
    'any': 'JSON',  # Requires custom scalar
    'unknown': 'JSON',
    'object': 'JSON',
    'dict': 'JSON',
    'JSON': 'JSON',
    'JsonValue': 'JSON',
    
    # Special handling needed
    'array': '[JSON]',  # Generic array
    'list': '[JSON]',
    'null': None,  # GraphQL handles null differently
    'undefined': None,
    'void': None,
}

# Python type to TypeScript type mappings (reverse mapping)
PYTHON_TO_TS_TYPE_MAP: Dict[str, str] = {
    'str': 'string',
    'int': 'number',
    'float': 'number',
    'bool': 'boolean',
    'None': 'null',
    'Any': 'any',
    'Dict': 'Record<string, any>',
    'List': 'Array',
    'Tuple': 'Array',
    'Set': 'Set',
    'FrozenSet': 'ReadonlySet',
}

# Default values by type and language
DEFAULT_VALUES = {
    'python': {
        'str': '""',
        'int': '0',
        'float': '0.0',
        'bool': 'False',
        'list': '[]',
        'dict': '{}',
        'set': 'set()',
        'tuple': '()',
        'None': 'None',
        'Any': 'None',
    },
    'typescript': {
        'string': '""',
        'number': '0',
        'boolean': 'false',
        'array': '[]',
        'object': '{}',
        'null': 'null',
        'undefined': 'undefined',
        'any': 'null',
    },
    'graphql': {
        'String': '""',
        'Int': '0',
        'Float': '0.0',
        'Boolean': 'false',
        'ID': '""',
        'JSON': '{}',
    }
}

# Common import statements by target language
COMMON_IMPORTS = {
    'python': {
        'typing': [
            'from typing import Any, Dict, List, Optional, Union, Literal',
            'from typing import TypeVar, Generic, Protocol, TypedDict',
        ],
        'dataclasses': [
            'from dataclasses import dataclass, field',
        ],
        'pydantic': [
            'from pydantic import BaseModel, Field, validator',
        ],
        'collections': [
            'from collections.abc import Sequence, Mapping',
        ],
    },
    'typescript': {
        'basic': [
            "import { z } from 'zod';",
        ],
        'react': [
            "import React from 'react';",
            "import { FC, ReactNode } from 'react';",
        ],
        'types': [
            "import type { Node, Edge, Connection } from 'reactflow';",
        ],
    },
    'graphql': {
        'scalars': [
            'scalar JSON',
            'scalar DateTime',
            'scalar UUID',
        ],
    }
}

# File extensions by language
FILE_EXTENSIONS = {
    'python': '.py',
    'typescript': '.ts',
    'javascript': '.js',
    'react': '.tsx',
    'graphql': '.graphql',
    'yaml': '.yaml',
    'json': '.json',
}

# Template file patterns
TEMPLATE_PATTERNS = {
    'jinja2': '*.j2',
    'jinja': '*.jinja',
    'mustache': '*.mustache',
    'handlebars': '*.hbs',
}

# Node type categories (for organization)
NODE_CATEGORIES = {
    'input': ['TextInput', 'NumberInput', 'BooleanInput', 'FileInput'],
    'output': ['TextOutput', 'DataOutput', 'FileOutput', 'ConsoleOutput'],
    'processing': ['Transform', 'Filter', 'Map', 'Reduce', 'Sort'],
    'control': ['If', 'Loop', 'Switch', 'Parallel', 'Sequential'],
    'external': ['HttpRequest', 'DatabaseQuery', 'FileSystem', 'Command'],
    'ai': ['LLMNode', 'ChatNode', 'EmbeddingNode', 'ClassifierNode'],
}

# Reserved keywords by language (to avoid in generated code)
RESERVED_KEYWORDS = {
    'python': {
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
        'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
        'while', 'with', 'yield', 'match', 'case',
    },
    'typescript': {
        'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
        'default', 'delete', 'do', 'else', 'enum', 'export', 'extends',
        'false', 'finally', 'for', 'function', 'if', 'import', 'in',
        'instanceof', 'new', 'null', 'return', 'super', 'switch', 'this',
        'throw', 'true', 'try', 'typeof', 'var', 'void', 'while', 'with',
        'as', 'implements', 'interface', 'let', 'package', 'private',
        'protected', 'public', 'static', 'yield', 'any', 'boolean', 'number',
        'string', 'symbol', 'type', 'unknown', 'never',
    },
    'graphql': {
        'query', 'mutation', 'subscription', 'fragment', 'schema', 'type',
        'interface', 'union', 'enum', 'input', 'extend', 'scalar', 'directive',
        'implements', 'on', 'true', 'false', 'null',
    }
}

# Common regex patterns for validation
VALIDATION_PATTERNS = {
    'identifier': r'^[a-zA-Z_][a-zA-Z0-9_]*$',
    'snake_case': r'^[a-z]+(_[a-z]+)*$',
    'camel_case': r'^[a-z]+([A-Z][a-z]+)*$',
    'pascal_case': r'^[A-Z][a-z]+([A-Z][a-z]+)*$',
    'kebab_case': r'^[a-z]+(-[a-z]+)*$',
    'semver': r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$',
}


def is_enum_type(type_name: str) -> bool:
    """Check if a type name is a known enum."""
    return type_name in KNOWN_ENUMS


def get_python_import_for_type(type_name: str) -> Optional[str]:
    """Get the Python import statement needed for a type."""
    if type_name in KNOWN_ENUMS:
        return f"from dipeo.domain.enums import {type_name}"
    
    # Check if it needs typing imports
    if any(t in type_name for t in ['List', 'Dict', 'Optional', 'Union', 'Any']):
        return "from typing import " + ", ".join(
            t for t in ['List', 'Dict', 'Optional', 'Union', 'Any']
            if t in type_name
        )
    
    return None


def sanitize_identifier(name: str, language: str = 'python') -> str:
    """Sanitize an identifier to avoid reserved keywords."""
    reserved = RESERVED_KEYWORDS.get(language, set())
    if name in reserved:
        return f"{name}_"  # Add underscore suffix
    return name