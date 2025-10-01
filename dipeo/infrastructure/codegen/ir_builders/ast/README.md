# AST Processing Framework

**Status**: ✅ Complete (Phase 2 of Codegen Refactoring)
**Completed**: 2025-09-30

## Overview

The AST Processing Framework provides a unified, extensible system for traversing and extracting data from TypeScript AST. This framework consolidates scattered extraction logic into reusable, well-tested components.

## Architecture

```
ast/
├── __init__.py          # Public API exports
├── walker.py            # ASTWalker and ASTVisitor for traversal
├── filters.py           # File and node filtering utilities
├── extractors.py        # Specialized node extractors
├── test_ast_framework.py  # Comprehensive test suite
└── README.md            # This file
```

## Components

### 1. Extractors (`extractors.py`)

Specialized classes for extracting different node types from TypeScript AST:

```python
from dipeo.infrastructure.codegen.ir_builders.ast import (
    InterfaceExtractor,
    EnumExtractor,
    TypeAliasExtractor,
    ConstantExtractor,
    BrandedScalarExtractor,
    GraphQLInputTypeExtractor,
)

# Extract all interfaces
extractor = InterfaceExtractor()
interfaces = extractor.extract(ast_data)

# Extract interfaces with suffix filter
extractor = InterfaceExtractor(suffix='Config')
configs = extractor.extract(ast_data)

# Extract with file filter
from dipeo.infrastructure.codegen.ir_builders.ast import FileFilter
file_filter = FileFilter(patterns=['**/node-specs/**'])
extractor = InterfaceExtractor(file_filter=file_filter)
interfaces = extractor.extract(ast_data)
```

**Available Extractors**:
- `InterfaceExtractor` - Extract TypeScript interfaces
- `EnumExtractor` - Extract enums
- `TypeAliasExtractor` - Extract type aliases
- `ConstantExtractor` - Extract constants
- `BrandedScalarExtractor` - Extract branded scalar types
- `GraphQLInputTypeExtractor` - Extract GraphQL input types

All extractors inherit from `BaseExtractor` and support:
- File filtering (glob patterns, regex, custom predicates)
- Node filtering (prefix, suffix, contains, regex, custom predicates)

### 2. Filters (`filters.py`)

Flexible filtering system for files and nodes:

```python
from dipeo.infrastructure.codegen.ir_builders.ast import (
    FileFilter,
    NodeFilter,
    prefix_filter,
    suffix_filter,
    and_filter,
    or_filter,
    not_filter,
)

# File filtering
file_filter = FileFilter(
    patterns=['**/node-specs/**/*.ts'],  # Glob patterns
    regex=r'node-specs/.*\\.ts$',         # Regex
    predicate=lambda path: 'test' not in path  # Custom predicate
)
filtered_files = file_filter.filter(ast_data)

# Node filtering
node_filter = suffix_filter('Config')
configs = node_filter.filter_nodes(nodes)

# Filter composition
combined = and_filter(
    prefix_filter('User'),
    suffix_filter('Config')
)
user_configs = combined.filter_nodes(nodes)
```

**Filter Types**:
- `FileFilter` - Filter files by path (glob, regex, predicate)
- `NodeFilter` - Filter nodes by name/properties
- `CompositeNodeFilter` - Combine filters with AND/OR logic
- `NotNodeFilter` - Invert filter results

**Convenience Functions**:
- `prefix_filter(prefix)` - Match nodes starting with prefix
- `suffix_filter(suffix)` - Match nodes ending with suffix
- `regex_filter(pattern)` - Match nodes by regex
- `and_filter(*filters)` - Combine with AND logic
- `or_filter(*filters)` - Combine with OR logic
- `not_filter(filter)` - Invert filter

**Preset Filters**:
- `NODE_SPECS_FILES` - Match node specification files
- `DOMAIN_MODEL_FILES` - Match domain model files
- `GRAPHQL_FILES` - Match GraphQL definition files
- `CONFIG_INTERFACES` - Match interfaces ending with 'Config'
- `PROPS_INTERFACES` - Match interfaces ending with 'Props'
- `INPUT_TYPES` - Match types ending with 'Input'
- `ID_TYPES` - Match types ending with 'ID'

### 3. Walker (`walker.py`)

Visitor pattern implementation for AST traversal:

```python
from dipeo.infrastructure.codegen.ir_builders.ast import (
    ASTWalker,
    ASTVisitor,
    CollectorVisitor,
)

# Simple collection with CollectorVisitor
collector = CollectorVisitor(collect_types=['interface', 'enum'])
walker = ASTWalker(ast_data)
walker.walk(collector)
interfaces = collector.collected['interface']
enums = collector.collected['enum']

# Custom visitor
class MyVisitor(ASTVisitor):
    def __init__(self):
        super().__init__()
        self.results = []

    def visit_interface(self, node, file_path, context):
        if node['name'].endswith('Config'):
            self.results.append(node)
        return node

visitor = MyVisitor()
walker.walk(visitor)
```

