"""Save TypeScript AST output to file for downstream processing."""

import json
from pathlib import Path
from typing import Dict, Any


def save_ast_output(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Save TypeScript AST output to file for generators to read.
    
    This adapter bridges the gap between the TypeScript AST node output
    and the file-based generators that expect data in specific locations.
    """
    print("[save_ast_output] Starting save operation")
    
    # Get AST data from inputs - check various locations
    ast_data = inputs.get('ast')
    if not ast_data and 'default' in inputs:
        ast_data = inputs['default']
    
    if not ast_data:
        print("[save_ast_output] ERROR: No AST data found in inputs")
        return {'error': 'No AST data provided'}
    
    # Get base directory from environment or use current working directory
    import os
    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    
    # Ensure temp directory exists with absolute path
    temp_dir = Path(base_dir) / '.temp' / 'codegen'
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the raw AST output for debugging/backup
    ast_file = temp_dir / 'parsed_ast.json'
    try:
        with open(ast_file, 'w') as f:
            json.dump(ast_data, f, indent=2)
        print(f"[save_ast_output] Saved AST data to {ast_file}")
    except Exception as e:
        print(f"[save_ast_output] Error saving AST: {e}")
        return {'error': f'Failed to save AST: {str(e)}'}
    
    # Also save the model_data.json file that transform_ast_to_python_models creates
    # This ensures the data persists for generators that run later
    if 'models' in ast_data:
        # This is already transformed model data
        model_file = temp_dir / 'model_data.json'
        try:
            with open(model_file, 'w') as f:
                json.dump(ast_data, f, indent=2)
            print(f"[save_ast_output] Saved model data to {model_file}")
        except Exception as e:
            print(f"[save_ast_output] Error saving model data: {e}")
    
    # Pass through the data
    return ast_data