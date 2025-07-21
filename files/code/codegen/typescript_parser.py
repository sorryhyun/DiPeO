"""
TypeScript AST parser wrapper for DiPeO code generation.
Uses ts-morph via Node.js subprocess to parse TypeScript code.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Get project root from environment or use current working directory
PROJECT_ROOT = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
PARSER_SCRIPT = PROJECT_ROOT / 'files' / 'code' / 'codegen' / 'parse-typescript.ts'


def parse_typescript(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse TypeScript source code using ts-morph via Node.js script.
    
    Args:
        inputs: Dictionary containing:
            - source: TypeScript source code to parse
            - extractPatterns: List of patterns to extract (default: ['interface', 'type', 'enum'])
            - includeJSDoc: Whether to include JSDoc comments (default: False)
            - parseMode: 'module' or 'script' (default: 'module')
    
    Returns:
        Dictionary containing:
            - ast: Parsed AST structure
            - interfaces: List of extracted interfaces
            - types: List of extracted type aliases
            - enums: List of extracted enums
            - classes: List of extracted classes (if requested)
            - functions: List of extracted functions (if requested)
            - error: Error message if parsing failed
    """
    # Extract inputs
    source = inputs.get('source', '')
    extract_patterns = inputs.get('extractPatterns', ['interface', 'type', 'enum'])
    include_jsdoc = inputs.get('includeJSDoc', False)
    parse_mode = inputs.get('parseMode', 'module')
    
    if not source:
        return {
            'error': 'No TypeScript source code provided',
            'ast': {},
            'interfaces': [],
            'types': [],
            'enums': []
        }
    
    # Ensure parser script exists
    if not PARSER_SCRIPT.exists():
        return {
            'error': f'TypeScript parser script not found at {PARSER_SCRIPT}',
            'ast': {},
            'interfaces': [],
            'types': [],
            'enums': []
        }
    
    # Build command arguments
    cmd = ['pnpm', 'tsx', str(PARSER_SCRIPT), source]
    
    if extract_patterns:
        cmd.append(f'--patterns={",".join(extract_patterns)}')
    
    if include_jsdoc:
        cmd.append('--include-jsdoc')
    
    cmd.append(f'--mode={parse_mode}')
    
    try:
        # Run the TypeScript parser
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=30
        )
        
        if result.returncode != 0:
            return {
                'error': f'Parser failed: {result.stderr}',
                'ast': {},
                'interfaces': [],
                'types': [],
                'enums': []
            }
        
        # Parse the JSON output
        parsed_result = json.loads(result.stdout)
        
        # Ensure all expected keys are present
        return {
            'ast': parsed_result.get('ast', {}),
            'interfaces': parsed_result.get('interfaces', []),
            'types': parsed_result.get('types', []),
            'enums': parsed_result.get('enums', []),
            'classes': parsed_result.get('classes', []),
            'functions': parsed_result.get('functions', []),
            'error': parsed_result.get('error'),
            'success': not parsed_result.get('error')
        }
        
    except subprocess.TimeoutExpired:
        return {
            'error': 'TypeScript parsing timed out after 30 seconds',
            'ast': {},
            'interfaces': [],
            'types': [],
            'enums': []
        }
    except json.JSONDecodeError as e:
        return {
            'error': f'Failed to parse JSON output: {str(e)}',
            'ast': {},
            'interfaces': [],
            'types': [],
            'enums': []
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}',
            'ast': {},
            'interfaces': [],
            'types': [],
            'enums': []
        }


