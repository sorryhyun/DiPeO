"""Integration tests showing services working together."""

import pytest
import asyncio
from pathlib import Path
from ..type_algebra import CoreTypeAlgebra
from ..ast_service import ASTService
from ..template_service import TemplateService
from ..constants import KNOWN_ENUMS, is_enum_type


@pytest.mark.asyncio
async def test_end_to_end_generation():
    """Test complete code generation flow using all services."""
    
    # 1. Parse types using Type Algebra
    algebra = CoreTypeAlgebra()
    field_types = [
        ('name', 'string'),
        ('age', 'number'),
        ('tags', 'string[]'),
        ('status', 'MemoryProfile'),  # Known enum
        ('metadata', 'Dict<string, any>')
    ]
    
    # 2. Project types to different targets
    python_types = {}
    ts_types = {}
    graphql_types = {}
    
    for field_name, type_str in field_types:
        expr = algebra.parse(type_str)
        python_types[field_name] = algebra.project(expr, 'python')
        ts_types[field_name] = algebra.project(expr, 'typescript')
        graphql_types[field_name] = algebra.project(expr, 'graphql')
    
    # 3. Use AST service for processing
    ast_service = ASTService()
    mock_ast = {
        'models': {'User': {'fields': field_types}},
        'enums': {'MemoryProfile': ['DEFAULT', 'EXTENDED', 'MINIMAL']}
    }
    
    # 4. Use Template service to generate code
    template_service = TemplateService()
    
    # Generate Python model
    python_template = """
class {{ model_name }}:
    {% for field, type in fields.items() -%}
    {{ field }}: {{ type }}
    {% endfor %}"""
    
    python_code = template_service.render_string(
        python_template,
        model_name='User',
        fields=python_types
    )
    
    assert 'name: str' in python_code
    assert 'age: int' in python_code
    assert 'tags: List[str]' in python_code
    assert 'status: MemoryProfile' in python_code
    
    # Generate TypeScript interface
    ts_template = """
interface {{ model_name }} {
    {% for field, type in fields.items() -%}
    {{ field }}: {{ type }};
    {% endfor %}}"""
    
    ts_code = template_service.render_string(
        ts_template,
        model_name='User',
        fields=ts_types
    )
    
    assert 'name: string;' in ts_code
    assert 'age: number;' in ts_code
    assert 'tags: string[];' in ts_code


def test_constants_integration():
    """Test that constants work with other services."""
    
    # Test enum detection
    assert is_enum_type('MemoryProfile')
    assert not is_enum_type('string')
    
    # Test with type algebra
    algebra = CoreTypeAlgebra()
    
    # Known enum should be treated as reference
    enum_expr = algebra.parse('MemoryProfile')
    assert enum_expr.kind.name == 'REFERENCE'
    assert enum_expr.reference_name == 'MemoryProfile'
    
    # Project should preserve enum name
    assert algebra.project(enum_expr, 'python') == 'MemoryProfile'
    assert algebra.project(enum_expr, 'typescript') == 'MemoryProfile'


def test_performance():
    """Quick performance check."""
    import time
    
    algebra = CoreTypeAlgebra()
    template_service = TemplateService()
    
    # Type parsing performance
    start = time.time()
    for _ in range(1000):
        algebra.parse('Array<Dict<string, List<number>>>')
    parse_time = time.time() - start
    
    # Template rendering performance
    start = time.time()
    for _ in range(1000):
        template_service.render_string('{{ name | snake_case }}', name='HelloWorld')
    render_time = time.time() - start
    
    # Should be reasonably fast
    assert parse_time < 1.0  # 1s for 1000 parses
    assert render_time < 5.0  # 5s for 1000 renders (template rendering can be slower)