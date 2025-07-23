"""Domain model functions - refactored modular version.

This module provides backwards compatibility by re-exporting functions
from their new modular locations.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import readers
from readers.glob_files import glob_typescript_files
from readers.typescript_reader import read_typescript_files
from readers.source_extractor import extract_source

# Import generators
from generators.pydantic_generator import generate_pydantic_models
from generators.conversions_generator import generate_conversions
from generators.zod_generator import generate_zod_schemas
from generators.graphql_generator import generate_graphql_schema
from generators.json_schema_generator import generate_json_schemas

# Import adapters
from adapters.extract_source import extract_source_for_ast

# Import missing functions
from utils.file_utils import load_all_results


def combine_generation_results(inputs):
    """Combine all generation results into a single output."""
    print("[combine_generation_results] Combining all results")
    
    # Load all saved results
    all_results = load_all_results()
    
    # Create combined output
    combined = {
        'generated_files': [],
        'file_count': 0
    }
    
    for result_type, result_data in all_results.items():
        if 'path' in result_data:
            combined['generated_files'].append({
                'path': result_data['path'],
                'type': result_data.get('type', result_type)
            })
            combined['file_count'] += 1
    
    print(f"[combine_generation_results] Combined {combined['file_count']} files")
    return combined


def verify_generated_code(inputs):
    """Verify that generated code is syntactically valid."""
    print("[verify_generated_code] Starting verification")
    
    results = {
        'errors': [],
        'warnings': [],
        'valid': True
    }
    
    # Get list of generated files from inputs
    generated_files = inputs.get('generated_files', [])
    
    for file_info in generated_files:
        file_path = file_info.get('path')
        if not file_path:
            continue
            
        if file_path.endswith('.py'):
            # Verify Python syntax
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
                compile(code, file_path, 'exec')
                print(f"[verify_generated_code] ✓ {file_path} is valid Python")
            except SyntaxError as e:
                error_msg = f"{file_path}: {e.msg} at line {e.lineno}"
                results['errors'].append(error_msg)
                results['valid'] = False
                print(f"[verify_generated_code] ✗ {error_msg}")
            except Exception as e:
                error_msg = f"{file_path}: {str(e)}"
                results['errors'].append(error_msg) 
                results['valid'] = False
                print(f"[verify_generated_code] ✗ {error_msg}")
    
    results['verification_results'] = results
    return results


# Export all functions for backward compatibility
__all__ = [
    'glob_typescript_files',
    'read_typescript_files',
    'extract_source',
    'extract_source_for_ast',
    'generate_pydantic_models',
    'generate_conversions',
    'generate_zod_schemas',
    'generate_graphql_schema',
    'generate_json_schemas',
    'combine_generation_results',
    'verify_generated_code',
]