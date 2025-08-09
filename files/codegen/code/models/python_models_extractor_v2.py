"""
Simplified Python domain models data extractor for DiPeO V2.
Extracts raw model data from TypeScript AST without any type conversion.
All type conversion is handled by template filters.
"""

import json
from typing import Any, Dict, List, Optional


def parse_ast_data(data):
    """Helper function to parse AST data from various formats."""
    if isinstance(data, str):
        try:
            return json.loads(data)
        except:
            return {}
    elif isinstance(data, dict):
        # If it looks like already parsed AST data, return as-is
        if 'interfaces' in data or 'types' in data or 'enums' in data:
            return data
        return data
    else:
        return {}


def extract_models(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract raw model data from TypeScript AST without any conversion.
    
    This simplified version just extracts and organizes the data,
    leaving all type conversion to template filters.
    """
    try:
        # Support both new format (ast_files) and old format (individual inputs)
        if 'ast_files' in inputs and isinstance(inputs['ast_files'], dict):
            # New format: dictionary where keys are file paths and values are file contents
            file_dict = inputs['ast_files']
            
            # Parse each file's content
            parsed_asts = []
            for file_path, content in file_dict.items():
                ast_data = parse_ast_data(content)
                if ast_data:
                    parsed_asts.append(ast_data)
                    pass  # Remove verbose logging
            
            # Merge all definitions from parsed ASTs
            all_interfaces = []
            all_types = []
            all_enums = []
            all_consts = []
            
            for ast in parsed_asts:
                if isinstance(ast, dict):
                    # Process interfaces and map jsDoc to description
                    interfaces = ast.get('interfaces', [])
                    for interface in interfaces:
                        # Map jsDoc to description for the interface itself
                        if 'jsDoc' in interface and interface['jsDoc']:
                            interface['description'] = interface['jsDoc']
                        
                        # Map jsDoc to description for each property
                        if 'properties' in interface:
                            for prop in interface['properties']:
                                if 'jsDoc' in prop and prop['jsDoc']:
                                    prop['description'] = prop['jsDoc']
                    
                    all_interfaces.extend(interfaces)
                    all_types.extend(ast.get('types', []))
                    all_enums.extend(ast.get('enums', []))
                    all_consts.extend(ast.get('consts', []) or ast.get('constants', []))
        else:
            # Legacy format: individual inputs with specific labels
            all_interfaces = []
            all_types = []
            all_enums = []
            all_consts = []
            
            for key in ['diagram_ast', 'execution_ast', 'conversation_ast', 'node_specs_ast', 
                        'utils_ast', 'integration_ast', 'node_data_ast']:
                ast = parse_ast_data(inputs.get(key, {}))
                if isinstance(ast, dict):
                    # Process interfaces and map jsDoc to description
                    interfaces = ast.get('interfaces', [])
                    for interface in interfaces:
                        # Map jsDoc to description for the interface itself
                        if 'jsDoc' in interface and interface['jsDoc']:
                            interface['description'] = interface['jsDoc']
                        
                        # Map jsDoc to description for each property
                        if 'properties' in interface:
                            for prop in interface['properties']:
                                if 'jsDoc' in prop and prop['jsDoc']:
                                    prop['description'] = prop['jsDoc']
                    
                    all_interfaces.extend(interfaces)
                    all_types.extend(ast.get('types', []))
                    all_enums.extend(ast.get('enums', []))
                    all_consts.extend(ast.get('consts', []) or ast.get('constants', []))
        
        # print(f"AST data: {len(all_interfaces)} interfaces, {len(all_types)} types")
        
        # Filter out deprecated type aliases
        deprecated_aliases = ['ExecutionStatus', 'NodeExecutionStatus']
        filtered_types = [t for t in all_types if t.get('name') not in deprecated_aliases]
        
        # Extract branded types (simple check for __brand)
        branded_types = []
        for type_alias in filtered_types:
            alias_type = type_alias.get('type', '')
            if '& {' in alias_type and '__brand' in alias_type:
                branded_types.append(type_alias.get('name', ''))
        
        # Data prepared for template processing
        
        # Return raw data for template processing
        return {
            # Raw TypeScript data
            'interfaces': all_interfaces,
            'types': filtered_types,  # Use filtered types without deprecated aliases
            'enums': all_enums,
            'constants': all_consts,
            'branded_types': sorted(branded_types),
            
            # Counts for summary
            'interfaces_count': len(all_interfaces),
            'types_count': len(filtered_types),  # Count filtered types
            'enums_count': len(all_enums),
            'constants_count': len(all_consts),
            
            # Configuration (can be extended later)
            'config': {
                'allow_extra': False,
                'use_field_validators': True,
                'generate_type_guards': True,
            }
        }
        
    except Exception as e:
        import traceback
        error_msg = f"Error extracting model data: {str(e)}\n{traceback.format_exc()}"
        # print(error_msg)
        return {
            'error': str(e),
            'interfaces': [],
            'types': [],
            'enums': [],
            'constants': [],
            'branded_types': [],
            'config': {}
        }


def generate_summary(inputs):
    """Generate summary of Python models generation."""
    generation_result = inputs.get('generation_result', {})

    # print(f"\n=== Python Domain Models Generation Complete ===")
    # print(f"Generated {generation_result.get('interfaces_count', 0)} models")
    # print(f"Generated {generation_result.get('enums_count', 0)} enums")
    # print(f"Generated {generation_result.get('types_count', 0)} type aliases")
    # print(f"\nOutput written to: dipeo/diagram_generated_staged/domain_models.py")

    result = {
        'status': 'success',
        'message': 'Python domain models generated successfully',
        'details': generation_result
    }

    return result

# Alias for backward compatibility
main = extract_models