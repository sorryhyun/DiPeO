"""AST cache utilities for optimized TypeScript parsing."""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple


def load_ast_from_cache(filename: str, max_age_minutes: int = 5) -> Optional[Tuple[Dict[str, Any], str]]:
    """Load AST data and source from cache if available and fresh.
    
    Args:
        filename: Base filename without extension (e.g., 'diagram', 'execution')
        max_age_minutes: Maximum age of cache in minutes before it's considered stale
        
    Returns:
        Tuple of (ast_data, source_code) if cache exists and is fresh, None otherwise
    """
    cache_dir = Path('.temp/ast_cache')
    ast_file = cache_dir / f'{filename}_ast.json'
    source_file = cache_dir / f'{filename}_source.ts'
    metadata_file = cache_dir / 'metadata.json'
    
    # Check if cache files exist
    if not all(f.exists() for f in [ast_file, source_file, metadata_file]):
        return None
    
    # Check cache age
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        cache_time = datetime.fromisoformat(metadata['timestamp'])
        if datetime.now() - cache_time > timedelta(minutes=max_age_minutes):
            print(f"[AST Cache] Cache for {filename} is older than {max_age_minutes} minutes, ignoring")
            return None
    except Exception:
        return None
    
    # Load cached data
    try:
        with open(ast_file, 'r') as f:
            ast_data = json.load(f)
        
        with open(source_file, 'r') as f:
            source_code = f.read()
        
        print(f"[AST Cache] Loaded {filename} from cache")
        return (ast_data, source_code)
    except Exception as e:
        print(f"[AST Cache] Error loading cache for {filename}: {e}")
        return None


def load_combined_ast_from_cache(filenames: list[str], max_age_minutes: int = 5) -> Optional[Dict[str, Any]]:
    """Load multiple AST files from cache and combine them.
    
    Args:
        filenames: List of base filenames to load
        max_age_minutes: Maximum age of cache in minutes
        
    Returns:
        Combined AST data with all interfaces, types, enums, and constants
    """
    all_interfaces = []
    all_types = []
    all_enums = []
    all_constants = []
    
    for filename in filenames:
        cache_data = load_ast_from_cache(filename, max_age_minutes)
        if cache_data is None:
            return None  # If any file is missing from cache, return None
        
        ast_data, _ = cache_data
        all_interfaces.extend(ast_data.get('interfaces', []))
        all_types.extend(ast_data.get('types', []))
        all_enums.extend(ast_data.get('enums', []))
        all_constants.extend(ast_data.get('constants', []))
    
    print(f"[AST Cache] Loaded {len(filenames)} files from cache")
    return {
        'interfaces': all_interfaces,
        'types': all_types,
        'enums': all_enums,
        'constants': all_constants
    }


def clear_ast_cache():
    """Clear the AST cache directory."""
    cache_dir = Path('.temp/ast_cache')
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)
        print("[AST Cache] Cache cleared")