def main(inputs):
    generation_result = inputs.get('generation_result', {})
    
    print(f"\n=== Python Domain Models Generation Complete ===")
    print(f"Generated {generation_result.get('models_count', 0)} models")
    print(f"Generated {generation_result.get('enums_count', 0)} enums")
    print(f"Generated {generation_result.get('type_aliases_count', 0)} type aliases")
    print(f"\nOutput written to: dipeo/diagram_generated_staged/domain_models.py")
    
    result = {
        'status': 'success',
        'message': 'Python domain models generated successfully',
        'details': generation_result
    }
    
    return result