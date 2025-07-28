import json


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


def main(inputs):
    # Parse all AST inputs from cache
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