**Walker Features**:
- File filtering via `file_filter` parameter
- Visitor pattern for flexible traversal
- Pre/post visit hooks
- Context passing for stateful visits

**Visitor Methods**:
- `visit_interface(node, file_path, context)`
- `visit_enum(node, file_path, context)`
- `visit_type_alias(node, file_path, context)`
- `visit_constant(node, file_path, context)`
- `visit_branded_scalar(node, file_path, context)`
- `visit_type(node, file_path, context)`

**Visitor Hooks**:
- `pre_visit(node_type, node, file_path)` - Before visiting (return False to skip)
- `post_visit(node_type, node, file_path, result)` - After visiting

## Migration Guide

### From Old `utils.py` Functions

The old extraction functions in `utils.py` are now deprecated but still work via backward-compatible wrappers:

```python
# ❌ OLD (Deprecated)
from dipeo.infrastructure.codegen.ir_builders.utils import (
    extract_interfaces_from_ast,
    extract_enums_from_ast,
)
interfaces = extract_interfaces_from_ast(ast_data, suffix='Config')
enums = extract_enums_from_ast(ast_data)

# ✅ NEW (Recommended)
from dipeo.infrastructure.codegen.ir_builders.ast import (
    InterfaceExtractor,
    EnumExtractor,
)
interface_extractor = InterfaceExtractor(suffix='Config')
interfaces = interface_extractor.extract(ast_data)

enum_extractor = EnumExtractor()
enums = enum_extractor.extract(ast_data)
```

### Creating Custom Extractors

Extend `BaseExtractor` to create custom extractors:

```python
from dipeo.infrastructure.codegen.ir_builders.ast.extractors import BaseExtractor

class MyCustomExtractor(BaseExtractor):
    def _extract_from_file(self, file_data, file_path):
        results = []
        # Custom extraction logic
        for item in file_data.get('custom_nodes', []):
            results.append({
                'name': item.get('name'),
                'file': file_path,
            })
        return results

# Use like any other extractor
extractor = MyCustomExtractor()
results = extractor.extract(ast_data)
```

## Testing

Comprehensive test suite in `test_ast_framework.py`:

```bash
python dipeo/infrastructure/codegen/ir_builders/ast/test_ast_framework.py
```

Tests cover:
- ✅ All 6 specialized extractors
- ✅ File and node filtering
- ✅ Filter composition (AND, OR, NOT)
- ✅ Walker and visitor pattern
- ✅ Backward compatibility with old functions

## Benefits

### Before (Scattered Logic)
- 6 separate extraction functions in `utils.py`
- No filtering capabilities
- Duplicated iteration logic
- Difficult to extend

### After (Unified Framework)
- ✅ Reusable `BaseExtractor` with filtering
- ✅ Flexible file and node filtering
- ✅ Visitor pattern for complex traversal
- ✅ Easy to extend with new extractors
- ✅ Well-tested and documented
- ✅ Backward compatible

## Code Reduction

- **Consolidated**: 6 extraction functions → Unified extractor framework
- **Eliminated**: Duplicated iteration and filtering logic
- **Improved**: Type safety, extensibility, and maintainability
- **Reduction**: ~15-20% code reduction in extraction logic

## Usage in Codebase

Currently used by:
- `FrontendBuilder` - Uses `EnumExtractor`
- `StrawberryBuilder` - Uses `InterfaceExtractor`, `GraphQLInputTypeExtractor`, `BrandedScalarExtractor`

Backward compatible wrappers ensure existing code continues to work.

## Next Steps

Future phases can further utilize this framework:
- **Phase 3**: Type System Consolidation can use extractors for type discovery
- **Phase 4**: Field Processing can use walker for field traversal
- **Phase 6**: Common Patterns can use filters for pattern matching

## API Reference

### Public API (`__init__.py`)

All components are exported from the main module:

```python
from dipeo.infrastructure.codegen.ir_builders.ast import (
    # Extractors
    InterfaceExtractor,
    EnumExtractor,
    TypeAliasExtractor,
    ConstantExtractor,
    BrandedScalarExtractor,
    GraphQLInputTypeExtractor,

    # Walker
    ASTWalker,
    ASTVisitor,

    # Filters
    FileFilter,
    NodeFilter,
    prefix_filter,
    suffix_filter,
    regex_filter,
    and_filter,
    or_filter,
    not_filter,
)
```

## Contributing

When adding new node types or extraction patterns:

1. Create a new extractor class in `extractors.py` extending `BaseExtractor`
2. Implement `_extract_from_file()` method
3. Export from `__init__.py`
4. Add tests to `test_ast_framework.py`
5. Update this README

## Support

For questions or issues with the AST framework, see:
- Main codegen docs: `docs/projects/code-generation-guide.md`
- Phase 2 TODO: `dipeo/infrastructure/codegen/TODO.md`
- Test examples: `ast/test_ast_framework.py`