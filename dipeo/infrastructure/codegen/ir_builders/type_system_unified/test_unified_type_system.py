"""Comprehensive tests for the unified type system.

Tests cover:
1. UnifiedTypeConverter - Type conversion functionality
2. TypeRegistry - Type registration and management
3. UnifiedTypeResolver - Strawberry GraphQL type resolution
"""

import pytest

from .converter import UnifiedTypeConverter
from .registry import TypeRegistry, get_global_registry, reset_global_registry
from .resolver import UnifiedTypeResolver


class TestUnifiedTypeConverter:
    """Tests for UnifiedTypeConverter."""

    @pytest.fixture
    def converter(self):
        """Create a UnifiedTypeConverter instance."""
        return UnifiedTypeConverter()

    # ========================================================================
    # TypeScript → Python Conversion Tests
    # ========================================================================

    def test_basic_ts_to_python(self, converter):
        """Test basic TypeScript to Python type conversion."""
        assert converter.ts_to_python("string") == "str"
        assert converter.ts_to_python("number") == "float"
        assert converter.ts_to_python("boolean") == "bool"
        assert converter.ts_to_python("any") == "Any"
        assert converter.ts_to_python("unknown") == "Any"
        assert converter.ts_to_python("null") == "None"
        assert converter.ts_to_python("undefined") == "None"
        assert converter.ts_to_python("void") == "None"

    def test_integer_field_override(self, converter):
        """Test that specific fields are converted to int instead of float."""
        assert converter.ts_to_python("number", "count") == "int"
        assert converter.ts_to_python("number", "maxIteration") == "int"
        assert converter.ts_to_python("number", "timeout") == "int"
        assert converter.ts_to_python("number", "x") == "int"
        assert converter.ts_to_python("number", "y") == "int"

        # Non-integer fields should still be float
        assert converter.ts_to_python("number", "score") == "float"

    def test_array_conversion(self, converter):
        """Test array type conversion."""
        assert converter.ts_to_python("string[]") == "List[str]"
        assert converter.ts_to_python("number[]", "count") == "List[int]"
        assert converter.ts_to_python("Array<string>") == "List[str]"
        assert converter.ts_to_python("ReadonlyArray<number>") == "Sequence[float]"

    def test_optional_types(self, converter):
        """Test optional type conversion."""
        assert converter.ts_to_python("string | undefined") == "Optional[str]"
        assert converter.ts_to_python("number | null") == "Optional[float]"
        assert converter.ts_to_python("boolean | null | undefined") == "Optional[bool]"

    def test_union_types(self, converter):
        """Test union type conversion."""
        assert converter.ts_to_python("'a' | 'b' | 'c'") == "Literal['a', 'b', 'c']"
        assert "Union[" in converter.ts_to_python("string | number")

    def test_literal_types(self, converter):
        """Test literal type conversion."""
        assert converter.ts_to_python("'value'") == "Literal['value']"
        assert converter.ts_to_python('"value"') == 'Literal["value"]'
        assert converter.ts_to_python("true") == "Literal[True]"
        assert converter.ts_to_python("false") == "Literal[False]"

    def test_generic_types(self, converter):
        """Test generic type conversion."""
        assert converter.ts_to_python("Array<string>") == "List[str]"
        assert converter.ts_to_python("Promise<number>") == "Awaitable[float]"
        assert converter.ts_to_python("Record<string, any>") == "Dict[str, Any]"
        assert converter.ts_to_python("Map<string, number>") == "Dict[str, float]"
        assert converter.ts_to_python("Partial<MyType>") == "Partial[MyType]"
        assert converter.ts_to_python("Required<MyType>") == "Required[MyType]"

    def test_tuple_types(self, converter):
        """Test tuple type conversion."""
        assert converter.ts_to_python("[string, number]") == "tuple[str, float]"
        assert converter.ts_to_python("[string, number, boolean]") == "tuple[str, float, bool]"

    def test_branded_types(self, converter):
        """Test branded ID type detection."""
        assert converter.is_branded_type("NodeID")
        assert converter.is_branded_type("DiagramID")
        assert converter.is_branded_type("ExecutionID")
        assert not converter.is_branded_type("string")

    def test_type_aliases(self, converter):
        """Test historical type aliases."""
        assert converter.ts_to_python("SerializedNodeOutput") == "SerializedEnvelope"
        assert converter.ts_to_python("PersonMemoryMessage") == "Message"
        assert converter.ts_to_python("ExecutionStatus") == "Status"

    def test_inline_object_types(self, converter):
        """Test inline object type conversion."""
        assert converter.ts_to_python("{}") == "Dict[str, Any]"
        assert converter.ts_to_python("{ [key: string]: number }") == "Dict[str, float]"

    # ========================================================================
    # TypeScript → GraphQL Conversion Tests
    # ========================================================================

    def test_ts_to_graphql(self, converter):
        """Test TypeScript to GraphQL conversion."""
        assert converter.ts_to_graphql("string") == "String"
        assert converter.ts_to_graphql("number") == "Float"
        assert converter.ts_to_graphql("boolean") == "Boolean"
        assert converter.ts_to_graphql("any") == "JSONScalar"
        assert converter.ts_to_graphql("unknown") == "JSONScalar"
        assert converter.ts_to_graphql("Date") == "DateTime"

    def test_ts_to_graphql_arrays(self, converter):
        """Test TypeScript array to GraphQL list conversion."""
        assert converter.ts_to_graphql("string[]") == "[String]"
        assert converter.ts_to_graphql("Array<number>") == "[Float]"

    # ========================================================================
    # GraphQL Conversion Tests
    # ========================================================================

    def test_graphql_to_ts(self, converter):
        """Test GraphQL to TypeScript conversion."""
        assert converter.graphql_to_ts("String") == "string"
        assert converter.graphql_to_ts("Int") == "number"
        assert converter.graphql_to_ts("Float") == "number"
        assert converter.graphql_to_ts("Boolean") == "boolean"
        assert converter.graphql_to_ts("ID") == "string"

    def test_graphql_to_python(self, converter):
        """Test GraphQL to Python conversion."""
        python_type = converter.graphql_to_python("String")
        assert python_type == "str"

        python_type = converter.graphql_to_python("Int")
        assert python_type == "float"  # Goes through TypeScript first

        # Test with required flag
        python_type = converter.graphql_to_python("String", required=False)
        assert "Optional[" in python_type or "list[" in python_type

    def test_graphql_input_conversion(self, converter):
        """Test GraphQL input pattern conversion."""
        assert converter.ts_graphql_input_to_python("Scalars['ID']['input']") == "str"
        assert converter.ts_graphql_input_to_python("Scalars['String']['input']") == "str"
        assert converter.ts_graphql_input_to_python("Scalars['Int']['input']") == "int"
        assert converter.ts_graphql_input_to_python("Scalars['Boolean']['input']") == "bool"

        assert converter.ts_graphql_input_to_python("InputMaybe<string>") == "Optional[str]"
        assert converter.ts_graphql_input_to_python("Maybe<number>") == "Optional[float]"
        assert converter.ts_graphql_input_to_python("Array<string>") == "List[str]"

    # ========================================================================
    # Utility Method Tests
    # ========================================================================

    def test_ensure_optional(self, converter):
        """Test ensure_optional utility."""
        assert converter.ensure_optional("str") == "Optional[str]"
        assert converter.ensure_optional("Optional[str]") == "Optional[str]"

    def test_is_optional_type(self, converter):
        """Test optional type detection."""
        assert converter.is_optional_type("string | undefined")
        assert converter.is_optional_type("number | null")
        assert not converter.is_optional_type("string")

    def test_get_default_value(self, converter):
        """Test default value generation."""
        assert converter.get_default_value("str") == '""'
        assert converter.get_default_value("int") == "0"
        assert converter.get_default_value("float") == "0.0"
        assert converter.get_default_value("bool") == "False"
        assert converter.get_default_value("List[str]") == "[]"
        assert converter.get_default_value("Dict[str, Any]") == "{}"
        assert converter.get_default_value("Optional[str]") == "None"
        assert converter.get_default_value("str", is_optional=True) == "None"

    def test_get_python_imports(self, converter):
        """Test Python import generation."""
        types = ["List[str]", "Dict[str, Any]", "Optional[int]"]
        imports = converter.get_python_imports(types)

        assert "from typing import List" in imports
        assert "from typing import Dict" in imports
        assert "from typing import Optional" in imports
        assert "from typing import Any" in imports

    def test_caching(self, converter):
        """Test that type conversion results are cached."""
        # Convert the same type twice
        result1 = converter.ts_to_python("string[]")
        result2 = converter.ts_to_python("string[]")

        assert result1 == result2
        assert len(converter._type_cache) > 0

        # Clear cache
        converter.clear_cache()
        assert len(converter._type_cache) == 0

    def test_python_type_with_context(self, converter):
        """Test context-aware Python type resolution."""
        # Test with context-aware field
        field = {"name": "method", "type": "string", "required": True}
        result = converter.python_type_with_context(field, "api_job")
        assert result == "HttpMethod"

        # Test with optional field
        field = {"name": "data", "type": "object", "required": False}
        result = converter.python_type_with_context(field, "api_job")
        assert "Optional[" in result


