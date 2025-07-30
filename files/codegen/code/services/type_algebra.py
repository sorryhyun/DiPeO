"""Core Type Algebra Service

Provides a mathematical foundation for type representation that can be
projected to different target languages while preserving semantic correctness.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .type_projectors import PythonProjector, TypeScriptProjector, GraphQLProjector


class TypeKind(Enum):
    """Fundamental type kinds in the algebra"""
    SCALAR = auto()
    ARRAY = auto()
    MAP = auto()
    UNION = auto()
    INTERSECTION = auto()
    OPTIONAL = auto()
    ENUM = auto()
    OBJECT = auto()
    REFERENCE = auto()
    LITERAL = auto()
    GENERIC = auto()


class ScalarType(Enum):
    """Built-in scalar types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ANY = "any"
    VOID = "void"
    NULL = "null"
    UNDEFINED = "undefined"


@dataclass
class TypeExpression:
    """Core type expression in the algebra"""
    kind: TypeKind
    params: List['TypeExpression'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # For scalars
    scalar_type: Optional[ScalarType] = None
    
    # For references
    reference_name: Optional[str] = None
    
    # For literals
    literal_value: Optional[Any] = None
    
    # For enums
    enum_values: Optional[List[str]] = None
    
    # For objects
    properties: Optional[Dict[str, 'TypeExpression']] = None
    
    def __repr__(self) -> str:
        if self.kind == TypeKind.SCALAR:
            return f"Scalar({self.scalar_type.value})"
        elif self.kind == TypeKind.ARRAY:
            return f"Array({self.params[0]})"
        elif self.kind == TypeKind.OPTIONAL:
            return f"Optional({self.params[0]})"
        elif self.kind == TypeKind.REFERENCE:
            return f"Ref({self.reference_name})"
        else:
            return f"{self.kind.name}({self.params})"


@dataclass
class ProjectionContext:
    """Context for type projection operations"""
    strict_nullability: bool = True
    preserve_unions: bool = True
    enum_as_literal: bool = False
    array_syntax: str = "bracket"  # bracket: T[], generic: Array<T>
    optional_syntax: str = "union"  # union: T | null, generic: Optional<T>
    import_tracker: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.import_tracker is None:
            self.import_tracker = {}


@dataclass
class LossinessInfo:
    """Information about potential data loss in type projection"""
    is_lossy: bool = False
    reason: Optional[str] = None
    severity: str = "info"  # info, warning, error
    suggested_mitigation: Optional[str] = None


class TypeProjector(Protocol):
    """Protocol for language-specific type projectors"""
    
    def project(self, expr: TypeExpression, context: ProjectionContext) -> str:
        """Project type expression to target language representation"""
        ...
    
    def project_with_info(self, expr: TypeExpression, context: ProjectionContext) -> tuple[str, LossinessInfo]:
        """Project with lossiness information"""
        ...


class CoreTypeAlgebra:
    """Core type algebra with language-agnostic representation"""
    
    def __init__(self, auto_register_projectors: bool = True):
        self._projectors: Dict[str, TypeProjector] = {}
        self._type_registry: Dict[str, TypeExpression] = {}
        
        if auto_register_projectors:
            self._register_default_projectors()
        
    def register_projector(self, target: str, projector: TypeProjector) -> None:
        """Register a type projector for a target language"""
        self._projectors[target] = projector
    
    def register_type(self, name: str, type_expr: TypeExpression) -> None:
        """Register a named type in the registry"""
        self._type_registry[name] = type_expr
    
    def parse(self, type_string: str) -> TypeExpression:
        """Parse a type string into a TypeExpression"""
        # Simplified parser - would be expanded in full implementation
        type_string = type_string.strip()
        
        # Handle arrays
        if type_string.endswith('[]'):
            element_type = self.parse(type_string[:-2])
            return TypeExpression(
                kind=TypeKind.ARRAY,
                params=[element_type]
            )
        
        # Handle optionals (TypeScript style)
        if type_string.endswith('?'):
            inner_type = self.parse(type_string[:-1])
            return TypeExpression(
                kind=TypeKind.OPTIONAL,
                params=[inner_type]
            )
        
        # Handle union types
        if ' | ' in type_string:
            parts = [p.strip() for p in type_string.split(' | ')]
            if len(parts) == 2 and 'null' in parts:
                # Special case for T | null -> Optional<T>
                non_null = parts[0] if parts[1] == 'null' else parts[1]
                return TypeExpression(
                    kind=TypeKind.OPTIONAL,
                    params=[self.parse(non_null)]
                )
            else:
                return TypeExpression(
                    kind=TypeKind.UNION,
                    params=[self.parse(p) for p in parts]
                )
        
        # Handle generics (simplified)
        if '<' in type_string and type_string.endswith('>'):
            base = type_string[:type_string.index('<')]
            params_str = type_string[type_string.index('<')+1:-1]
            
            if base == 'Array':
                return TypeExpression(
                    kind=TypeKind.ARRAY,
                    params=[self.parse(params_str)]
                )
            elif base == 'Map' or base == 'Dict':
                # Simplified - assumes Map<K, V> format
                parts = params_str.split(',', 1)
                if len(parts) == 2:
                    return TypeExpression(
                        kind=TypeKind.MAP,
                        params=[self.parse(parts[0]), self.parse(parts[1])]
                    )
        
        # Check if it's a known type reference
        if type_string in self._type_registry:
            return TypeExpression(
                kind=TypeKind.REFERENCE,
                reference_name=type_string
            )
        
        # Check for scalar types
        scalar_map = {
            'string': ScalarType.STRING,
            'number': ScalarType.INTEGER,
            'float': ScalarType.FLOAT,
            'boolean': ScalarType.BOOLEAN,
            'bool': ScalarType.BOOLEAN,
            'any': ScalarType.ANY,
            'void': ScalarType.VOID,
            'null': ScalarType.NULL,
            'undefined': ScalarType.UNDEFINED,
            'int': ScalarType.INTEGER,
        }
        
        if type_string.lower() in scalar_map:
            return TypeExpression(
                kind=TypeKind.SCALAR,
                scalar_type=scalar_map[type_string.lower()]
            )
        
        # Default to reference for unknown types
        return TypeExpression(
            kind=TypeKind.REFERENCE,
            reference_name=type_string
        )
    
    def project(self, expr: TypeExpression, target: str, context: Optional[ProjectionContext] = None) -> str:
        """Project type expression to target language"""
        if target not in self._projectors:
            raise ValueError(f"No projector registered for target: {target}")
        
        if context is None:
            context = ProjectionContext()
        
        projector = self._projectors[target]
        return projector.project(expr, context)
    
    def project_with_info(self, expr: TypeExpression, target: str, context: Optional[ProjectionContext] = None) -> tuple[str, LossinessInfo]:
        """Project with lossiness information"""
        if target not in self._projectors:
            raise ValueError(f"No projector registered for target: {target}")
        
        if context is None:
            context = ProjectionContext()
        
        projector = self._projectors[target]
        return projector.project_with_info(expr, context)
    
    def resolve_reference(self, ref_name: str) -> Optional[TypeExpression]:
        """Resolve a type reference"""
        return self._type_registry.get(ref_name)
    
    def _register_default_projectors(self) -> None:
        """Register default language projectors"""
        # Import here to avoid circular dependencies
        from .type_projectors import PythonProjector, TypeScriptProjector, GraphQLProjector
        
        self.register_projector('python', PythonProjector(self))
        self.register_projector('typescript', TypeScriptProjector(self))
        self.register_projector('graphql', GraphQLProjector(self))