def parse_typescript_file(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a TypeScript file by reading it first.
    
    Args:
        inputs: Dictionary containing:
            - filePath: Path to the TypeScript file
            - extractPatterns: List of patterns to extract
            - includeJSDoc: Whether to include JSDoc comments
            - parseMode: 'module' or 'script'
    
    Returns:
        Same as parse_typescript
    """
    file_path = inputs.get('filePath', '')
    
    if not file_path:
        return {
            'error': 'No file path provided',
            'ast': {},
            'interfaces': [],
            'types': [],
            'enums': []
        }
    
    full_path = PROJECT_ROOT / file_path
    
    if not full_path.exists():
        return {
            'error': f'File not found: {full_path}',
            'ast': {},
            'interfaces': [],
            'types': [],
            'enums': []
        }
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Call parse_typescript with the file content
        return parse_typescript({
            'source': source,
            'extractPatterns': inputs.get('extractPatterns', ['interface', 'type', 'enum']),
            'includeJSDoc': inputs.get('includeJSDoc', False),
            'parseMode': inputs.get('parseMode', 'module')
        })
    
    except Exception as e:
        return {
            'error': f'Failed to read file: {str(e)}',
            'ast': {},
            'interfaces': [],
            'types': [],
            'enums': []
        }


def transform_ts_to_python(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform TypeScript AST to Python type definitions.
    
    Args:
        inputs: Dictionary containing parsed TypeScript data
    
    Returns:
        Dictionary containing Python type mappings and definitions
    """
    interfaces = inputs.get('interfaces', [])
    types = inputs.get('types', [])
    enums = inputs.get('enums', [])
    
    # Type mapping from TypeScript to Python
    type_map = {
        'string': 'str',
        'number': 'float',
        'boolean': 'bool',
        'Date': 'datetime',
        'any': 'Any',
        'unknown': 'Any',
        'void': 'None',
        'null': 'None',
        'undefined': 'Optional[Any]',
        'object': 'Dict[str, Any]',
        'Object': 'Dict[str, Any]',
        'Array': 'List',
        'Promise': 'Awaitable'
    }
    
    def map_ts_type(ts_type: str) -> str:
        """Map TypeScript type to Python type."""
        # Handle array types
        if ts_type.endswith('[]'):
            inner_type = ts_type[:-2]
            return f'List[{map_ts_type(inner_type)}]'
        
        # Handle generic types
        if '<' in ts_type and '>' in ts_type:
            base = ts_type[:ts_type.index('<')]
            inner = ts_type[ts_type.index('<')+1:ts_type.rindex('>')]
            
            if base == 'Array':
                return f'List[{map_ts_type(inner)}]'
            elif base == 'Promise':
                return f'Awaitable[{map_ts_type(inner)}]'
            elif base == 'Record':
                parts = inner.split(',', 1)
                if len(parts) == 2:
                    return f'Dict[{map_ts_type(parts[0].strip())}, {map_ts_type(parts[1].strip())}]'
            
            return f'{base}[{inner}]'
        
        # Handle union types
        if '|' in ts_type:
            parts = [map_ts_type(p.strip()) for p in ts_type.split('|')]
            return f'Union[{", ".join(parts)}]'
        
        # Handle literal types
        if ts_type.startswith('"') and ts_type.endswith('"'):
            return f'Literal[{ts_type}]'
        
        # Map basic types
        return type_map.get(ts_type, ts_type)
    
    # Transform interfaces to Python dataclasses
    python_classes = []
    for interface in interfaces:
        fields = []
        for prop in interface.get('properties', []):
            py_type = map_ts_type(prop['type'])
            if prop['optional']:
                py_type = f'Optional[{py_type}]'
            
            fields.append({
                'name': prop['name'],
                'type': py_type,
                'optional': prop['optional'],
                'readonly': prop['readonly'],
                'jsDoc': prop.get('jsDoc')
            })
        
        python_classes.append({
            'name': interface['name'],
            'fields': fields,
            'extends': interface.get('extends', []),
            'isExported': interface['isExported'],
            'jsDoc': interface.get('jsDoc')
        })
    
    # Transform type aliases
    python_types = []
    for type_alias in types:
        python_types.append({
            'name': type_alias['name'],
            'type': map_ts_type(type_alias['type']),
            'isExported': type_alias['isExported'],
            'jsDoc': type_alias.get('jsDoc')
        })
    
    # Transform enums
    python_enums = []
    for enum in enums:
        python_enums.append({
            'name': enum['name'],
            'members': enum['members'],
            'isExported': enum['isExported'],
            'jsDoc': enum.get('jsDoc')
        })
    
    return {
        'classes': python_classes,
        'types': python_types,
        'enums': python_enums,
        'imports': ['from typing import Dict, List, Optional, Union, Any, Literal, Awaitable',
                    'from datetime import datetime',
                    'from dataclasses import dataclass, field']
    }


# Export main function for code_job usage
def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for code_job node."""
    # Determine which function to call based on inputs
    if 'source' in inputs:
        return parse_typescript(inputs)
    elif 'filePath' in inputs:
        return parse_typescript_file(inputs)
    elif 'interfaces' in inputs or 'types' in inputs:
        return transform_ts_to_python(inputs)
    else:
        return {
            'error': 'Invalid inputs. Expected either "source", "filePath", or AST data.',
            'ast': {},
            'interfaces': [],
            'types': [],
            'enums': []
        }