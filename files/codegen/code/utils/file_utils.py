"""File utilities for code generation."""

import json
from pathlib import Path
from typing import Dict, Any


def load_model_data():
    """Load parsed model data from temporary storage."""
    # First try to load from the transformed model data
    model_data_file = Path('.temp/codegen/model_data.json')
    
    if model_data_file.exists():
        try:
            with open(model_data_file, 'r') as f:
                data = json.load(f)
                print(f"[load_model_data] Loaded model data with keys: {list(data.keys())}")
                return data
        except Exception as e:
            print(f"[load_model_data] Error loading model data: {e}")
    
    # Fallback to AST file if model data doesn't exist
    ast_file = Path('.temp/codegen/parsed_ast.json')
    
    if not ast_file.exists():
        print(f"[load_model_data] Neither model data nor AST file found")
        return {}
    
    try:
        with open(ast_file, 'r') as f:
            data = json.load(f)
            print(f"[load_model_data] Loaded AST data with keys: {list(data.keys())}")
            return data
    except Exception as e:
        print(f"[load_model_data] Error loading AST: {e}")
        return {}


def save_result_info(result_type: str, result_data: Dict[str, Any]):
    """Save generation result info for later combination."""
    result_dir = Path('.temp/codegen/results')
    result_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = result_dir / f"{result_type}_result.json"
    
    try:
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        print(f"[save_result_info] Saved {result_type} result to {result_file}")
    except Exception as e:
        print(f"[save_result_info] Error saving result: {e}")


def load_all_results():
    """Load all generation results for combination."""
    result_dir = Path('.temp/codegen/results')
    results = {}
    
    if not result_dir.exists():
        return results
    
    for result_file in result_dir.glob('*_result.json'):
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
                result_type = result_file.stem.replace('_result', '')
                results[result_type] = data
                print(f"[load_all_results] Loaded {result_type} result")
        except Exception as e:
            print(f"[load_all_results] Error loading {result_file}: {e}")
    
    return results