"""Language-specific type projectors

Implements type projection from the core algebra to target languages.
"""

from typing import Dict, List, Optional, Set

from .type_algebra import (
    TypeExpression, TypeKind, ScalarType, ProjectionContext,
    LossinessInfo, TypeProjector
)


class BaseProjector:
    """Base class for type projectors with common functionality"""
    
    def __init__(self, type_algebra=None):
        self.type_algebra = type_algebra
        self._import_tracker: Set[str] = set()
    
    def project_with_info(self, expr: TypeExpression, context: ProjectionContext) -> tuple[str, LossinessInfo]:
        """Default implementation that reports no lossiness"""
        result = self.project(expr, context)
        return result, LossinessInfo(is_lossy=False)
    
    def get_imports(self) -> List[str]:
        """Get required imports for projected types"""
        return sorted(list(self._import_tracker))
    
    def clear_imports(self) -> None:
        """Clear tracked imports"""
        self._import_tracker.clear()


class PythonProjector(BaseProjector):
    """Projects types to Python 3.13+ with typing module"""
    
    SCALAR_MAP = {
        ScalarType.STRING: 'str',
        ScalarType.INTEGER: 'int',
        ScalarType.FLOAT: 'float',
        ScalarType.BOOLEAN: 'bool',
        ScalarType.ANY: 'Any',
        ScalarType.VOID: 'None',
        ScalarType.NULL: 'None',
        ScalarType.UNDEFINED: 'None',
    }
    
    def project(self, expr: TypeExpression, context: ProjectionContext) -> str:
        """Project to Python type annotation"""
        if expr.kind == TypeKind.SCALAR:
            python_type = self.SCALAR_MAP.get(expr.scalar_type, 'Any')
            if python_type == 'Any':
                self._import_tracker.add('from typing import Any')
            return python_type
        
        elif expr.kind == TypeKind.ARRAY:
            self._import_tracker.add('from typing import List')
            element_type = self.project(expr.params[0], context)
            return f"List[{element_type}]"
        
        elif expr.kind == TypeKind.OPTIONAL:
            self._import_tracker.add('from typing import Optional')
            inner_type = self.project(expr.params[0], context)
            return f"Optional[{inner_type}]"
        
        elif expr.kind == TypeKind.MAP:
            self._import_tracker.add('from typing import Dict')
            key_type = self.project(expr.params[0], context) if expr.params else 'str'
            value_type = self.project(expr.params[1], context) if len(expr.params) > 1 else 'Any'
            return f"Dict[{key_type}, {value_type}]"
        
        elif expr.kind == TypeKind.UNION:
            self._import_tracker.add('from typing import Union')
            types = [self.project(p, context) for p in expr.params]
            # Deduplicate types
            unique_types = list(dict.fromkeys(types))
            if len(unique_types) == 1:
                return unique_types[0]
            return f"Union[{', '.join(unique_types)}]"
        
        elif expr.kind == TypeKind.REFERENCE:
            # Assume reference is to a local type
            return expr.reference_name or 'Any'
        
        elif expr.kind == TypeKind.ENUM:
            # Enums are typically defined as classes in Python
            return expr.reference_name or 'str'
        
        elif expr.kind == TypeKind.LITERAL:
            self._import_tracker.add('from typing import Literal')
            if isinstance(expr.literal_value, str):
                return f'Literal["{expr.literal_value}"]'
            else:
                return f'Literal[{expr.literal_value}]'
        
        elif expr.kind == TypeKind.OBJECT:
            # For objects, we typically use TypedDict or a class
            if expr.properties:
                self._import_tracker.add('from typing import TypedDict')
                # This is simplified - real implementation would generate proper TypedDict
                return 'Dict[str, Any]'
            return 'Dict[str, Any]'
        
        else:
            return 'Any'
    
    def project_with_info(self, expr: TypeExpression, context: ProjectionContext) -> tuple[str, LossinessInfo]:
        """Project with lossiness information"""
        result = self.project(expr, context)
        info = LossinessInfo()
        
        # Check for lossiness
        if expr.kind == TypeKind.INTERSECTION:
            info.is_lossy = True
            info.reason = "Python doesn't support intersection types natively"
            info.severity = "warning"
            info.suggested_mitigation = "Use Protocol or multiple inheritance"
        
        elif expr.kind == TypeKind.GENERIC and len(expr.params) > 1:
            info.is_lossy = True
            info.reason = "Complex generic constraints may be simplified"
            info.severity = "info"
        
        return result, info


