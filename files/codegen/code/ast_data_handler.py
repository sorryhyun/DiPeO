"""Helper functions for handling AST data between nodes."""

import json
import os
import asyncio
from typing import Dict, Any


def save_parsed_ast(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Save parsed AST data to a temporary file and return the file path."""
    # Debug: print all inputs
    print(f"[save_parsed_ast] Received inputs keys: {list(inputs.keys())}")
    print(f"[save_parsed_ast] Input type: {type(inputs)}")
    
    # DiPeO might pass the entire node output, so check common patterns
    ast_data = {}
    
    # First check if the inputs contain the AST data directly at the top level
    if 'interfaces' in inputs or 'types' in inputs or 'enums' in inputs or 'ast' in inputs:
        ast_data = inputs
        print(f"[save_parsed_ast] Using inputs directly as AST data")
    # Check for 'value' key (common DiPeO pattern)
    elif 'value' in inputs:
        value = inputs['value']
        if isinstance(value, dict) and ('interfaces' in value or 'types' in value or 'enums' in value or 'ast' in value):
            ast_data = value
            print(f"[save_parsed_ast] Using data from 'value' key")
    # Check for 'default' key
    elif 'default' in inputs:
        ast_data = inputs.get('default', {})
        print(f"[save_parsed_ast] Using data from 'default' key")
    # Check for any other keys
    elif inputs:
        # Just use the first value if there's only one key
        if len(inputs) == 1:
            key = list(inputs.keys())[0]
            ast_data = inputs[key]
            print(f"[save_parsed_ast] Using data from '{key}' key")
    
    # If we still don't have AST data, try to use the entire inputs
    if not ast_data and inputs:
        ast_data = inputs
        print(f"[save_parsed_ast] Using entire inputs as AST data")
    
    print(f"[save_parsed_ast] AST data keys: {list(ast_data.keys()) if isinstance(ast_data, dict) else 'Not a dict'}")
    
    # Save to a temporary file
    temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_base = os.path.join(temp_dir, '.temp', 'codegen')
    
    # Create temp directory if it doesn't exist
    os.makedirs(temp_base, exist_ok=True)
    
    # Save the full AST data
    ast_file = os.path.join(temp_base, 'parsed_ast.json')
    with open(ast_file, 'w') as f:
        json.dump(ast_data, f, indent=2)
    
    print(f"[save_parsed_ast] Saved AST data to: {ast_file}")
    
    # Also save file info from previous steps if available
    file_info_file = os.path.join(temp_base, 'file_info.json')
    file_info = {
        'typescript_files': inputs.get('typescript_files', []),
        'file_count': inputs.get('file_count', 0),
        'source': inputs.get('source', ''),
        'files': inputs.get('files', [])
    }
    with open(file_info_file, 'w') as f:
        json.dump(file_info, f, indent=2)
    
    print(f"[save_parsed_ast] Saved file info to: {file_info_file}")
    
    # Return success indicator and stats
    return {
        'success': True,
        'ast_file': ast_file,
        'file_info_file': file_info_file,
        'interfaces_count': len(ast_data.get('interfaces', [])) if isinstance(ast_data, dict) else 0,
        'types_count': len(ast_data.get('types', [])) if isinstance(ast_data, dict) else 0,
        'enums_count': len(ast_data.get('enums', [])) if isinstance(ast_data, dict) else 0,
    }


def load_and_transform_ast(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Load AST data from file and transform to Python."""
    # Always use the standard temp file location
    temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_base = os.path.join(temp_dir, '.temp', 'codegen')
    ast_file = os.path.join(temp_base, 'parsed_ast.json')
    
    print(f"[load_and_transform_ast] Loading AST from: {ast_file}")
    
    if not os.path.exists(ast_file):
        print(f"[load_and_transform_ast] ERROR: AST file not found: {ast_file}")
        return {
            'error': f'AST file not found: {ast_file}'
        }
    
    # Load the AST data
    with open(ast_file, 'r') as f:
        ast_data = json.load(f)
    
    print(f"[load_and_transform_ast] Loaded AST data with keys: {list(ast_data.keys())}")
    print(f"[load_and_transform_ast] Stats: {len(ast_data.get('interfaces', []))} interfaces, "
          f"{len(ast_data.get('types', []))} types, {len(ast_data.get('enums', []))} enums")
    
    # Import and use the transformer
    try:
        from type_transformers import TypeScriptToPythonTransformer
        
        transformer = TypeScriptToPythonTransformer()
        # Pass the AST data directly as it has the expected structure
        transform_result = transformer.transform_typescript_to_python(ast_data)
        
        print(f"[load_and_transform_ast] Transformation complete")
        
        # Save transformation results to files for other nodes to read
        # Helper function to convert objects to dictionaries
        def to_serializable(obj):
            if isinstance(obj, set):
                return list(obj)  # Convert sets to lists
            elif hasattr(obj, '__dict__'):
                return to_serializable(obj.__dict__)
            elif isinstance(obj, list):
                return [to_serializable(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: to_serializable(v) for k, v in obj.items()}
            else:
                return obj
        
        # Save model data
        model_data_file = os.path.join(temp_base, 'model_data.json')
        model_data = transform_result.get('model_data', {})
        serializable_model_data = to_serializable(model_data)
        with open(model_data_file, 'w') as f:
            json.dump(serializable_model_data, f, indent=2)
        print(f"[load_and_transform_ast] Saved model data to: {model_data_file}")
        
        # Save conversion data
        conversion_data_file = os.path.join(temp_base, 'conversion_data.json')
        conversion_data = transform_result.get('conversion_data', {})
        serializable_conversion_data = to_serializable(conversion_data)
        with open(conversion_data_file, 'w') as f:
            json.dump(serializable_conversion_data, f, indent=2)
        print(f"[load_and_transform_ast] Saved conversion data to: {conversion_data_file}")
        
        # Save zod data
        zod_data_file = os.path.join(temp_base, 'zod_data.json')
        zod_data = transform_result.get('zod_data', {})
        serializable_zod_data = to_serializable(zod_data)
        with open(zod_data_file, 'w') as f:
            json.dump(serializable_zod_data, f, indent=2)
        print(f"[load_and_transform_ast] Saved zod data to: {zod_data_file}")
        
        # Save schema data
        schema_data_file = os.path.join(temp_base, 'schema_data.json')
        schema_data = transform_result.get('schema_data', {})
        serializable_schema_data = to_serializable(schema_data)
        with open(schema_data_file, 'w') as f:
            json.dump(serializable_schema_data, f, indent=2)
        print(f"[load_and_transform_ast] Saved schema data to: {schema_data_file}")
        
        # Return success indicator
        return {
            'success': True,
            'transform_complete': True,
            'models_count': len(transform_result.get('model_data', {}).get('models', [])),
            'files_saved': {
                'model_data': model_data_file,
                'conversion_data': conversion_data_file,
                'zod_data': zod_data_file,
                'schema_data': schema_data_file
            }
        }
        
    except Exception as e:
        print(f"[load_and_transform_ast] ERROR during transformation: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'error': f'Transformation failed: {str(e)}'
        }


def parse_and_save_ast(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Parse TypeScript and save AST data in one step (workaround for data flow issue)."""
    print(f"[parse_and_save_ast] Received inputs keys: {list(inputs.keys())}")
    
    # Get the source code
    source = inputs.get('source', '')
    if not source and 'default' in inputs:
        source = inputs['default'].get('source', '')
    
    if not source:
        print("[parse_and_save_ast] ERROR: No source code provided")
        return {'error': 'No source code provided'}
    
    print(f"[parse_and_save_ast] Source length: {len(source)}")
    
    # Parse the TypeScript source
    from dipeo.infra.parsers.typescript.parser import TypeScriptParser
    
    parser = TypeScriptParser()
    
    async def _parse():
        return await parser.parse(
            source=source,
            extract_patterns=['interface', 'type', 'enum', 'class'],
            options={
                'includeJSDoc': True,
                'parseMode': 'module'
            }
        )
    
    try:
        parse_result = asyncio.run(_parse())
        ast_data = parse_result.get('ast', {})
        
        print(f"[parse_and_save_ast] Parsed successfully:")
        print(f"  - Interfaces: {len(ast_data.get('interfaces', []))}")
        print(f"  - Types: {len(ast_data.get('types', []))}")
        print(f"  - Enums: {len(ast_data.get('enums', []))}")
        print(f"  - Classes: {len(ast_data.get('classes', []))}")
        
    except Exception as e:
        print(f"[parse_and_save_ast] ERROR parsing TypeScript: {str(e)}")
        return {'error': str(e)}
    
    # Save to a temporary file
    temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_base = os.path.join(temp_dir, '.temp', 'codegen')
    
    # Create temp directory if it doesn't exist
    os.makedirs(temp_base, exist_ok=True)
    
    # Save the full AST data
    ast_file = os.path.join(temp_base, 'parsed_ast.json')
    with open(ast_file, 'w') as f:
        json.dump(ast_data, f, indent=2)
    
    print(f"[parse_and_save_ast] Saved AST data to: {ast_file}")
    
    # Also save file info from previous steps if available
    file_info_file = os.path.join(temp_base, 'file_info.json')
    file_info = {
        'typescript_files': inputs.get('typescript_files', []),
        'file_count': inputs.get('file_count', 0),
        'source': source,
        'files': inputs.get('files', [])
    }
    with open(file_info_file, 'w') as f:
        json.dump(file_info, f, indent=2)
    
    print(f"[parse_and_save_ast] Saved file info to: {file_info_file}")
    
    # Return success indicator and stats
    return {
        'success': True,
        'ast_file': ast_file,
        'file_info_file': file_info_file,
        'interfaces_count': len(ast_data.get('interfaces', [])),
        'types_count': len(ast_data.get('types', [])),
        'enums_count': len(ast_data.get('enums', [])),
        'parsed_and_saved': True
    }