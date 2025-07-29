"""
Python domain models generator for DiPeO.
Consolidates all Python model generation logic into a single module.
"""

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from jinja2 import Environment, DictLoader


# ============================================================================
# Constants
# ============================================================================

# Type mapping from TypeScript to Python
TYPE_MAP = {
    'string': 'str',
    'number': 'float',
    'boolean': 'bool',
    'any': 'Any',
    'unknown': 'Any',
    'void': 'None',
    'null': 'None',
    'undefined': 'None',
    'object': 'Dict[str, Any]'
}

# Fields that should be integers instead of floats
INTEGER_FIELDS = {
    'maxIteration', 'sequence', 'messageCount', 'timeout', 'timeoutSeconds',
    'durationSeconds', 'maxTokens', 'statusCode', 'totalTokens', 'promptTokens',
    'completionTokens', 'input', 'output', 'cached', 'total', 'retries',
    'maxRetries', 'port', 'x', 'y'
}

# Branded ID types
BRANDED_IDS = {
    'NodeID', 'ArrowID', 'HandleID', 'PersonID', 'ApiKeyID', 
    'DiagramID', 'ExecutionID', 'HookID', 'TaskID'
}


# ============================================================================
# AST Data Combination
# ============================================================================

def parse_ast_data(data):
    """Helper function to parse AST data from various formats."""
    if isinstance(data, str):
        try:
            return json.loads(data)
        except:
            return {}
    elif isinstance(data, dict):
        return data
    else:
        return {}


def combine_ast_data(inputs):
    """Combine multiple AST data sources into a single structure.
    
    Handles two input formats:
    1. Legacy: Individual inputs with labels (diagram_ast, execution_ast, etc.)
    2. New: Single input 'ast_files' containing a dictionary of file paths to contents
    """
    # Check if we have the new format (single input with multiple files)
    if 'ast_files' in inputs and isinstance(inputs['ast_files'], dict):
        # New format: dictionary where keys are file paths and values are file contents
        file_dict = inputs['ast_files']
        
        # Map file names to expected AST types
        file_mapping = {
            '.temp/diagram_ast.json': 'diagram_ast',
            '.temp/execution_ast.json': 'execution_ast',
            '.temp/conversation_ast.json': 'conversation_ast',
            '.temp/node_specifications_ast.json': 'node_specs_ast',
            '.temp/utils_ast.json': 'utils_ast',
            '.temp/integration_ast.json': 'integration_ast',
            '.temp/node_data_ast.json': 'node_data_ast'
        }
        
        # Parse each file's content
        parsed_asts = []
        for file_path, content in file_dict.items():
            ast_data = parse_ast_data(content)
            if ast_data:
                parsed_asts.append(ast_data)
                # Log which file we're processing
                ast_type = file_mapping.get(file_path, file_path)
                print(f"  Processing {ast_type}: {len(ast_data.get('interfaces', []))} interfaces")
        
        # Merge all definitions from parsed ASTs
        all_interfaces = []
        all_types = []
        all_enums = []
        all_consts = []
        
        for ast in parsed_asts:
            if isinstance(ast, dict):
                all_interfaces.extend(ast.get('interfaces', []))
                all_types.extend(ast.get('types', []))
                all_enums.extend(ast.get('enums', []))
                # Handle both 'consts' and 'constants' keys for compatibility
                all_consts.extend(ast.get('consts', []) or ast.get('constants', []))
    
    else:
        # Legacy format: individual inputs with specific labels
        diagram_ast = parse_ast_data(inputs.get('diagram_ast', {}))
        execution_ast = parse_ast_data(inputs.get('execution_ast', {}))
        conversation_ast = parse_ast_data(inputs.get('conversation_ast', {}))
        node_specs_ast = parse_ast_data(inputs.get('node_specs_ast', {}))
        utils_ast = parse_ast_data(inputs.get('utils_ast', {}))
        integration_ast = parse_ast_data(inputs.get('integration_ast', {}))
        node_data_ast = parse_ast_data(inputs.get('node_data_ast', {}))
        
        # Merge all definitions
        all_interfaces = []
        all_types = []
        all_enums = []
        all_consts = []
        
        for ast in [diagram_ast, execution_ast, conversation_ast, node_specs_ast, utils_ast, integration_ast, node_data_ast]:
            if isinstance(ast, dict):
                all_interfaces.extend(ast.get('interfaces', []))
                all_types.extend(ast.get('types', []))
                all_enums.extend(ast.get('enums', []))
                # Handle both 'consts' and 'constants' keys for compatibility
                all_consts.extend(ast.get('consts', []) or ast.get('constants', []))
    
    result = {
        'interfaces': all_interfaces,
        'types': all_types,
        'enums': all_enums,
        'consts': all_consts,
        'total_definitions': len(all_interfaces) + len(all_types) + len(all_enums)
    }
    
    print(f"Combined AST data from cache:")
    print(f"  - {len(all_interfaces)} interfaces")
    print(f"  - {len(all_types)} type aliases")
    print(f"  - {len(all_enums)} enums")
    print(f"  - {len(all_consts)} constants")
    
    return result


