#!/usr/bin/env python3
"""
Migration script to convert TypeScript node interfaces to JSON specifications.
This script parses TypeScript interfaces and generates JSON node specifications
for the codegen system.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FieldInfo:
    name: str
    type: str
    required: bool
    default_value: Any = None
    is_array: bool = False
    is_nullable: bool = False
    enum_values: Optional[List[str]] = None


@dataclass
class NodeInfo:
    node_type: str
    interface_name: str
    fields: List[FieldInfo]


class TypeScriptParser:
    """Simple TypeScript interface parser for node data interfaces."""
    
    def __init__(self, content: str):
        self.content = content
        self.enums = self._extract_enums()
        
    def _extract_enums(self) -> Dict[str, List[str]]:
        """Extract enum definitions from TypeScript content."""
        enums = {}
        enum_pattern = r'export\s+enum\s+(\w+)\s*\{([^}]+)\}'
        
        for match in re.finditer(enum_pattern, self.content, re.DOTALL):
            enum_name = match.group(1)
            enum_body = match.group(2)
            
            # Extract enum values
            values = []
            for line in enum_body.strip().split('\n'):
                if '=' in line:
                    # Extract the string value after =
                    value_match = re.search(r'=\s*["\']([^"\']+)["\']', line)
                    if value_match:
                        values.append(value_match.group(1))
                
            enums[enum_name] = values
            
        return enums
    
    def parse_interface(self, interface_name: str) -> Optional[List[FieldInfo]]:
        """Parse a specific interface and return its fields."""
        # Find the interface definition
        pattern = rf'export\s+interface\s+{interface_name}\s+extends\s+\w+\s*\{{([^}}]+)\}}'
        match = re.search(pattern, self.content, re.DOTALL)
        
        if not match:
            return None
            
        interface_body = match.group(1)
        fields = []
        
        # Parse each field
        field_pattern = r'^\s*(\w+)(\?)?\s*:\s*(.+?)(?:;|$)'
        
        for line in interface_body.strip().split('\n'):
            field_match = re.match(field_pattern, line.strip())
            if field_match:
                field_name = field_match.group(1)
                is_optional = field_match.group(2) == '?'
                field_type = field_match.group(3).strip()
                
                field_info = self._parse_field_type(field_name, field_type, not is_optional)
                if field_info:
                    fields.append(field_info)
                    
        return fields
    
    def _parse_field_type(self, name: str, type_str: str, required: bool) -> Optional[FieldInfo]:
        """Parse a field type string into FieldInfo."""
        # Clean up the type string
        type_str = type_str.strip()
        
        # Check for nullable types
        is_nullable = ' | null' in type_str
        type_str = type_str.replace(' | null', '').strip()
        
        # Check for array types
        is_array = type_str.endswith('[]')
        if is_array:
            type_str = type_str[:-2].strip()
            
        # Check for union types with literals
        if '|' in type_str and "'" in type_str:
            # Extract literal values
            values = re.findall(r"'([^']+)'", type_str)
            return FieldInfo(
                name=name,
                type='enum',
                required=required,
                is_nullable=is_nullable,
                enum_values=values
            )
            
        # Map TypeScript types to JSON spec types
        type_mapping = {
            'string': 'string',
            'number': 'number',
            'boolean': 'boolean',
            'any': 'object',
            'Record<string, string>': 'object',
            'Record<string, any>': 'object',
            'MemorySettings': 'object',
            'MemoryConfig': 'object',
            'ToolConfig': 'object',
            'PersonID': 'string',
            'HttpMethod': 'enum',
        }
        
        # Check if it's an enum
        if type_str in self.enums:
            return FieldInfo(
                name=name,
                type='enum',
                required=required,
                is_array=is_array,
                is_nullable=is_nullable,
                enum_values=self.enums[type_str]
            )
            
        # Get the mapped type
        json_type = type_mapping.get(type_str, 'string')
        
        return FieldInfo(
            name=name,
            type=json_type,
            required=required,
            is_array=is_array,
            is_nullable=is_nullable
        )


class NodeSpecGenerator:
    """Generate JSON node specifications from TypeScript interfaces."""
    
    # Node metadata mappings
    NODE_METADATA = {
        'start': {
            'displayName': 'Start Node',
            'category': 'control',
            'icon': '🚀',
            'color': '#4CAF50',
            'description': 'Entry point for diagram execution'
        },
        'person_job': {
            'displayName': 'Person Job',
            'category': 'ai',
            'icon': '🤖',
            'color': '#2196F3',
            'description': 'Execute tasks using AI language models'
        },
        'condition': {
            'displayName': 'Condition',
            'category': 'control',
            'icon': '🔀',
            'color': '#FF9800',
            'description': 'Conditional branching based on expressions'
        },
        'code_job': {
            'displayName': 'Code Job',
            'category': 'compute',
            'icon': '💻',
            'color': '#9C27B0',
            'description': 'Execute custom code functions'
        },
        'api_job': {
            'displayName': 'API Job',
            'category': 'integration',
            'icon': '🌐',
            'color': '#00BCD4',
            'description': 'Make HTTP API requests'
        },
        'endpoint': {
            'displayName': 'End Node',
            'category': 'control',
            'icon': '🏁',
            'color': '#F44336',
            'description': 'Exit point for diagram execution'
        },
        'db': {
            'displayName': 'Database',
            'category': 'data',
            'icon': '🗄️',
            'color': '#795548',
            'description': 'Database operations'
        },
        'user_response': {
            'displayName': 'User Response',
            'category': 'interaction',
            'icon': '💬',
            'color': '#E91E63',
            'description': 'Collect user input'
        },
        'template_job': {
            'displayName': 'Template Job',
            'category': 'compute',
            'icon': '📝',
            'color': '#3F51B5',
            'description': 'Process templates with data'
        },
        'shell_job': {
            'displayName': 'Shell Job',
            'category': 'compute',
            'icon': '🐚',
            'color': '#009688',
            'description': 'Execute shell commands'
        },
        'json_schema_validator': {
            'displayName': 'JSON Schema Validator',
            'category': 'validation',
            'icon': '✓',
            'color': '#8BC34A',
            'description': 'Validate data against JSON schema'
        },
    }
    
    def generate_ui_config(self, field: FieldInfo) -> Dict[str, Any]:
        """Generate UI configuration based on field type."""
        ui_config = {}
        
        if field.type == 'string':
            if 'prompt' in field.name.lower():
                ui_config['inputType'] = 'textarea'
                ui_config['placeholder'] = 'Enter prompt template...'
            elif 'url' in field.name.lower():
                ui_config['inputType'] = 'url'
                ui_config['placeholder'] = 'https://example.com'
            elif 'path' in field.name.lower():
                ui_config['inputType'] = 'text'
                ui_config['placeholder'] = '/path/to/file'
            else:
                ui_config['inputType'] = 'text'
                
        elif field.type == 'number':
            ui_config['inputType'] = 'number'
            if 'timeout' in field.name.lower():
                ui_config['min'] = 0
                ui_config['max'] = 3600
            elif 'max' in field.name.lower():
                ui_config['min'] = 1
                
        elif field.type == 'boolean':
            ui_config['inputType'] = 'checkbox'
            
        elif field.type == 'enum':
            ui_config['inputType'] = 'select'
            
        elif field.type == 'object':
            ui_config['inputType'] = 'code'
            ui_config['language'] = 'json'
            ui_config['collapsible'] = True
            
        return ui_config
    
    def generate_field_spec(self, field: FieldInfo) -> Dict[str, Any]:
        """Generate field specification."""
        spec = {
            'name': field.name,
            'type': 'array' if field.is_array else field.type,
            'required': field.required,
            'description': f'{field.name.replace("_", " ").title()} configuration'
        }
        
        if field.default_value is not None:
            spec['defaultValue'] = field.default_value
            
        # For enum fields, add values array
        if field.enum_values:
            spec['values'] = field.enum_values
            
        if field.is_array and field.type != 'array':
            spec['validation'] = {'itemType': field.type}
            
        ui_config = self.generate_ui_config(field)
        if ui_config:
            spec['uiConfig'] = ui_config
            
        return spec
    
    def generate_node_spec(self, node_type: str, fields: List[FieldInfo]) -> Dict[str, Any]:
        """Generate complete node specification."""
        metadata = self.NODE_METADATA.get(node_type, {
            'displayName': node_type.replace('_', ' ').title(),
            'category': 'utility',
            'icon': '📦',
            'color': '#607D8B',
            'description': f'{node_type} node'
        })
        
        spec = {
            'nodeType': node_type,
            'displayName': metadata['displayName'],
            'category': metadata['category'],
            'icon': metadata['icon'],
            'color': metadata['color'],
            'description': metadata['description'],
            'fields': [self.generate_field_spec(field) for field in fields],
            'handles': {
                'inputs': ['in'],
                'outputs': ['out'] if node_type != 'endpoint' else []
            },
            'outputs': {
                'result': {
                    'type': 'any',
                    'description': 'Node execution result'
                }
            } if node_type != 'endpoint' else {},
            'execution': {
                'timeout': 300,
                'retryable': True,
                'maxRetries': 3
            }
        }
        
        # Special handling for condition nodes
        if node_type == 'condition':
            spec['handles']['outputs'] = ['true', 'false']
            spec['outputs'] = {
                'true': {'type': 'any', 'description': 'Output when condition is true'},
                'false': {'type': 'any', 'description': 'Output when condition is false'}
            }
            
        return spec


def main():
    """Main migration function."""
    # Define node type to interface mappings
    node_mappings = {
        'start': 'StartNodeData',
        'person_job': 'PersonJobNodeData',
        'condition': 'ConditionNodeData',
        'code_job': 'CodeJobNodeData',
        'api_job': 'ApiJobNodeData',
        'endpoint': 'EndpointNodeData',
        'db': 'DBNodeData',
        'user_response': 'UserResponseNodeData',
        'template_job': 'TemplateJobNodeData',
        'shell_job': 'ShellJobNodeData',
        'json_schema_validator': 'JsonSchemaValidatorNodeData',
    }
    
    # Read the TypeScript file
    diagram_path = Path('/home/soryhyun/DiPeO/dipeo/models/src/diagram.ts')
    content = diagram_path.read_text()
    
    # Parse interfaces and generate specs
    parser = TypeScriptParser(content)
    generator = NodeSpecGenerator()
    
    output_dir = Path('/home/soryhyun/DiPeO/files/codegen/specifications/nodes')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_specs = []
    
    for node_type, interface_name in node_mappings.items():
        print(f"Processing {node_type} ({interface_name})...")
        
        fields = parser.parse_interface(interface_name)
        if fields is not None:
            spec = generator.generate_node_spec(node_type, fields)
            
            # Write the specification
            output_path = output_dir / f'{node_type}.json'
            with open(output_path, 'w') as f:
                json.dump(spec, f, indent=2)
                
            generated_specs.append(node_type)
            print(f"  ✓ Generated {output_path}")
        else:
            print(f"  ✗ Could not parse interface {interface_name}")
    
    print(f"\nGenerated {len(generated_specs)} specifications:")
    for spec in generated_specs:
        print(f"  - {spec}")


if __name__ == '__main__':
    main()