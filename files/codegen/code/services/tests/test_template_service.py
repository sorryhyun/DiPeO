"""Compact tests for Template Service."""

import pytest
from ..template_service import TemplateService, MacroDefinition


def test_singleton():
    service1 = TemplateService()
    service2 = TemplateService()
    assert service1 is service2


def test_shared_filters():
    service = TemplateService()
    
    # Test case conversion filters
    assert service.render_string('{{ "hello_world" | camel_case }}').strip() == 'helloWorld'
    assert service.render_string('{{ "hello_world" | pascal_case }}').strip() == 'HelloWorld'
    assert service.render_string('{{ "HelloWorld" | snake_case }}').strip() == 'hello_world'
    assert service.render_string('{{ "hello_world" | kebab_case }}').strip() == 'hello-world'
    
    # Test pluralization
    assert service.render_string('{{ "user" | pluralize }}').strip() == 'users'
    assert service.render_string('{{ "class" | pluralize }}').strip() == 'classes'
    
    # Test default values
    assert service.render_string('{{ "str" | default_value("python") }}').strip() == '""'
    assert service.render_string('{{ "number" | default_value("typescript") }}').strip() == '0'


def test_custom_renderer():
    service = TemplateService()
    
    # Renderer with extra filters
    renderer = service.get_renderer('', extra_filters={
        'double': lambda x: x * 2,
        'reverse': lambda x: x[::-1]
    })
    
    assert renderer.render_string('{{ 5 | double }}').strip() == '10'
    assert renderer.render_string('{{ "hello" | reverse }}').strip() == 'olleh'


def test_macro_library():
    service = TemplateService()
    
    # Register custom macro
    macro = MacroDefinition(
        name='greeting',
        template='Hello, {{ name }}!',
        params=['name']
    )
    service.register_macro(macro)
    
    # Use macro
    template = '{{ greeting("World") }}'
    result = service.render_string(template)
    assert 'Hello, World!' in result


def test_base_templates():
    service = TemplateService()
    env = service.get_environment()
    
    # Should have base templates available
    assert env.get_template('python_base.j2') is not None
    assert env.get_template('typescript_base.j2') is not None
    assert env.get_template('graphql_base.j2') is not None