# ============================================================================
# Type Conversion
# ============================================================================

def strip_inline_comments(type_str: str) -> str:
    """Remove inline comments from TypeScript type strings."""
    # Remove // style comments
    if '//' in type_str:
        type_str = type_str.split('//')[0].strip()
    # Remove /* */ style comments
    if '/*' in type_str and '*/' in type_str:
        type_str = re.sub(r'/\*.*?\*/', '', type_str).strip()
    return type_str


class TypeConverter:
    """Converts TypeScript types to Python types."""
    
    def __init__(self):
        self.imports: Set[Tuple[str, str]] = set()
        self.type_cache: Dict[str, str] = {}
        
    def convert(self, ts_type: str, field_name: str = '', is_optional: bool = False) -> str:
        """Convert a TypeScript type to Python type."""
        if not ts_type:
            return 'Any'
            
        # Clean inline comments first
        ts_type = strip_inline_comments(ts_type)
            
        # Check cache
        cache_key = f"{ts_type}:{field_name}:{is_optional}"
        if cache_key in self.type_cache:
            return self.type_cache[cache_key]
            
        # Remove whitespace
        ts_type = ts_type.strip()
        
        # Handle complex object types with properties
        if ts_type.startswith('{') and ts_type.endswith('}'):
            self.imports.add(('typing', 'Dict'))
            self.imports.add(('typing', 'Any'))
            result = 'Dict[str, Any]'
            self.type_cache[cache_key] = result
            return self._wrap_optional(result, is_optional)
        
        # Handle optional
        if ts_type.endswith(' | undefined') or ts_type.endswith(' | null'):
            base_type = ts_type.replace(' | undefined', '').replace(' | null', '').strip()
            result = self.convert(base_type, field_name, True)
            self.type_cache[cache_key] = result
            return result
            
        # Handle arrays
        array_match = re.match(r'^(.+)\[\]$', ts_type)
        if array_match:
            inner_type = self.convert(array_match.group(1), field_name)
            self.imports.add(('typing', 'List'))
            result = f'List[{inner_type}]'
            self.type_cache[cache_key] = result
            return self._wrap_optional(result, is_optional)
            
        # Handle Array<T>
        generic_array_match = re.match(r'^Array<(.+)>$', ts_type)
        if generic_array_match:
            inner_type = self.convert(generic_array_match.group(1), field_name)
            self.imports.add(('typing', 'List'))
            result = f'List[{inner_type}]'
            self.type_cache[cache_key] = result
            return self._wrap_optional(result, is_optional)
            
        # Handle Map/Record types
        map_match = re.match(r'^(Map|Record)<([^,]+),\s*(.+)>$', ts_type)
        if map_match:
            key_type = 'str' if map_match.group(2) in BRANDED_IDS or map_match.group(2) == 'string' else self.convert(map_match.group(2))
            value_type = self.convert(map_match.group(3))
            self.imports.add(('typing', 'Dict'))
            result = f'Dict[{key_type}, {value_type}]'
            self.type_cache[cache_key] = result
            return self._wrap_optional(result, is_optional)
            
        # Handle literal types (single quoted string)
        if re.match(r'^["\'].*["\']$', ts_type) and '|' not in ts_type:
            self.imports.add(('typing', 'Literal'))
            # Convert single/double quotes to double quotes for Python
            literal_value = ts_type.strip("'\"")
            result = f'Literal["{literal_value}"]'
            self.type_cache[cache_key] = result
            return self._wrap_optional(result, is_optional)
            
        # Handle union types (excluding optional unions handled above)
        if '|' in ts_type and not ts_type.startswith('('):
            parts = [strip_inline_comments(p.strip()) for p in ts_type.split('|')]
            # Filter out undefined/null
            parts = [p for p in parts if p not in ['undefined', 'null']]
            if not parts:
                return 'None'
            if len(parts) == 1:
                return self.convert(parts[0], field_name, is_optional)
            
            # Check if all parts are string literals
            all_literals = all(re.match(r'^["\'].*["\']$', p.strip()) for p in parts)
            
            # Check if all parts are numeric literals
            all_numeric = all(p.strip().isdigit() for p in parts)
            
            if all_literals:
                # Convert to Literal with multiple values
                self.imports.add(('typing', 'Literal'))
                literal_values = [p.strip().strip("'\"") for p in parts]
                # Format as Literal["value1", "value2", ...]
                quoted_values = ', '.join(f'"{v}"' for v in literal_values)
                result = f'Literal[{quoted_values}]'
            elif all_numeric:
                # Convert numeric literals to Literal
                self.imports.add(('typing', 'Literal'))
                numeric_values = ', '.join(p.strip() for p in parts)
                result = f'Literal[{numeric_values}]'
            else:
                # Convert each part
                converted_parts = []
                for part in parts:
                    converted = self.convert(part, field_name)
                    if converted not in converted_parts:
                        converted_parts.append(converted)
                        
                self.imports.add(('typing', 'Union'))
                result = f'Union[{", ".join(converted_parts)}]'
            
            self.type_cache[cache_key] = result
            return self._wrap_optional(result, is_optional)
            
        # Handle branded types
        if ts_type in BRANDED_IDS:
            result = ts_type
            self.type_cache[cache_key] = result
            return self._wrap_optional(result, is_optional)
            
        # Handle basic types
        if ts_type in TYPE_MAP:
            # Special handling for number fields that should be int
            if ts_type == 'number' and field_name in INTEGER_FIELDS:
                result = 'int'
            else:
                result = TYPE_MAP[ts_type]
                
            if result == 'Any':
                self.imports.add(('typing', 'Any'))
            elif result == 'Dict[str, Any]':
                self.imports.add(('typing', 'Dict'))
                self.imports.add(('typing', 'Any'))
                
            self.type_cache[cache_key] = result
            return self._wrap_optional(result, is_optional)
            
        # Default to the type name (likely a custom type)
        result = ts_type
        self.type_cache[cache_key] = result
        return self._wrap_optional(result, is_optional)
        
    def _wrap_optional(self, type_str: str, is_optional: bool) -> str:
        """Wrap a type in Optional if needed."""
        if is_optional and not type_str.startswith('Optional['):
            self.imports.add(('typing', 'Optional'))
            return f'Optional[{type_str}]'
        return type_str