class TypeScriptProjector(BaseProjector):
    """Projects types to TypeScript"""
    
    SCALAR_MAP = {
        ScalarType.STRING: 'string',
        ScalarType.INTEGER: 'number',
        ScalarType.FLOAT: 'number',
        ScalarType.BOOLEAN: 'boolean',
        ScalarType.ANY: 'any',
        ScalarType.VOID: 'void',
        ScalarType.NULL: 'null',
        ScalarType.UNDEFINED: 'undefined',
    }
    
    def project(self, expr: TypeExpression, context: ProjectionContext) -> str:
        """Project to TypeScript type"""
        if expr.kind == TypeKind.SCALAR:
            return self.SCALAR_MAP.get(expr.scalar_type, 'any')
        
        elif expr.kind == TypeKind.ARRAY:
            element_type = self.project(expr.params[0], context)
            if context.array_syntax == "generic":
                return f"Array<{element_type}>"
            else:
                return f"{element_type}[]"
        
        elif expr.kind == TypeKind.OPTIONAL:
            inner_type = self.project(expr.params[0], context)
            if context.optional_syntax == "generic":
                # TypeScript doesn't have Optional, use union
                return f"{inner_type} | null | undefined"
            else:
                return f"{inner_type} | null"
        
        elif expr.kind == TypeKind.MAP:
            key_type = self.project(expr.params[0], context) if expr.params else 'string'
            value_type = self.project(expr.params[1], context) if len(expr.params) > 1 else 'any'
            if key_type in ['string', 'number', 'symbol']:
                return f"{{ [key: {key_type}]: {value_type} }}"
            else:
                return f"Map<{key_type}, {value_type}>"
        
        elif expr.kind == TypeKind.UNION:
            types = [self.project(p, context) for p in expr.params]
            # Deduplicate types
            unique_types = list(dict.fromkeys(types))
            if len(unique_types) == 1:
                return unique_types[0]
            return ' | '.join(unique_types)
        
        elif expr.kind == TypeKind.INTERSECTION:
            types = [self.project(p, context) for p in expr.params]
            return ' & '.join(types)
        
        elif expr.kind == TypeKind.REFERENCE:
            return expr.reference_name or 'any'
        
        elif expr.kind == TypeKind.ENUM:
            return expr.reference_name or 'string'
        
        elif expr.kind == TypeKind.LITERAL:
            if isinstance(expr.literal_value, str):
                return f'"{expr.literal_value}"'
            elif isinstance(expr.literal_value, bool):
                return 'true' if expr.literal_value else 'false'
            else:
                return str(expr.literal_value)
        
        elif expr.kind == TypeKind.OBJECT:
            if expr.properties:
                # Generate inline object type
                props = []
                for name, prop_type in expr.properties.items():
                    prop_str = f"{name}: {self.project(prop_type, context)}"
                    props.append(prop_str)
                return f"{{ {'; '.join(props)} }}"
            return '{}'
        
        else:
            return 'any'


class GraphQLProjector(BaseProjector):
    """Projects types to GraphQL schema definition language"""
    
    SCALAR_MAP = {
        ScalarType.STRING: 'String',
        ScalarType.INTEGER: 'Int',
        ScalarType.FLOAT: 'Float',
        ScalarType.BOOLEAN: 'Boolean',
        ScalarType.ANY: 'JSON',  # Requires scalar definition
        ScalarType.VOID: None,  # GraphQL doesn't have void
        ScalarType.NULL: None,
        ScalarType.UNDEFINED: None,
    }
    
    def __init__(self, type_algebra=None):
        super().__init__(type_algebra)
        self._custom_scalars: Set[str] = set()
    
    def project(self, expr: TypeExpression, context: ProjectionContext) -> str:
        """Project to GraphQL type"""
        if expr.kind == TypeKind.SCALAR:
            graphql_type = self.SCALAR_MAP.get(expr.scalar_type)
            if graphql_type == 'JSON':
                self._custom_scalars.add('JSON')
            return graphql_type or 'String'
        
        elif expr.kind == TypeKind.ARRAY:
            element_type = self.project(expr.params[0], context)
            # GraphQL arrays must specify nullability
            return f"[{element_type}!]"
        
        elif expr.kind == TypeKind.OPTIONAL:
            # In GraphQL, optional is the default, so we just project the inner type
            inner_type = self.project(expr.params[0], context)
            return inner_type
        
        elif expr.kind == TypeKind.MAP:
            # GraphQL doesn't have native map types
            self._custom_scalars.add('JSON')
            return 'JSON'
        
        elif expr.kind == TypeKind.UNION:
            # GraphQL unions need to be defined separately
            # For inline use, we might fall back to a common type
            return 'String'  # Simplified - real impl would track union definitions
        
        elif expr.kind == TypeKind.REFERENCE:
            return expr.reference_name or 'String'
        
        elif expr.kind == TypeKind.ENUM:
            return expr.reference_name or 'String'
        
        elif expr.kind == TypeKind.LITERAL:
            # GraphQL doesn't support literal types
            return 'String'
        
        elif expr.kind == TypeKind.OBJECT:
            # Objects need to be defined as types
            return expr.reference_name or 'JSON'
        
        else:
            return 'String'
    
    def project_with_info(self, expr: TypeExpression, context: ProjectionContext) -> tuple[str, LossinessInfo]:
        """Project with lossiness information"""
        result = self.project(expr, context)
        info = LossinessInfo()
        
        # Check for lossiness
        if expr.kind == TypeKind.MAP:
            info.is_lossy = True
            info.reason = "GraphQL doesn't have native Map types, using JSON scalar"
            info.severity = "warning"
            info.suggested_mitigation = "Define a custom object type if structure is known"
        
        elif expr.kind == TypeKind.UNION and context.preserve_unions:
            info.is_lossy = True
            info.reason = "GraphQL union types must be defined separately"
            info.severity = "info"
            info.suggested_mitigation = "Define union type in schema"
        
        elif expr.kind == TypeKind.LITERAL:
            info.is_lossy = True
            info.reason = "GraphQL doesn't support literal types"
            info.severity = "info"
            info.suggested_mitigation = "Use enum type for known values"
        
        elif expr.kind == TypeKind.INTERSECTION:
            info.is_lossy = True
            info.reason = "GraphQL doesn't support intersection types"
            info.severity = "warning"
            info.suggested_mitigation = "Use interface inheritance or merge fields"
        
        return result, info
    
    def get_custom_scalars(self) -> Set[str]:
        """Get set of custom scalars that need to be defined"""
        return self._custom_scalars.copy()