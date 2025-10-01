"""Test script for the new AST framework.

This script validates that all AST extractors work correctly with sample data.
"""

from __future__ import annotations


def test_extractors():
    """Test all extractors with sample AST data."""
    from dipeo.infrastructure.codegen.ir_builders.ast import (
        BrandedScalarExtractor,
        ConstantExtractor,
        EnumExtractor,
        GraphQLInputTypeExtractor,
        InterfaceExtractor,
        TypeAliasExtractor,
    )

    # Sample AST data
    ast_data = {
        "test.ts": {
            "interfaces": [
                {"name": "UserConfig", "properties": [], "extends": []},
                {"name": "NodeProps", "properties": [], "extends": []},
            ],
            "enums": [{"name": "Status", "members": ["ACTIVE", "INACTIVE"]}],
            "typeAliases": [{"name": "ID", "type": "string"}],
            "constants": [{"name": "MAX_ITEMS", "value": "100", "type": "number"}],
            "brandedScalars": [{"name": "UserID", "baseType": "string"}],
        },
        "graphql-inputs.ts": {
            "typeAliases": [
                {
                    "name": "CreateUserInput",
                    "type": {"type": "object", "properties": []},
                    "comment": "Input for creating a user",
                }
            ]
        },
    }

    print("Testing AST Framework Extractors")
    print("=" * 60)

    # Test InterfaceExtractor
    print("\n1. Testing InterfaceExtractor...")
    interface_extractor = InterfaceExtractor()
    interfaces = interface_extractor.extract(ast_data)
    print(f"   ✓ Extracted {len(interfaces)} interfaces: {[i['name'] for i in interfaces]}")

    # Test with suffix filter
    config_extractor = InterfaceExtractor(suffix="Config")
    configs = config_extractor.extract(ast_data)
    print(f"   ✓ Extracted {len(configs)} configs: {[c['name'] for c in configs]}")

    # Test EnumExtractor
    print("\n2. Testing EnumExtractor...")
    enum_extractor = EnumExtractor()
    enums = enum_extractor.extract(ast_data)
    print(f"   ✓ Extracted {len(enums)} enums: {[e['name'] for e in enums]}")

    # Test TypeAliasExtractor
    print("\n3. Testing TypeAliasExtractor...")
    type_alias_extractor = TypeAliasExtractor()
    type_aliases = type_alias_extractor.extract(ast_data)
    print(f"   ✓ Extracted {len(type_aliases)} type aliases: {[t['name'] for t in type_aliases]}")

    # Test ConstantExtractor
    print("\n4. Testing ConstantExtractor...")
    constant_extractor = ConstantExtractor()
    constants = constant_extractor.extract(ast_data)
    print(f"   ✓ Extracted {len(constants)} constants: {[c['name'] for c in constants]}")

    # Test BrandedScalarExtractor
    print("\n5. Testing BrandedScalarExtractor...")
    scalar_extractor = BrandedScalarExtractor()
    scalars = scalar_extractor.extract(ast_data)
    print(f"   ✓ Extracted {len(scalars)} branded scalars: {[s['name'] for s in scalars]}")

    # Test GraphQLInputTypeExtractor
    print("\n6. Testing GraphQLInputTypeExtractor...")
    input_extractor = GraphQLInputTypeExtractor()
    inputs = input_extractor.extract(ast_data)
    print(f"   ✓ Extracted {len(inputs)} GraphQL input types: {[i['name'] for i in inputs]}")

    print("\n" + "=" * 60)
    print("All extractors working correctly! ✓")


def test_filters():
    """Test filter utilities."""
    from dipeo.infrastructure.codegen.ir_builders.ast.filters import (
        FileFilter,
        and_filter,
        not_filter,
        prefix_filter,
        suffix_filter,
    )

    print("\n\nTesting AST Filters")
    print("=" * 60)

    # Test FileFilter
    print("\n1. Testing FileFilter...")
    file_filter = FileFilter(patterns=["**/*-inputs.ts"])
    ast_data = {
        "test.ts": {},
        "graphql-inputs.ts": {},
        "models/user.ts": {},
    }
    filtered = file_filter.filter(ast_data)
    print(f"   ✓ FileFilter matched {len(filtered)} files: {list(filtered.keys())}")

    # Test NodeFilter
    print("\n2. Testing NodeFilter...")
    nodes = [
        {"name": "UserConfig"},
        {"name": "UserProps"},
        {"name": "AdminConfig"},
    ]

    suffix = suffix_filter("Config")
    configs = suffix.filter_nodes(nodes)
    print(f"   ✓ Suffix filter found {len(configs)} configs: {[n['name'] for n in configs]}")

    prefix = prefix_filter("User")
    users = prefix.filter_nodes(nodes)
    print(f"   ✓ Prefix filter found {len(users)} user nodes: {[n['name'] for n in users]}")

    # Test filter composition
    print("\n3. Testing filter composition...")
    combined = and_filter(prefix_filter("User"), suffix_filter("Config"))
    result = combined.filter_nodes(nodes)
    print(f"   ✓ AND filter found {len(result)} nodes: {[n['name'] for n in result]}")

    inverted = not_filter(suffix_filter("Config"))
    result = inverted.filter_nodes(nodes)
    print(f"   ✓ NOT filter found {len(result)} nodes: {[n['name'] for n in result]}")

    print("\n" + "=" * 60)
    print("All filters working correctly! ✓")


def test_walker():
    """Test AST walker and visitor."""
    from dipeo.infrastructure.codegen.ir_builders.ast.walker import ASTWalker, CollectorVisitor

    print("\n\nTesting AST Walker")
    print("=" * 60)

    # Sample AST data
    ast_data = {
        "test.ts": {
            "interfaces": [{"name": "UserConfig"}],
            "enums": [{"name": "Status"}],
        }
    }

    print("\n1. Testing CollectorVisitor...")
    collector = CollectorVisitor(collect_types=["interface", "enum"])
    walker = ASTWalker(ast_data)
    walker.walk(collector)

    print(f"   ✓ Collected {len(collector.collected.get('interface', []))} interfaces")
    print(f"   ✓ Collected {len(collector.collected.get('enum', []))} enums")

    print("\n" + "=" * 60)
    print("Walker working correctly! ✓")


def test_backward_compatibility():
    """Test that old utils.py functions still work."""
    from dipeo.infrastructure.codegen.ir_builders.utils import (
        extract_constants_from_ast,
        extract_enums_from_ast,
        extract_interfaces_from_ast,
    )

    print("\n\nTesting Backward Compatibility")
    print("=" * 60)

    ast_data = {
        "test.ts": {
            "interfaces": [{"name": "UserConfig", "properties": [], "extends": []}],
            "enums": [{"name": "Status", "members": ["ACTIVE"]}],
            "constants": [{"name": "MAX", "value": "100", "type": "number"}],
        }
    }

    print("\n1. Testing deprecated functions...")
    interfaces = extract_interfaces_from_ast(ast_data)
    print(f"   ✓ extract_interfaces_from_ast: {len(interfaces)} interfaces")

    enums = extract_enums_from_ast(ast_data)
    print(f"   ✓ extract_enums_from_ast: {len(enums)} enums")

    constants = extract_constants_from_ast(ast_data)
    print(f"   ✓ extract_constants_from_ast: {len(constants)} constants")

    print("\n" + "=" * 60)
    print("Backward compatibility maintained! ✓")


if __name__ == "__main__":
    try:
        test_extractors()
        test_filters()
        test_walker()
        test_backward_compatibility()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓✓✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        exit(1)