# ============================================================================
# Processing and Template Rendering
# ============================================================================

def process_ast_data(ast_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process TypeScript AST data into structured format for template."""
    converter = TypeConverter()
    
    # Process interfaces into models
    models = []
    for interface in ast_data.get('interfaces', []):
        fields = []
        for prop in interface.get('properties', []):
            # Special handling for empty object types
            prop_type = prop.get('type', 'Any')
            if prop_type == '{}':
                prop_type = 'object'
            
            field_type = converter.convert(
                prop_type, 
                prop['name'], 
                prop.get('optional', False)
            )
            
            # Replace empty {} with proper type annotations
            if field_type == '{}':
                # Determine proper type based on field name
                if 'node' in prop['name'].lower() and 'indices' in prop['name'].lower():
                    field_type = 'List[int]'
                    converter.imports.add(('typing', 'List'))
                elif any(x in prop['name'].lower() for x in ['tools', 'tags', 'args', 'env', 'params', 'headers']):
                    field_type = 'List[str]'
                    converter.imports.add(('typing', 'List'))
                elif prop['name'].lower() in ['messages', 'nodes', 'handles', 'arrows', 'persons', 'fields', 'inputs', 'outputs', 'examples']:
                    # These are typically lists
                    field_type = 'List[Any]'
                    converter.imports.add(('typing', 'List'))
                    converter.imports.add(('typing', 'Any'))
                else:
                    field_type = 'Dict[str, Any]'
                    converter.imports.add(('typing', 'Dict'))
                    converter.imports.add(('typing', 'Any'))
            
            fields.append({
                'name': prop['name'],
                'type': field_type,
                'optional': prop.get('optional', False),
                'description': prop.get('description', '')
            })
            
        extends_list = interface.get('extends', [])
        extends_value = extends_list[0] if extends_list else None
        
        models.append({
            'name': interface['name'],
            'extends': extends_value,
            'description': interface.get('description', ''),
            'fields': fields
        })
    
    # Process enums
    enums = []
    for enum in ast_data.get('enums', []):
        members = []
        for member in enum.get('members', []):
            members.append({
                'name': member['name'].replace('-', '_'),
                'value': member['value']
            })
        enums.append({
            'name': enum['name'],
            'description': enum.get('description', ''),
            'members': members
        })
    
    # Process type aliases
    type_aliases = []
    deferred_aliases = []  # Aliases that need forward references
    branded_types = []
    
    # Get all model names for forward reference checking
    model_names = {interface['name'] for interface in ast_data.get('interfaces', [])}
    
    for type_alias in ast_data.get('types', []):
        alias_name = type_alias.get('name', '')
        alias_type = type_alias.get('type', '')
        
        
        # Check if it's a branded type
        if '& {' in alias_type and '__brand' in alias_type:
            branded_types.append(alias_name)
        else:
            # Convert the type alias
            py_type = converter.convert(alias_type)
            
            # Skip if it's the same as the name (to avoid NodeID = NodeID)
            if py_type != alias_name:
                alias_dict = {
                    'name': alias_name,
                    'type': py_type
                }
                
                # Check if this alias references a model that will be defined later
                if py_type in model_names:
                    deferred_aliases.append(alias_dict)
                else:
                    type_aliases.append(alias_dict)
    
    # Merge branded types with predefined list
    all_branded = sorted(list(set(branded_types) | BRANDED_IDS))
    
    # Get unique imports
    imports = sorted(list(converter.imports))
    
    return {
        'models': models,
        'enums': enums,
        'type_aliases': type_aliases,
        'deferred_aliases': deferred_aliases,  # Aliases that reference models
        'branded_ids': all_branded,
        'imports': imports,
        'allow_extra': False  # Can be made configurable
    }


# ============================================================================
# Main Functions (called by diagram nodes)
# ============================================================================

def generate_python_models(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for Python models generation."""
    try:
        # Debug: Print input structure
        print(f"[Python Models Generator] Input keys: {list(inputs.keys())}")
        print(f"[Python Models Generator] Input types: {[(k, type(v).__name__) for k, v in inputs.items()]}")
        
        ast_data = inputs.get('ast_data', {})
        template_content = inputs.get('template_content', '')
        
        # Debug: Print what we got
        print(f"[Python Models Generator] ast_data type: {type(ast_data).__name__}")
        if isinstance(ast_data, dict):
            print(f"[Python Models Generator] ast_data keys: {list(ast_data.keys())}")
        
        if not ast_data:
            raise ValueError("No AST data provided")
        
        if not template_content:
            raise ValueError("No template content provided")
        
        # Process AST data
        template_data = process_ast_data(ast_data)
        
        # Set up Jinja2 environment
        env = Environment(loader=DictLoader({'template': template_content}))
        
        # Add custom filters
        env.filters['quote'] = lambda s: f'"{s}"'
        
        # Render template
        template = env.get_template('template')
        generated_code = template.render(**template_data)
        
        return {
            'generated_code': generated_code,
            'status': 'success',
            'models_count': len(template_data['models']),
            'enums_count': len(template_data['enums']),
            'type_aliases_count': len(template_data['type_aliases'])
        }
    except Exception as e:
        import traceback
        error_msg = f"Error in python_models generator: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return {
            'generated_code': error_msg,
            'status': 'error',
            'error': str(e)
        }


def generate_summary(inputs):
    """Generate summary of Python models generation."""
    generation_result = inputs.get('generation_result', {})
    
    print(f"\n=== Python Domain Models Generation Complete ===")
    print(f"Generated {generation_result.get('models_count', 0)} models")
    print(f"Generated {generation_result.get('enums_count', 0)} enums")
    print(f"Generated {generation_result.get('type_aliases_count', 0)} type aliases")
    print(f"\nOutput written to: dipeo/diagram_generated_staged/domain_models.py")
    
    result = {
        'status': 'success',
        'message': 'Python domain models generated successfully',
        'details': generation_result
    }
    
    return result


# Backward compatibility aliases
main = combine_ast_data