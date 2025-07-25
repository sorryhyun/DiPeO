"""Shared node mappings and specifications loader.

This module provides centralized access to node specifications and type mappings,
eliminating the need for hard-coded mappings in individual extractors.
"""

from typing import Dict, List, Any, Optional


class NodeSpecificationsLoader:
    """Loads and provides access to node specifications from TypeScript."""
    
    def __init__(self):
        self._specs = None
        self._node_interface_map = None
        self._field_overrides = None
        self._type_mappings = None
    
    def get_node_specifications(self) -> Dict[str, Any]:
        """Load node specifications by running TypeScript code."""
        if self._specs is not None:
            return self._specs
            
        # For now, return empty specs - we'll use the AST-based approach
        # In a future enhancement, we could load actual specs from TypeScript
        self._specs = {}
        return self._specs
    
    def get_node_interface_map(self) -> Dict[str, str]:
        """Get mapping from node type to interface name."""
        if self._node_interface_map is not None:
            return self._node_interface_map
            
        # Define all known node types and their interface names
        # Standard pattern: node_type -> NodeTypeNodeData
        self._node_interface_map = {
            'start': 'StartNodeData',
            'person_job': 'PersonJobNodeData',
            'person_batch_job': 'PersonBatchJobNodeData',
            'condition': 'ConditionNodeData',
            'endpoint': 'EndpointNodeData',
            'db': 'DBNodeData',
            'code_job': 'CodeJobNodeData',
            'api_job': 'ApiJobNodeData',
            'user_response': 'UserResponseNodeData',
            'notion': 'NotionNodeData',
            'hook': 'HookNodeData',
            'template_job': 'TemplateJobNodeData',
            'json_schema_validator': 'JsonSchemaValidatorNodeData',
            'typescript_ast': 'TypescriptAstNodeData',
            'sub_diagram': 'SubDiagramNodeData'
        }
        
        return self._node_interface_map
    
    def get_field_overrides(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Get field configuration overrides for special handling."""
        if self._field_overrides is not None:
            return self._field_overrides
            
        # Define overrides for fields that need special Python handling
        self._field_overrides = {
            'person_job': {
                'fields': [
                    {
                        'ts_name': 'person',
                        'py_name': 'person_id',
                        'special': None
                    },
                    {
                        'ts_name': 'memory_config',
                        'py_name': 'memory_config',
                        'special': 'MemoryConfig(**data.get("memory_config")) if data.get("memory_config") else None'
                    },
                    {
                        'ts_name': 'memory_settings',
                        'py_name': 'memory_settings',
                        'special': 'MemorySettings(**data.get("memory_settings")) if data.get("memory_settings") else None'
                    },
                    {
                        'ts_name': 'tools',
                        'py_name': 'tools',
                        'special': '[ToolConfig(**tool) if isinstance(tool, dict) else tool for tool in data.get("tools", [])] if data.get("tools") else None'
                    }
                ]
            }
        }
        
        return self._field_overrides
    
    def get_type_mappings(self) -> Dict[str, str]:
        """Get TypeScript to Python type mappings."""
        if self._type_mappings is not None:
            return self._type_mappings
            
        self._type_mappings = {
            # Basic types
            'string': 'str',
            'number': 'int',
            'boolean': 'bool',
            'any': 'Any',
            
            # Domain types
            'PersonID': 'Optional[PersonID]',
            'NodeID': 'NodeID',
            'HandleID': 'HandleID',
            'ArrowID': 'ArrowID',
            
            # Complex types
            'MemoryConfig': 'Optional[MemoryConfig]',
            'MemorySettings': 'Optional[MemorySettings]',
            'ToolConfig[]': 'Optional[List[ToolConfig]]',
            'string[]': 'Optional[List[str]]',
            'Record<string, any>': 'Dict[str, Any]',
            'Record<string, string>': 'Dict[str, str]',
            
            # Enums
            'HookTriggerMode': 'Optional[HookTriggerMode]',
            'SupportedLanguage': 'SupportedLanguage',
            'HttpMethod': 'HttpMethod',
            'DBBlockSubType': 'DBBlockSubType',
            'NotionOperation': 'NotionOperation',
            'HookType': 'HookType',
            'DiagramFormat': 'DiagramFormat',
            'ForgettingMode': 'ForgettingMode',
            'ContentType': 'ContentType',
            'MemoryView': 'MemoryView'
        }
        
        return self._type_mappings
    
    def get_branded_types(self) -> List[str]:
        """Get list of branded types that shouldn't be generated as schemas."""
        return [
            'PersonID', 'NodeID', 'HandleID', 'ArrowID', 'NodeType',
            'SupportedLanguage', 'HttpMethod', 'DBBlockSubType', 
            'HookType', 'ForgettingMode', 'NotionOperation',
            'HookTriggerMode', 'ContentType', 'MemoryView'
        ]
    
    def get_type_to_field_mapping(self) -> Dict[str, str]:
        """Get type to UI field type mapping."""
        return {
            'string': 'text',
            'number': 'number',
            'boolean': 'checkbox',
            'PersonID': 'personSelect',
            'SupportedLanguage': 'select',
            'HttpMethod': 'select',
            'DBBlockSubType': 'select',
            'HookType': 'select',
            'ForgettingMode': 'select',
            'NotionOperation': 'select',
            'HookTriggerMode': 'select',
            'ContentType': 'select',
            'MemoryView': 'select',
            'DiagramFormat': 'select'
        }
    
    def get_base_fields(self) -> List[str]:
        """Get base fields to skip in generation."""
        return ['label', 'flipped']


# Singleton instance
_loader = NodeSpecificationsLoader()


def get_loader() -> NodeSpecificationsLoader:
    """Get the singleton loader instance."""
    return _loader


def get_python_type(ts_type: str, is_optional: bool) -> str:
    """Convert TypeScript type to Python type."""
    loader = get_loader()
    type_mappings = loader.get_type_mappings()
    
    # Clean type
    clean_type = ts_type.replace(' | null', '').replace(' | undefined', '').strip()
    
    # Handle string literal unions
    if ("'" in clean_type or '"' in clean_type) and '|' in clean_type:
        literals = []
        for lit in clean_type.split('|'):
            cleaned = lit.strip().replace("'", '').replace('"', '')
            literals.append(f'"{cleaned}"')
        literal_type = f"Literal[{', '.join(literals)}]"
        return f"Optional[{literal_type}]" if is_optional else literal_type
    
    # Check mapping
    if clean_type in type_mappings:
        return type_mappings[clean_type]
    
    # Handle arrays
    if clean_type.endswith('[]'):
        inner_type = clean_type[:-2]
        inner_py = get_python_type(inner_type, False)
        list_type = f"List[{inner_py}]"
        return f"Optional[{list_type}]" if is_optional else list_type
    
    # Handle Record types
    if clean_type.startswith('Record<'):
        return 'Dict[str, Any]'
    
    # Handle optional
    if is_optional and not clean_type.startswith('Optional['):
        return f"Optional[{clean_type}]"
    
    return clean_type


def get_field_default(field_name: str, py_type: str, is_optional: bool) -> Optional[Dict[str, Any]]:
    """Get default value configuration for a field."""
    # Handle optional fields
    if is_optional:
        return {'value': 'None', 'is_field': False}
    
    # Handle dict types
    if 'Dict[' in py_type and 'Optional[' not in py_type:
        return {'value': 'field(default_factory=dict)', 'is_field': True}
    
    # Handle list types
    if 'List[' in py_type and 'Optional[' not in py_type:
        return {'value': 'field(default_factory=list)', 'is_field': True}
    
    # Check specification defaults
    # This would need to be extended to read from specs
    
    return None