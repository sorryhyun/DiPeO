"""
Unified IR Builder for Backend Code Generation
Consolidates all backend extractors into a single IR for template consumption.
"""

from __future__ import annotations
from pathlib import Path
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import sys
import os

# Add the DiPeO base directory to path for imports
sys.path.append(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))


# ============================================================================
# SHARED UTILITIES
# ============================================================================

def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            if (i + 1 < len(name) and name[i + 1].islower()) or (
                i > 0 and name[i - 1].islower()
            ):
                result.append('_')
        result.append(char.lower())
    return ''.join(result)


def snake_to_pascal(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return ''.join(word.title() for word in name.split('_'))


def ts_to_python_type(ts_type: str) -> str:
    """Convert TypeScript type to Python type."""
    type_map = {
        'string': 'str',
        'number': 'float',
        'boolean': 'bool',
        'any': 'Any',
        'unknown': 'Any',
        'null': 'None',
        'undefined': 'None',
        'void': 'None',
        'Date': 'datetime',
        'Record<string, any>': 'Dict[str, Any]',
        'Record<string, string>': 'Dict[str, str]',
        'object': 'Dict[str, Any]',
    }

    # Handle union types (A | B | C)
    if '|' in ts_type:
        parts = [part.strip() for part in ts_type.split('|')]

        # Special case: if it's just Type | null or Type | undefined
        if len(parts) == 2:
            if 'null' in parts or 'undefined' in parts:
                other_type = parts[0] if parts[1] in ['null', 'undefined'] else parts[1]
                return f'Optional[{ts_to_python_type(other_type)}]'

        # General union case
        converted_parts = [ts_to_python_type(part) for part in parts]
        # Filter out None values for cleaner output
        converted_parts = [p for p in converted_parts if p != 'None']

        if len(converted_parts) == 1:
            return f'Optional[{converted_parts[0]}]'
        elif len(converted_parts) > 1:
            return f'Union[{", ".join(converted_parts)}]'
        else:
            return 'None'

    # Check for array types
    if ts_type.startswith('Array<') and ts_type.endswith('>'):
        inner_type = ts_type[6:-1]
        return f'List[{ts_to_python_type(inner_type)}]'

    if ts_type.endswith('[]'):
        inner_type = ts_type[:-2]
        return f'List[{ts_to_python_type(inner_type)}]'

    # Check for branded scalars
    if '&' in ts_type and '__brand' in ts_type:
        # Extract brand name
        import re
        match = re.search(r"'__brand':\s*'([^']+)'", ts_type)
        if match:
            return match.group(1)

    return type_map.get(ts_type, ts_type)


# ============================================================================
# NODE SPECS EXTRACTION
# ============================================================================

def extract_node_specs(ast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract node specifications from TypeScript AST."""
    node_specs = []

    for file_path, file_data in ast_data.items():
        if not file_path.endswith('.spec.ts.json'):
            continue

        # Extract node type from filename
        base_name = Path(file_path).stem.replace('.spec.ts', '')
        node_type = base_name.replace('-', '_')
        node_name = snake_to_pascal(node_type)

        # Look for the specification constant
        for const in file_data.get('constants', []):
            const_name = const.get('name', '')
            # Check for spec constants (could be 'apiJobSpec' or 'apiJobSpecification')
            if const_name.endswith('Spec') or const_name.endswith('Specification'):
                spec_value = const.get('value', {})
                if not isinstance(spec_value, dict):
                    continue

                fields = []
                for field in spec_value.get('fields', []):
                    field_def = {
                        'name': field.get('name', ''),
                        'type': ts_to_python_type(field.get('type', 'any')),
                        'required': field.get('required', False),
                        'default': field.get('defaultValue'),
                        'description': field.get('description', ''),
                        'validation': field.get('validation', {}),
                    }
                    fields.append(field_def)

                node_spec = {
                    'node_type': node_type,
                    'node_name': node_name,
                    'display_name': spec_value.get('displayName', node_name),
                    'category': spec_value.get('category', ''),
                    'description': spec_value.get('description', ''),
                    'fields': fields,
                    'icon': spec_value.get('icon', ''),
                    'color': spec_value.get('color', ''),
                }
                node_specs.append(node_spec)
                break

    return node_specs


# ============================================================================
# ENUMS EXTRACTION
# ============================================================================

def extract_enums(ast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract enum definitions from TypeScript AST."""
    enums = []
    processed_enums = set()

    for file_path, file_data in ast_data.items():
        for enum in file_data.get('enums', []):
            enum_name = enum.get('name', '')

            # Skip if already processed or is frontend-only
            if enum_name in processed_enums:
                continue
            if enum_name in {'QueryOperationType', 'CrudOperation', 'QueryEntity', 'FieldPreset', 'FieldGroup'}:
                continue

            processed_enums.add(enum_name)

            # Extract enum values
            values = []
            if 'members' in enum:
                for member in enum['members']:
                    values.append({
                        'name': member.get('name', ''),
                        'value': member.get('value', member.get('name', '').lower()),
                    })
            elif 'values' in enum:
                for value in enum['values']:
                    if isinstance(value, str):
                        values.append({'name': value, 'value': value.lower()})
                    elif isinstance(value, dict):
                        values.append(value)

            enum_def = {
                'name': enum_name,
                'values': values,
                'description': enum.get('description', ''),
            }
            enums.append(enum_def)

    return enums


# ============================================================================
# INTEGRATIONS EXTRACTION
# ============================================================================

def extract_integrations(ast_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract integration configurations from TypeScript AST."""
    integrations = {
        'models': [],
        'functions': [],
        'configs': [],
    }

    for file_path, file_data in ast_data.items():
        # Check for integration files more broadly
        if 'integration' not in file_path.lower() and not file_path.endswith('integration.ts.json'):
            continue

        # Extract all interfaces from integration files
        for interface in file_data.get('interfaces', []):
            # Include all interfaces from integration files, not just those with 'Integration' in name
            model = {
                'name': interface['name'],
                'fields': [],
            }
            for prop in interface.get('properties', []):
                field = {
                    'name': prop['name'],
                    'type': ts_to_python_type(prop.get('type', 'any')),
                    'optional': prop.get('optional', prop.get('isOptional', False)),
                }
                model['fields'].append(field)
            integrations['models'].append(model)

        # Extract integration configs from constants
        for const in file_data.get('constants', []):
            if 'config' in const.get('name', '').lower():
                config = {
                    'name': const['name'],
                    'value': const.get('value', {}),
                }
                integrations['configs'].append(config)

    return integrations


# ============================================================================
# CONVERSIONS EXTRACTION
# ============================================================================

def extract_conversions(ast_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract type conversion mappings from TypeScript AST."""
    conversions = {
        'node_type_map': {},
        'type_conversions': {},
        'field_mappings': {},
    }

    for file_path, file_data in ast_data.items():
        # Check for conversion/mapping files more broadly
        if ('conversion' not in file_path.lower() and
            'mapping' not in file_path.lower() and
            not file_path.endswith('conversions.ts.json') and
            not file_path.endswith('mappings.ts.json')):
            continue

        # Extract all constants from conversion/mapping files
        for const in file_data.get('constants', []):
            const_name = const.get('name', '')
            const_value = const.get('value', {})

            # Handle NODE_TYPE_MAP
            if 'NODE_TYPE_MAP' in const_name:
                # Parse the JavaScript object literal string if needed
                if isinstance(const_value, str) and '{' in const_value:
                    # This is a JavaScript literal, extract key-value pairs
                    import re
                    matches = re.findall(r"'([^']+)':\s*NodeType\.([A-Z_]+)", const_value)
                    for key, value in matches:
                        conversions['node_type_map'][key] = value
                elif isinstance(const_value, dict):
                    for key, value in const_value.items():
                        if isinstance(value, dict):
                            conversions['node_type_map'][key] = value.get('value', key)
                        else:
                            conversions['node_type_map'][key] = str(value)

            # Handle TS_TO_PY_TYPE
            elif 'TS_TO_PY' in const_name and isinstance(const_value, dict):
                # Clean up the keys (remove quotes)
                for key, value in const_value.items():
                    clean_key = key.strip("'\"")
                    conversions['type_conversions'][clean_key] = value

            # Handle TYPE_TO_FIELD
            elif 'TYPE_TO_FIELD' in const_name and isinstance(const_value, dict):
                for key, value in const_value.items():
                    clean_key = key.strip("'\"")
                    conversions['field_mappings'][clean_key] = value

            # Handle other conversion/mapping constants
            elif 'Conversion' in const_name and isinstance(const_value, dict):
                conversions['type_conversions'].update(const_value)
            elif 'Mapping' in const_name and isinstance(const_value, dict):
                conversions['field_mappings'].update(const_value)

    return conversions


# ============================================================================
# FACTORY DATA EXTRACTION
# ============================================================================

def build_factory_data(node_specs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build factory configuration from node specifications."""
    factory_data = {
        'nodes': [],
        'node_map': {},
        'categories': set(),
    }

    for spec in node_specs:
        node_entry = {
            'type': spec['node_type'],
            'name': spec['node_name'],
            'display_name': spec['display_name'],
            'category': spec['category'],
            'fields': [field['name'] for field in spec['fields']],
        }
        factory_data['nodes'].append(node_entry)
        factory_data['node_map'][spec['node_type']] = spec['node_name']
        if spec['category']:
            factory_data['categories'].add(spec['category'])

    factory_data['categories'] = sorted(list(factory_data['categories']))
    return factory_data


# ============================================================================
# TYPESCRIPT INDEXES EXTRACTION
# ============================================================================

def extract_typescript_indexes(base_dir: Path) -> Dict[str, Any]:
    """Generate TypeScript index exports configuration."""
    indexes = {
        'node_specs': [],
        'types': [],
        'utils': [],
    }

    # Scan for TypeScript files that should be indexed
    specs_dir = base_dir / 'dipeo/models/src/node-specs'
    if specs_dir.exists():
        for spec_file in specs_dir.glob('*.spec.ts'):
            spec_name = spec_file.stem.replace('.spec', '')
            registry_key = camel_to_snake(spec_name)
            indexes['node_specs'].append({
                'file': spec_file.name,
                'name': spec_name,
                'registry_key': registry_key,
            })

    return indexes


# ============================================================================
# UNIFIED IR BUILDER
# ============================================================================

class BackendIRBuilder:
    """Unified IR builder for backend code generation."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def build_ir(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build complete backend IR from TypeScript AST."""

        # Extract all components
        node_specs = extract_node_specs(ast_data)
        enums = extract_enums(ast_data)
        integrations = extract_integrations(ast_data)
        conversions = extract_conversions(ast_data)
        factory_data = build_factory_data(node_specs)
        typescript_indexes = extract_typescript_indexes(self.base_dir)

        # Build unified models data
        unified_models = []
        for spec in node_specs:
            model = {
                'class_name': spec['node_name'],
                'display_name': spec['display_name'],
                'description': spec['description'],
                'fields': spec['fields'],
                'category': spec['category'],
                'icon': spec['icon'],
                'color': spec['color'],
            }
            unified_models.append(model)

        # Build complete IR
        ir = {
            'version': 1,
            'generated_at': datetime.now().isoformat(),

            # Core data
            'node_specs': node_specs,
            'enums': enums,
            'integrations': integrations,
            'conversions': conversions,
            'unified_models': unified_models,
            'factory_data': factory_data,
            'typescript_indexes': typescript_indexes,

            # Metadata
            'metadata': {
                'node_count': len(node_specs),
                'enum_count': len(enums),
                'integration_model_count': len(integrations['models']),
                'categories': factory_data['categories'],
            },
        }

        return ir


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def build_backend_ir(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build unified backend IR from TypeScript AST files.
    This is the main entry point called by the diagram.

    Args:
        input_data: Input from the db node - contains AST data

    Returns:
        Complete unified IR for template rendering
    """
    # Load base directory
    base_dir = Path(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))

    # Create builder instance
    builder = BackendIRBuilder(base_dir)

    # Handle input data - the db node always wraps in 'default' key
    file_dict = input_data.get('default', {})

    # Merge all AST files
    merged_ast = {}
    for file_path, ast_content in file_dict.items():
        if isinstance(ast_content, dict):
            merged_ast[file_path] = ast_content

    # Build IR
    print(f"Processing {len(merged_ast)} AST files for backend generation")
    ir = builder.build_ir(merged_ast)

    # Write IR to file for debugging/inspection
    ir_output_path = base_dir / 'projects/codegen/ir/backend_ir.json'
    ir_output_path.parent.mkdir(parents=True, exist_ok=True)
    ir_output_path.write_text(json.dumps(ir, indent=2))
    print(f"Wrote backend IR to {ir_output_path}")

    # Print summary
    print(f"Generated backend IR with:")
    print(f"  - {ir['metadata']['node_count']} node specifications")
    print(f"  - {ir['metadata']['enum_count']} enums")
    print(f"  - {ir['metadata']['integration_model_count']} integration models")
    print(f"  - {len(ir['metadata']['categories'])} categories")

    return ir


# For backward compatibility
def main(inputs: dict[str, Any]) -> dict[str, Any]:
    """Backward compatibility wrapper."""
    return build_backend_ir(inputs)
