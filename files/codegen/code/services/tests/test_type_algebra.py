"""Compact tests for Core Type Algebra."""

import pytest
from ..type_algebra import CoreTypeAlgebra, TypeExpression, TypeKind, ScalarType, ProjectionContext


def test_parse_basic_types():
    algebra = CoreTypeAlgebra()
    
    # Scalars
    assert algebra.parse('string').scalar_type == ScalarType.STRING
    assert algebra.parse('number').scalar_type == ScalarType.INTEGER
    assert algebra.parse('boolean').scalar_type == ScalarType.BOOLEAN
    
    # Arrays
    arr = algebra.parse('string[]')
    assert arr.kind == TypeKind.ARRAY
    assert arr.params[0].scalar_type == ScalarType.STRING
    
    # Optionals
    opt = algebra.parse('string | null')
    assert opt.kind == TypeKind.OPTIONAL
    assert opt.params[0].scalar_type == ScalarType.STRING


def test_type_projection():
    algebra = CoreTypeAlgebra()
    
    # Test all three projectors
    expr = algebra.parse('string[]')
    assert algebra.project(expr, 'python') == 'List[str]'
    assert algebra.project(expr, 'typescript') == 'string[]'
    assert algebra.project(expr, 'graphql') == '[String!]'
    
    # Test optional projection
    opt_expr = algebra.parse('number | null')
    assert algebra.project(opt_expr, 'python') == 'Optional[int]'
    assert algebra.project(opt_expr, 'typescript') == 'number | null'
    assert algebra.project(opt_expr, 'graphql') == 'Int'


def test_lossiness_detection():
    algebra = CoreTypeAlgebra()
    
    # Map type (lossy in GraphQL)
    map_expr = TypeExpression(kind=TypeKind.MAP, params=[])
    result, info = algebra.project_with_info(map_expr, 'graphql')
    assert info.is_lossy
    assert 'Map' in info.reason
    
    # Union type (lossy in GraphQL)
    union_expr = TypeExpression(kind=TypeKind.UNION, params=[])
    result, info = algebra.project_with_info(union_expr, 'graphql')
    assert info.is_lossy