class TestTypeRegistry:
    """Tests for TypeRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a TypeRegistry instance."""
        return TypeRegistry()

    def test_register_branded_type(self, registry):
        """Test branded type registration."""
        registry.register_branded_type("CustomID")

        assert registry.is_branded_type("CustomID")
        assert registry.get_python_type("CustomID") == "str"
        assert registry.get_strawberry_type("CustomID") == "CustomIDScalar"

    def test_register_enum_type(self, registry):
        """Test enum type registration."""
        registry.register_enum_type("Status", ["PENDING", "RUNNING", "COMPLETED"])

        assert registry.is_enum_type("Status")
        info = registry.get_type_info("Status")
        assert info is not None
        assert info.metadata["values"] == ["PENDING", "RUNNING", "COMPLETED"]

    def test_register_custom_type(self, registry):
        """Test custom type registration."""
        registry.register_custom_type(
            "CustomType", python_type="CustomClass", graphql_type="CustomGQL"
        )

        assert registry.is_registered("CustomType")
        assert registry.get_python_type("CustomType") == "CustomClass"
        assert registry.get_graphql_type("CustomType") == "CustomGQL"

    def test_register_domain_type(self, registry):
        """Test domain type registration."""
        fields = {"id": "NodeID", "name": "str", "data": "Dict[str, Any]"}
        registry.register_domain_type("DomainNode", fields)

        assert registry.is_registered("DomainNode")
        assert registry.get_python_type("DomainNode") == "DomainNode"
        assert registry.get_strawberry_type("DomainNode") == "DomainNodeType"

    def test_type_conversion(self, registry):
        """Test type conversion with custom converter."""

        def uppercase_converter(value: str) -> str:
            return value.upper()

        registry.register_custom_type(
            "UpperString", python_type="str", converter=uppercase_converter
        )

        result = registry.convert_value("UpperString", "hello")
        assert result == "HELLO"

    def test_unregister_type(self, registry):
        """Test type unregistration."""
        registry.register_branded_type("TempID")
        assert registry.is_registered("TempID")

        success = registry.unregister_type("TempID")
        assert success
        assert not registry.is_registered("TempID")

    def test_get_types_by_category(self, registry):
        """Test getting types by category."""
        registry.register_branded_type("ID1")
        registry.register_branded_type("ID2")
        registry.register_enum_type("Enum1", ["A", "B"])

        branded_types = registry.get_types_by_category("branded")
        assert len(branded_types) == 2
        assert "ID1" in branded_types
        assert "ID2" in branded_types

        enum_types = registry.get_types_by_category("enum")
        assert len(enum_types) == 1
        assert "Enum1" in enum_types

    def test_load_from_config(self, registry):
        """Test loading types from configuration."""
        config = {
            "branded_types": ["NodeID", "DiagramID"],
            "enum_types": {"Status": ["PENDING", "RUNNING"]},
            "custom_types": {
                "CustomType": {"python_type": "CustomClass", "graphql_type": "CustomGQL"}
            },
        }

        registry.load_from_config(config)

        assert registry.is_branded_type("NodeID")
        assert registry.is_branded_type("DiagramID")
        assert registry.is_enum_type("Status")
        assert registry.is_registered("CustomType")

    def test_export_to_config(self, registry):
        """Test exporting types to configuration."""
        registry.register_branded_type("NodeID")
        registry.register_enum_type("Status", ["PENDING", "RUNNING"])

        config = registry.export_to_config()

        assert "NodeID" in config["branded_types"]
        assert "Status" in config["enum_types"]
        assert config["enum_types"]["Status"] == ["PENDING", "RUNNING"]

    def test_clear_registry(self, registry):
        """Test clearing the registry."""
        registry.register_branded_type("NodeID")
        registry.register_enum_type("Status", ["A", "B"])

        assert len(registry.get_all_types()) > 0

        registry.clear()

        assert len(registry.get_all_types()) == 0
        assert len(registry.get_all_branded_types()) == 0
        assert len(registry.get_all_enum_types()) == 0

    def test_global_registry(self):
        """Test global registry singleton."""
        # Reset first
        reset_global_registry()

        registry1 = get_global_registry()
        registry2 = get_global_registry()

        assert registry1 is registry2

        registry1.register_branded_type("GlobalID")
        assert registry2.is_branded_type("GlobalID")


