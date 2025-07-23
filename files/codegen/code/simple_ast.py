"""Simplified AST handling - replaces complex ast_data_handler.py"""

import json
from pathlib import Path
from typing import Dict, Any

def save_ast(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Save AST data to temp file."""
    # Extract AST data - check common patterns
    ast_data = inputs.get('value', inputs.get('default', inputs))
    
    # Save to temp file
    ast_file = Path('.temp/codegen/parsed_ast.json')
    ast_file.parent.mkdir(parents=True, exist_ok=True)
    ast_file.write_text(json.dumps(ast_data, indent=2))
    
    return {
        'success': True,
        'ast_file': str(ast_file)
    }

def load_ast(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Load AST data from temp file."""
    ast_file = Path('.temp/codegen/parsed_ast.json')
    
    if not ast_file.exists():
        return {'error': f'AST file not found: {ast_file}'}
    
    return json.loads(ast_file.read_text())