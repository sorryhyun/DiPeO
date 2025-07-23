"""TypeScript to Python type transformers for code generation."""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class PythonImport:
    """Represents a Python import statement."""
    module: str
    items: List[str] = field(default_factory=list)
    is_type_import: bool = False


@dataclass
class TypeInfo:
    """Information about a transformed type."""
    python_type: str
    imports: List[PythonImport] = field(default_factory=list)
    is_optional: bool = False
    is_list: bool = False
    is_dict: bool = False
    is_union: bool = False
    union_types: List[str] = field(default_factory=list)


@dataclass
class ModelInfo:
    """Information about a Python model."""
    name: str
    type: str  # 'class', 'enum', 'type_alias'
    fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    bases: List[str] = field(default_factory=list)
    imports: Set[PythonImport] = field(default_factory=set)
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    methods: List[Dict[str, Any]] = field(default_factory=list)
    enum_values: List[Tuple[str, Any]] = field(default_factory=list)


class TypeScriptToPythonTransformer:
    """Transforms TypeScript AST to Python models."""
    
    # TypeScript to Python type mappings
    TYPE_MAPPINGS = {
        'string': 'str',
        'number': 'float',
        'boolean': 'bool',
        'any': 'Any',
        'unknown': 'Any',
        'void': 'None',
        'null': 'None',
        'undefined': 'None',
        'object': 'Dict[str, Any]',
        'Function': 'Callable',
        'Date': 'datetime',
        'RegExp': 'Pattern[str]',
        'Promise': 'Awaitable',
        'Array': 'List',
        'Record': 'Dict',
        'Map': 'Dict',
        'Set': 'Set',
    }
    
    # DiPeO specific branded types
    BRANDED_TYPES = {
        'NodeID': 'NodeID',
        'ArrowID': 'ArrowID',
        'PersonID': 'PersonID',
        'Handle': 'Handle',
        'NodeType': 'NodeType',
        'ExecutionStatus': 'ExecutionStatus',
        'DiagramFormat': 'DiagramFormat',
    }
    
    def __init__(self):
        self.imports: Set[PythonImport] = set()
        self.models: List[ModelInfo] = []
        self.type_aliases: Dict[str, str] = {}
        
    def transform_typescript_to_python(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for transformation."""
        # The typescript_ast node outputs parsed data directly with keys: interfaces, types, enums, classes, functions
        # DiPeO may pass data under 'default' key or directly
        parsed_ast = inputs
        if 'default' in inputs and isinstance(inputs['default'], dict):
            # If wrapped in default, use that
            parsed_ast = inputs['default']
        
        print(f"[transform_typescript_to_python] Received inputs keys: {list(inputs.keys())}")
        print(f"[transform_typescript_to_python] Using parsed_ast keys: {list(parsed_ast.keys())}")
        
        # Debug: print the actual content
        if 'default' in parsed_ast:
            print(f"[transform_typescript_to_python] Content of default: {list(parsed_ast['default'].keys()) if isinstance(parsed_ast['default'], dict) else type(parsed_ast['default'])}")
        
        # Process each parsed item type directly
        if 'interfaces' in parsed_ast and isinstance(parsed_ast['interfaces'], list):
            for interface in parsed_ast['interfaces']:
                self._transform_interface(interface)
                
        if 'types' in parsed_ast and isinstance(parsed_ast['types'], list):
            for type_alias in parsed_ast['types']:
                self._transform_type_alias(type_alias)
                
        if 'enums' in parsed_ast and isinstance(parsed_ast['enums'], list):
            for enum in parsed_ast['enums']:
                self._transform_enum(enum)
                
        if 'classes' in parsed_ast and isinstance(parsed_ast['classes'], list):
            for cls in parsed_ast['classes']:
                self._transform_class(cls)
        
        # Prepare output data for templates
        # Each key becomes a handle that can be referenced in connections
        result = {
            'model_data': {
                'models': self.models,
                'imports': self._consolidate_imports(),
                'type_aliases': self.type_aliases,
            },
            'conversion_data': {
                'models': [m for m in self.models if m.type == 'class'],
                'enums': [m for m in self.models if m.type == 'enum'],
            },
            'zod_data': {
                'models': self.models,
                'imports': self._get_zod_imports(),
            },
            'schema_data': {
                'models': self.models,
            }
        }
        
        # Add 'default' key containing all data for DiPeO
        result['default'] = result.copy()
        
        print(f"[transform_typescript_to_python] Generated {len(self.models)} models")
        print(f"Output handles: {list(result.keys())}")
        
        return result
    
    def _transform_interface(self, interface: Dict[str, Any]) -> None:
        """Transform TypeScript interface to Python dataclass."""
        model = ModelInfo(
            name=interface['name'],
            type='class',
            bases=['BaseModel'],  # Using Pydantic
            decorators=[],
        )
        
        # Add docstring if available
        if 'comment' in interface:
            model.docstring = interface['comment']
        
        # Transform properties
        for prop in interface.get('properties', []):
            field_info = self._transform_property(prop)
            model.fields[prop['name']] = field_info
            
            # Collect imports from field types
            if 'imports' in field_info:
                for imp in field_info['imports']:
                    self.imports.add(PythonImport(**imp))
        
        # Add type validation methods if needed
        if self._needs_validators(model):
            model.methods.extend(self._generate_validators(model))
        
        self.models.append(model)
    
    def _transform_type_alias(self, type_alias: Dict[str, Any]) -> None:
        """Transform TypeScript type alias."""
        name = type_alias['name']
        ts_type = type_alias.get('type', 'Any')
        
        # Handle union types
        if '|' in ts_type:
            union_types = [t.strip() for t in ts_type.split('|')]
            python_types = [self._map_type(t).python_type for t in union_types]
            self.type_aliases[name] = f"Union[{', '.join(python_types)}]"
            self.imports.add(PythonImport(module='typing', items=['Union'], is_type_import=True))
        else:
            type_info = self._map_type(ts_type)
            self.type_aliases[name] = type_info.python_type
            self.imports.update(type_info.imports)
    
    def _transform_enum(self, enum: Dict[str, Any]) -> None:
        """Transform TypeScript enum to Python Enum."""
        model = ModelInfo(
            name=enum['name'],
            type='enum',
            bases=['str', 'Enum'],  # String enum for JSON serialization
        )
        
        # Transform enum members
        for member in enum.get('members', []):
            # Handle both string and numeric enums
            value = member.get('value', member['name'])
            model.enum_values.append((member['name'], value))
        
        self.imports.add(PythonImport(module='enum', items=['Enum'], is_type_import=False))
        self.models.append(model)
    
    def _transform_class(self, cls: Dict[str, Any]) -> None:
        """Transform TypeScript class to Python class."""
        model = ModelInfo(
            name=cls['name'],
            type='class',
            bases=self._get_class_bases(cls),
        )
        
        # Transform properties and methods
        for prop in cls.get('properties', []):
            field_info = self._transform_property(prop)
            model.fields[prop['name']] = field_info
        
        # Add methods
        for method in cls.get('methods', []):
            model.methods.append(self._transform_method(method))
        
        self.models.append(model)
    
    def _transform_property(self, prop: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a TypeScript property to Python field info."""
        ts_type = prop.get('type', 'Any')
        type_info = self._map_type(ts_type)
        
        field_info = {
            'name': prop['name'],
            'type': type_info.python_type,
            'required': not prop.get('optional', False),
            'default': prop.get('initializer'),
            'description': prop.get('comment', ''),
            'imports': [imp.__dict__ for imp in type_info.imports],
        }
        
        # Handle Field attributes for Pydantic
        field_attrs = []
        if field_info['description']:
            field_attrs.append(f'description="{field_info["description"]}"')
        if not field_info['required']:
            field_attrs.append('default=None')
        elif field_info['default'] is not None:
            field_attrs.append(f'default={field_info["default"]}')
            
        if field_attrs:
            field_info['field_definition'] = f"Field({', '.join(field_attrs)})"
            self.imports.add(PythonImport(module='pydantic', items=['Field'], is_type_import=False))
        
        return field_info
    
    def _map_type(self, ts_type: str) -> TypeInfo:
        """Map TypeScript type to Python type."""
        type_info = TypeInfo(python_type='Any')
        
        # Clean up the type string
        ts_type = ts_type.strip()
        
        # Check for optional type (Type | undefined)
        if '| undefined' in ts_type or '| null' in ts_type:
            type_info.is_optional = True
            ts_type = ts_type.replace('| undefined', '').replace('| null', '').strip()
        
        # Check for array types
        if ts_type.endswith('[]'):
            type_info.is_list = True
            inner_type = ts_type[:-2].strip()
            inner_type_info = self._map_type(inner_type)
            type_info.python_type = f"List[{inner_type_info.python_type}]"
            type_info.imports.extend(inner_type_info.imports)
            type_info.imports.append(PythonImport(module='typing', items=['List'], is_type_import=True))
            return type_info
        
        # Check for generic types
        generic_match = re.match(r'(\w+)<(.+)>', ts_type)
        if generic_match:
            container_type = generic_match.group(1)
            inner_types = generic_match.group(2)
            
            if container_type == 'Array':
                inner_type_info = self._map_type(inner_types)
                type_info.python_type = f"List[{inner_type_info.python_type}]"
                type_info.imports.append(PythonImport(module='typing', items=['List'], is_type_import=True))
            elif container_type == 'Record':
                # Record<K, V> -> Dict[K, V]
                key_value = inner_types.split(',', 1)
                if len(key_value) == 2:
                    key_type = self._map_type(key_value[0].strip())
                    value_type = self._map_type(key_value[1].strip())
                    type_info.python_type = f"Dict[{key_type.python_type}, {value_type.python_type}]"
                    type_info.imports.append(PythonImport(module='typing', items=['Dict'], is_type_import=True))
            elif container_type == 'Promise':
                inner_type_info = self._map_type(inner_types)
                type_info.python_type = f"Awaitable[{inner_type_info.python_type}]"
                type_info.imports.append(PythonImport(module='typing', items=['Awaitable'], is_type_import=True))
            else:
                # Generic custom type
                type_info.python_type = f"{container_type}[{inner_types}]"
                
            return type_info
        
        # Check for union types
        if '|' in ts_type:
            type_info.is_union = True
            union_types = [t.strip() for t in ts_type.split('|')]
            python_types = []
            for t in union_types:
                t_info = self._map_type(t)
                python_types.append(t_info.python_type)
                type_info.imports.extend(t_info.imports)
            type_info.python_type = f"Union[{', '.join(python_types)}]"
            type_info.imports.append(PythonImport(module='typing', items=['Union'], is_type_import=True))
            return type_info
        
        # Check for branded types
        if ts_type in self.BRANDED_TYPES:
            type_info.python_type = self.BRANDED_TYPES[ts_type]
            type_info.imports.append(PythonImport(module='dipeo.models', items=[ts_type], is_type_import=True))
            return type_info
        
        # Check for basic type mappings
        if ts_type in self.TYPE_MAPPINGS:
            type_info.python_type = self.TYPE_MAPPINGS[ts_type]
            
            # Add necessary imports
            if ts_type == 'any' or ts_type == 'unknown':
                type_info.imports.append(PythonImport(module='typing', items=['Any'], is_type_import=True))
            elif ts_type == 'Date':
                type_info.imports.append(PythonImport(module='datetime', items=['datetime'], is_type_import=False))
            elif ts_type == 'RegExp':
                type_info.imports.append(PythonImport(module='re', items=['Pattern'], is_type_import=True))
                
            return type_info
        
        # Assume it's a custom type/interface
        type_info.python_type = ts_type
        return type_info
    
    def _get_class_bases(self, cls: Dict[str, Any]) -> List[str]:
        """Get base classes for a Python class."""
        bases = []
        
        # Check if it extends another class
        if 'extends' in cls:
            bases.append(cls['extends'])
        
        # For data classes, use Pydantic BaseModel
        if not bases and cls.get('properties'):
            bases.append('BaseModel')
            
        return bases or ['object']
    
    def _transform_method(self, method: Dict[str, Any]) -> Dict[str, Any]:
        """Transform TypeScript method to Python method info."""
        return {
            'name': method['name'],
            'parameters': [self._transform_parameter(p) for p in method.get('parameters', [])],
            'return_type': self._map_type(method.get('returnType', 'None')).python_type,
            'is_async': method.get('async', False),
            'is_static': method.get('static', False),
            'docstring': method.get('comment'),
        }
    
    def _transform_parameter(self, param: Dict[str, Any]) -> Dict[str, Any]:
        """Transform method parameter."""
        type_info = self._map_type(param.get('type', 'Any'))
        return {
            'name': param['name'],
            'type': type_info.python_type,
            'default': param.get('initializer'),
            'optional': param.get('optional', False),
        }
    
    def _needs_validators(self, model: ModelInfo) -> bool:
        """Check if model needs validators."""
        # Add validators for branded types, complex validations, etc.
        for field in model.fields.values():
            if field['type'] in self.BRANDED_TYPES.values():
                return True
        return False
    
    def _generate_validators(self, model: ModelInfo) -> List[Dict[str, Any]]:
        """Generate Pydantic validators for the model."""
        validators = []
        
        # Add validators for specific field types
        for field_name, field_info in model.fields.items():
            if field_info['type'] == 'NodeID':
                validators.append({
                    'name': f'validate_{field_name}',
                    'decorator': f'@field_validator("{field_name}")',
                    'body': [
                        f'def validate_{field_name}(cls, v):',
                        '    if v and not isinstance(v, str):',
                        '        raise ValueError(f"{field_name} must be a string")',
                        '    return v',
                    ]
                })
        
        return validators
    
    def _consolidate_imports(self) -> List[Dict[str, Any]]:
        """Consolidate and organize imports."""
        # Group imports by module
        import_groups = {}
        for imp in self.imports:
            if imp.module not in import_groups:
                import_groups[imp.module] = {
                    'module': imp.module,
                    'items': set(),
                    'is_type_import': imp.is_type_import,
                }
            import_groups[imp.module]['items'].update(imp.items)
        
        # Convert to list and sort
        consolidated = []
        for group in import_groups.values():
            consolidated.append({
                'module': group['module'],
                'items': sorted(list(group['items'])),
                'is_type_import': group['is_type_import'],
            })
        
        # Sort by standard library, third party, then local imports
        def import_priority(imp):
            module = imp['module']
            if module in ['typing', 'enum', 'datetime', 're', 'dataclasses']:
                return 0  # Standard library
            elif module.startswith('dipeo'):
                return 2  # Local imports
            else:
                return 1  # Third party
        
        return sorted(consolidated, key=lambda x: (import_priority(x), x['module']))
    
    def _get_zod_imports(self) -> List[str]:
        """Get required Zod imports."""
        return ['z']  # Simplified for now


# Export the main transformation function
def transform_typescript_to_python(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Transform TypeScript AST to Python models."""
    transformer = TypeScriptToPythonTransformer()
    return transformer.transform_typescript_to_python(inputs)