"""Generate summaries for model generation processes."""

from datetime import datetime


def generate_field_configs_summary(node_configs: list) -> dict:
    """Generate summary for field configurations generation"""
    print(f"\n=== Field Configurations Generation Complete ===")
    print(f"Generated field configs for {len(node_configs)} node types")
    print(f"Output written to:")
    print(f"  - apps/web/src/__generated__/nodes/fields.ts")
    print(f"  - dipeo/diagram_generated/field-configs.json")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    return {
        'status': 'success',
        'message': 'Field configurations generated successfully',
        'node_types_count': len(node_configs)
    }


def generate_graphql_schema_summary(graphql_types: dict) -> dict:
    """Generate summary for GraphQL schema generation"""
    print(f"\n=== GraphQL Schema Generation Complete ===")
    print(f"Generated:")
    print(f"  - {len(graphql_types.get('scalars', []))} scalars")
    print(f"  - {len(graphql_types.get('enums', []))} enums")
    print(f"  - {len(graphql_types.get('types', []))} types")
    print(f"  - {len(graphql_types.get('input_types', []))} input types")
    print(f"Output written to: dipeo/diagram_generated/domain-schema.graphql")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    return {
        'status': 'success',
        'message': 'GraphQL schema generated successfully'
    }


def generate_python_models_summary(generation_result: dict) -> dict:
    """Generate summary for Python models generation"""
    print(f"\n=== Python Domain Models Generation Complete ===")
    print(f"Generated {generation_result.get('models_count', 0)} models")
    print(f"Generated {generation_result.get('enums_count', 0)} enums")
    print(f"Generated {generation_result.get('type_aliases_count', 0)} type aliases")
    print(f"\nOutput written to: dipeo/models/models.py")
    
    return {
        'status': 'success',
        'message': 'Python domain models generated successfully',
        'details': generation_result
    }


def generate_conversions_summary(node_type_map: dict) -> dict:
    """Generate summary for conversions generation"""
    print(f"\n=== Domain Model Conversions Generation Complete ===")
    print(f"Generated mappings for {len(node_type_map)} node types")
    print(f"Output written to: dipeo/models/conversions.py")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    return {
        'status': 'success',
        'message': 'Domain model conversions generated successfully',
        'node_types_count': len(node_type_map)
    }


def generate_static_nodes_summary(static_nodes_data: dict) -> dict:
    """Generate summary for static nodes generation"""
    node_classes = static_nodes_data.get('node_classes', [])
    
    print(f"\n=== Static Nodes Generation Complete ===")
    print(f"Generated {len(node_classes)} node classes:")
    for nc in node_classes:
        print(f"  - {nc['class_name']}")
    print(f"\nOutput written to: dipeo/diagram_generated/generated_nodes.py")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    return {
        'status': 'success',
        'message': 'Static nodes generated successfully',
        'node_classes_count': len(node_classes)
    }


def generate_zod_schemas_summary(schemas: list, enum_schemas: dict) -> dict:
    """Generate summary for Zod schemas generation"""
    print(f"\n=== Zod Schemas Generation Complete ===")
    print(f"Generated schemas for {len(schemas)} node types")
    print(f"Generated {len(enum_schemas)} enum schemas")
    print(f"Output written to: apps/web/src/features/diagram-editor/config/nodes/generated-schemas.ts")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    return {
        'status': 'success',
        'message': 'Zod schemas generated successfully',
        'node_types_count': len(schemas),
        'enum_schemas_count': len(enum_schemas)
    }


# Main entry points for different summary types
def main(inputs: dict) -> dict:
    """Main entry point - determines which summary to generate based on inputs"""
    # Detect which summary type based on inputs
    if 'node_configs' in inputs:
        return generate_field_configs_summary(inputs['node_configs'])
    elif 'graphql_types' in inputs:
        return generate_graphql_schema_summary(inputs['graphql_types'])
    elif 'generation_result' in inputs:
        return generate_python_models_summary(inputs['generation_result'])
    elif 'node_type_map' in inputs:
        return generate_conversions_summary(inputs['node_type_map'])
    elif 'static_nodes_data' in inputs:
        return generate_static_nodes_summary(inputs['static_nodes_data'])
    elif 'schemas' in inputs and 'enum_schemas' in inputs:
        return generate_zod_schemas_summary(inputs['schemas'], inputs['enum_schemas'])
    else:
        raise ValueError("Unknown summary type - no recognized inputs")