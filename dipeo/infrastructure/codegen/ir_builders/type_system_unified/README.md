# Unified Type System

**Status**: ✅ Implementation Complete (Phase 3)
**Date**: 2025-09-30
**Tests**: 46/46 passing

A configuration-driven type conversion system that consolidates three previously separate type conversion systems into one unified, maintainable solution.

## Overview

This module provides a comprehensive type conversion system for the DiPeO code generation pipeline, consolidating:

1. **TypeConverter** (`type_system/converter.py`) - Core TypeScript ↔ Python conversions
2. **TypeConversionFilters** (`templates/filters/type_conversion_filters.py`) - Jinja2 template filters
3. **StrawberryTypeResolver** (`type_resolver.py`) - Strawberry GraphQL type resolution

### Key Benefits

- **Configuration-Driven**: All type mappings in YAML files
- **Single Source of Truth**: One system for all type conversions
- **Well-Tested**: 46 comprehensive tests covering all conversion paths
- **Extensible**: Runtime type registration via TypeRegistry
- **Performance**: Built-in caching for frequently used conversions
- **Backward Compatible**: Can coexist with old systems during migration

## Components

### 1. UnifiedTypeConverter

Main converter class handling all type conversions.

**Supported Conversions**:
- TypeScript → Python
- TypeScript → GraphQL
- GraphQL → TypeScript
- GraphQL → Python
- TypeScript GraphQL Input → Python (for codegen patterns)

**Features**:
- Configuration-driven mappings from YAML files
- Intelligent type detection (arrays, unions, literals, generics, etc.)
- Field-context-aware conversions (e.g., `number` → `int` for specific fields)
- Branded ID type handling
- Type alias resolution
- Performance caching

```python
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeConverter

converter = UnifiedTypeConverter()

# Basic conversions
python_type = converter.ts_to_python("string[]")  # Returns: "List[str]"
graphql_type = converter.ts_to_graphql("number")  # Returns: "Float"

# Context-aware conversion
python_type = converter.ts_to_python("number", field_name="count")  # Returns: "int"

# GraphQL input patterns
python_type = converter.ts_graphql_input_to_python("Scalars['ID']['input']")  # Returns: "str"

# Utility methods
default = converter.get_default_value("List[str]")  # Returns: "[]"
imports = converter.get_python_imports(["List[str]", "Dict[str, Any]"])
# Returns: ["from typing import Any", "from typing import Dict", "from typing import List"]
```

### 2. TypeRegistry

Runtime type registration and management.

**Supported Types**:
- Branded types (e.g., `NodeID`, `DiagramID`)
- Enum types
- Custom types with converters
- Domain model types

```python
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import TypeRegistry

registry = TypeRegistry()

# Register a branded ID type
registry.register_branded_type("CustomID", python_type="str")

# Register an enum
registry.register_enum_type("Status", ["PENDING", "RUNNING", "COMPLETED"])

# Register a custom type with converter
def uppercase_converter(value: str) -> str:
    return value.upper()

registry.register_custom_type(
    "UpperString",
    python_type="str",
    converter=uppercase_converter
)

# Query types
is_branded = registry.is_branded_type("CustomID")  # Returns: True
python_type = registry.get_python_type("CustomID")  # Returns: "str"

# Convert values
result = registry.convert_value("UpperString", "hello")  # Returns: "HELLO"
```

### 3. UnifiedTypeResolver

Strawberry GraphQL type resolution and conversion method generation.

**Features**:
- Field-level type resolution for Strawberry GraphQL
- Automatic detection of manual conversion needs
- Generation of `from_pydantic()` conversion methods
- Context-aware field handling
- Integration with UnifiedTypeConverter

```python
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeResolver

resolver = UnifiedTypeResolver()

# Resolve a field
field = {
    "name": "nodes",
    "type": "List[DomainNode]",
    "optional": False
}
resolved = resolver.resolve_field(field, type_name="DomainDiagram")

print(resolved.name)  # "nodes"
print(resolved.python_type)  # "List[DomainNode]"
print(resolved.strawberry_type)  # "List[DomainNodeType]"

# Process a complete type
interface = {
    "name": "TestType",
    "description": "Test type",
    "properties": [
        {"name": "id", "type": "str", "optional": False},
        {"name": "name", "type": "str", "optional": False}
    ]
}
processed = resolver.process_type(interface)

# Check conversion requirements
needs_manual = resolver.should_use_manual_conversion("DomainDiagram")  # True
can_use_decorator = resolver.should_use_pydantic_decorator("Vec2")  # True
```

