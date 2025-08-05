"""
Dynamic node file discovery for DiPeO code generation.
"""

import os
from pathlib import Path
from typing import List, Dict

def discover_node_data_files(inputs: dict) -> dict:
    """Discover all node data AST files dynamically."""
    base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    cache_dir = base_dir / '.temp'
    
    # Find all files matching the pattern
    node_data_files = []
    if cache_dir.exists():
        for file_path in cache_dir.glob('*_data_ast.json'):
            node_data_files.append(file_path.name)
    
    return {'node_data_files': sorted(node_data_files)}


def discover_node_spec_files(inputs: dict) -> dict:
    """Discover all node spec files dynamically."""
    base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    cache_dir = base_dir / 'temp'
    
    # Find all files matching the pattern
    spec_files = []
    if cache_dir.exists():
        for file_path in cache_dir.glob('*.spec.ts.json'):
            spec_files.append(file_path.name)
    
    return {'spec_files': sorted(spec_files)}


def discover_all_node_files(inputs: dict) -> dict:
    """Discover both node data and spec files."""
    base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    
    # Discover data files from .temp
    cache_dir = base_dir / '.temp'
    node_data_files = []
    if cache_dir.exists():
        for file_path in cache_dir.glob('*_data_ast.json'):
            node_data_files.append(file_path.name)
    
    # Discover spec files from temp
    temp_dir = base_dir / 'temp'
    spec_files = []
    if temp_dir.exists():
        for file_path in temp_dir.glob('*.spec.ts.json'):
            spec_files.append(file_path.name)
    
    return {
        'node_data_files': sorted(node_data_files),
        'spec_files': sorted(spec_files)
    }