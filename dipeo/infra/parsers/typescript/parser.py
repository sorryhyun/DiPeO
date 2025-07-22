"""TypeScript AST parser implementation."""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dipeo.core.ports.ast_parser_port import ASTParserPort
from dipeo.core.base.exceptions import ServiceError


class TypeScriptParser(ASTParserPort):
    """TypeScript AST parser using ts-morph via Node.js subprocess."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the TypeScript parser.
        
        Args:
            project_root: Project root directory. If not provided, uses DIPEO_BASE_DIR or cwd.
        """
        self.project_root = project_root or Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
        self.parser_script = self.project_root / 'dipeo' / 'infra' / 'parsers' / 'typescript' / 'ts_ast_extractor.ts'
    
    async def parse(
        self,
        source: str,
        extract_patterns: List[str],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Parse TypeScript source code and extract AST information.
        
        Args:
            source: The TypeScript source code to parse
            extract_patterns: List of patterns to extract (e.g., ["interface", "type", "enum"])
            options: Optional parser-specific options:
                - includeJSDoc: Whether to include JSDoc comments (default: False)
                - parseMode: 'module' or 'script' (default: 'module')
                
        Returns:
            Dictionary containing:
                - ast: The extracted AST nodes organized by pattern type
                - metadata: Additional metadata about the parsing operation
                
        Raises:
            ServiceError: If parsing fails
        """
        options = options or {}
        include_jsdoc = options.get('includeJSDoc', False)
        parse_mode = options.get('parseMode', 'module')
        
        if not source:
            raise ServiceError('No TypeScript source code provided')
        
        # Ensure parser script exists
        if not self.parser_script.exists():
            raise ServiceError(f'TypeScript parser script not found at {self.parser_script}')
        
        # Build command arguments
        cmd = ['pnpm', 'tsx', str(self.parser_script), source]
        
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
                cwd=str(self.project_root),
                timeout=30
            )
            
            if result.returncode != 0:
                raise ServiceError(f'Parser failed: {result.stderr}')
            
            # Parse the JSON output
            parsed_result = json.loads(result.stdout)
            
            # Check for parser errors
            if parsed_result.get('error'):
                raise ServiceError(f'Parser error: {parsed_result["error"]}')
            
            # Extract AST data
            ast_data = {}
            for pattern in extract_patterns:
                if pattern == 'interface':
                    ast_data['interfaces'] = parsed_result.get('interfaces', [])
                elif pattern == 'type':
                    ast_data['types'] = parsed_result.get('types', [])
                elif pattern == 'enum':
                    ast_data['enums'] = parsed_result.get('enums', [])
                elif pattern == 'class':
                    ast_data['classes'] = parsed_result.get('classes', [])
                elif pattern == 'function':
                    ast_data['functions'] = parsed_result.get('functions', [])
            
            return {
                'ast': ast_data,
                'metadata': {
                    'success': True,
                    'extractedPatterns': extract_patterns,
                    'astSummary': parsed_result.get('ast', {})
                }
            }
            
        except subprocess.TimeoutExpired:
            raise ServiceError('TypeScript parsing timed out after 30 seconds')
        except json.JSONDecodeError as e:
            raise ServiceError(f'Failed to parse JSON output: {str(e)}')
        except Exception as e:
            raise ServiceError(f'Unexpected error during TypeScript parsing: {str(e)}')
    
    async def parse_file(self, file_path: str, extract_patterns: List[str], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Parse a TypeScript file.
        
        Args:
            file_path: Path to the TypeScript file (relative to project root)
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options
            
        Returns:
            Same as parse() method
            
        Raises:
            ServiceError: If file reading or parsing fails
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            raise ServiceError(f'File not found: {full_path}')
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            return await self.parse(source, extract_patterns, options)
        
        except Exception as e:
            raise ServiceError(f'Failed to read file: {str(e)}')


def transform_ts_to_python(ast_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform TypeScript AST to Python type definitions.
    
    This is a utility function that can be used to convert TypeScript
    types to Python equivalents.
    
    Args:
        ast_data: Dictionary containing parsed TypeScript AST data
    
    Returns:
        Dictionary containing Python type mappings and definitions
    """
    interfaces = ast_data.get('interfaces', [])
    types = ast_data.get('types', [])
    enums = ast_data.get('enums', [])
    
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