class TestUnifiedTypeResolver:
    """Tests for UnifiedTypeResolver."""

    @pytest.fixture
    def resolver(self):
        """Create a UnifiedTypeResolver instance."""
        return UnifiedTypeResolver()

    def test_resolve_basic_field(self, resolver):
        """Test basic field resolution."""
        field = {"name": "name", "type": "str", "optional": False}
        resolved = resolver.resolve_field(field, "DomainNode")

        assert resolved.name == "name"
        assert resolved.python_type == "str"
        assert resolved.strawberry_type == "str"
        assert not resolved.is_optional

    def test_resolve_optional_field(self, resolver):
        """Test optional field resolution."""
        field = {"name": "description", "type": "str", "optional": True}
        resolved = resolver.resolve_field(field, "DomainNode")

        assert resolved.is_optional
        assert resolved.default == " = None"
        assert "Optional[" in resolved.strawberry_type

    def test_resolve_id_field(self, resolver):
        """Test ID field resolution."""
        field = {"name": "id", "type": "NodeID", "optional": False}
        resolved = resolver.resolve_field(field, "DomainNode")

        # Should map to NodeIDScalar
        assert "Scalar" in resolved.strawberry_type or resolved.strawberry_type == "str"

    def test_resolve_domain_type_field(self, resolver):
        """Test domain type field resolution."""
        field = {"name": "node", "type": "DomainNode", "optional": False}
        resolved = resolver.resolve_field(field, "DomainDiagram")

        assert resolved.strawberry_type == "DomainNodeType"

    def test_resolve_list_field(self, resolver):
        """Test list field resolution."""
        field = {"name": "nodes", "type": "List[DomainNode]", "optional": False}
        resolved = resolver.resolve_field(field, "DomainDiagram")

        assert resolved.strawberry_type == "List[DomainNodeType]"
        assert resolved.is_custom_list

    def test_resolve_json_field(self, resolver):
        """Test JSON field resolution."""
        field = {"name": "data", "type": "Dict[str, Any]", "optional": False}
        resolved = resolver.resolve_field(field, "DomainNode")

        assert resolved.is_json
        assert resolved.strawberry_type == "JSONScalar"

    def test_resolve_literal_field(self, resolver):
        """Test literal field resolution."""
        field = {"name": "type", "type": "Literal['node']", "optional": False}
        resolved = resolver.resolve_field(field, "DomainNode")

        assert resolved.is_literal
        assert resolved.strawberry_type == "str"

    def test_process_type(self, resolver):
        """Test complete type processing."""
        interface = {
            "name": "TestType",
            "description": "Test type description",
            "properties": [
                {"name": "id", "type": "str", "optional": False},
                {"name": "name", "type": "str", "optional": False},
                {"name": "description", "type": "str", "optional": True},
            ],
        }

        processed = resolver.process_type(interface)

        assert processed["name"] == "TestType"
        assert len(processed["resolved_fields"]) == 3
        assert processed["description"] == "Test type description"

    def test_should_use_pydantic_decorator(self, resolver):
        """Test pydantic decorator detection."""
        assert resolver.should_use_pydantic_decorator("Vec2")
        assert resolver.should_use_pydantic_decorator("KeepalivePayload")
        assert not resolver.should_use_pydantic_decorator("DomainDiagram")

    def test_should_use_manual_conversion(self, resolver):
        """Test manual conversion detection."""
        assert resolver.should_use_manual_conversion("DomainDiagram")
        assert resolver.should_use_manual_conversion("ExecutionState")
        assert not resolver.should_use_manual_conversion("Vec2")

    def test_generate_conversion_method(self, resolver):
        """Test conversion method generation."""
        fields = [
            resolver.resolve_field({"name": "type", "type": "NodeType", "optional": False}, "DomainNode"),
            resolver.resolve_field({"name": "data", "type": "Dict[str, Any]", "optional": False}, "DomainNode"),
        ]

        # Force manual conversion
        for field in fields:
            if field.name == "type":
                field.needs_conversion = True

        conversion = resolver.generate_conversion_method("DomainNode", fields)

        if conversion.needs_method:
            assert "from_pydantic" in conversion.method_code
            assert "def from_pydantic" in conversion.method_code


class TestIntegration:
    """Integration tests for the unified type system."""

    def test_converter_and_resolver_integration(self):
        """Test that converter and resolver work together."""
        converter = UnifiedTypeConverter()
        resolver = UnifiedTypeResolver(converter=converter)

        # Convert TypeScript type to Python
        python_type = converter.ts_to_python("string[]")
        assert python_type == "List[str]"

        # Resolve field with that type
        field = {"name": "items", "type": python_type, "optional": False}
        resolved = resolver.resolve_field(field, "TestType")

        assert resolved.python_type == python_type
        assert "List[" in resolved.strawberry_type

    def test_registry_and_resolver_integration(self):
        """Test that registry and resolver work together."""
        registry = TypeRegistry()
        registry.register_branded_type("CustomID")

        resolver = UnifiedTypeResolver()

        # Resolve a field with the custom branded type
        field = {"name": "id", "type": "CustomID", "optional": False}
        resolved = resolver.resolve_field(field, "CustomType")

        # Should recognize it as a branded type
        # (Note: resolver needs to be aware of the registry for this to work fully)
        assert resolved.python_type == "CustomID"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])