## Configuration Files

### type_mappings.yaml

Core type mappings for TypeScript ↔ Python conversions:

- `base_types`: Base type mappings (string → str, number → float, etc.)
- `type_aliases`: Historical type aliases for backward compatibility
- `branded_types`: List of branded ID types
- `field_overrides`: Field-specific type overrides (e.g., integer fields)
- `patterns`: Regex patterns for type detection
- `conversion_rules`: Rules for complex type patterns
- `default_values`: Default values for Python types
- `python_imports`: Required imports for type usage

### graphql_mappings.yaml

GraphQL and Strawberry-specific mappings:

- `scalar_mappings`: Branded ID → Scalar mappings
- `json_types`: Types that should be JSONScalar
- `manual_conversion_types`: Types needing manual `from_pydantic()` methods
- `pydantic_decorator_types`: Types that can use pydantic decorator
- `json_field_patterns`: Field names that suggest JSON data
- `strawberry_type_rules`: Rules for Strawberry type resolution
- `conversion_templates`: Templates for conversion expressions
- `graphql_input_mappings`: GraphQL codegen input type mappings

## Testing

Run the comprehensive test suite:

```bash
python -m pytest dipeo/infrastructure/codegen/ir_builders/type_system_unified/test_unified_type_system.py -v
```

**Test Coverage**:
- 22 tests for UnifiedTypeConverter
- 10 tests for TypeRegistry
- 11 tests for UnifiedTypeResolver
- 2 integration tests

## Migration Guide

### From TypeConverter

```python
# Old way
from dipeo.infrastructure.codegen.type_system import TypeConverter
converter = TypeConverter()
python_type = converter.ts_to_python("string[]")

# New way
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeConverter
converter = UnifiedTypeConverter()
python_type = converter.ts_to_python("string[]")
```

### From TypeConversionFilters

```python
# Old way
from dipeo.infrastructure.codegen.templates.filters.type_conversion_filters import TypeConversionFilters
python_type = TypeConversionFilters.ts_to_python("string", "field_name")

# New way
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeConverter
converter = UnifiedTypeConverter()
python_type = converter.ts_to_python("string", "field_name")
```

### From StrawberryTypeResolver

```python
# Old way
from dipeo.infrastructure.codegen.type_resolver import StrawberryTypeResolver
resolver = StrawberryTypeResolver()
resolved = resolver.resolve_field(field, type_name)

# New way
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeResolver
resolver = UnifiedTypeResolver()
resolved = resolver.resolve_field(field, type_name)
```

## Custom Mappings

You can extend the type system with custom mappings:

```python
custom_mappings = {
    "ts_to_python": {
        "MyCustomType": "MyPythonClass"
    },
    "ts_to_graphql": {
        "MyCustomType": "MyGraphQLType"
    }
}

converter = UnifiedTypeConverter(custom_mappings=custom_mappings)
```

## Performance

The unified type system includes several performance optimizations:

1. **Configuration Caching**: YAML configs loaded once at initialization
2. **Type Conversion Caching**: Results cached with `functools.lru_cache`
3. **Pattern Pre-compilation**: Regex patterns compiled at module load
4. **Lazy Evaluation**: Type resolution only when needed

## File Structure

```
type_system_unified/
├── __init__.py              # Module exports
├── README.md                # This file
├── MAPPING_MATRIX.md        # Detailed analysis of old systems
├── converter.py             # UnifiedTypeConverter implementation
├── registry.py              # TypeRegistry implementation
├── resolver.py              # UnifiedTypeResolver implementation
├── test_unified_type_system.py  # Comprehensive test suite
├── type_mappings.yaml       # TypeScript/Python mappings
└── graphql_mappings.yaml    # GraphQL/Strawberry mappings
```

## Future Enhancements

- [ ] Runtime configuration hot-reload
- [ ] Type validation with JSON schema
- [ ] Performance metrics and profiling
- [ ] Additional type system support (e.g., Rust, Java)
- [ ] Web-based configuration editor

## Related Documentation

- [Code Generation Guide](../../../../../docs/projects/code-generation-guide.md)
- [Overall Architecture](../../../../../docs/architecture/overall_architecture.md)
- [Codegen TODO](../../TODO.md) - Phase 3 details

## Support

For issues or questions:
- Create an issue at https://github.com/anthropics/dipeo/issues
- Consult the mapping matrix: `MAPPING_MATRIX.md`
- Review tests: `test_unified_type_system.py`