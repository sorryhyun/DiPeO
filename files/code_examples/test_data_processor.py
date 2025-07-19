"""
Test processor for debugging object content type.
"""
import json

def process_data(inputs):
    """Process input data and return structured result."""
    print(f"Code job received inputs: {json.dumps(inputs, indent=2)}")
    
    test_data = inputs.get('test_data', {})
    print(f"test_data: {json.dumps(test_data, indent=2)}")
    
    # Return a structured object
    result = {
        'total_items': len(test_data.get('numbers', [])),
        'processing_time': 0.5,
        'results': {
            'original_value': test_data.get('test_value', 'not found'),
            'sum': sum(test_data.get('numbers', [])),
            'count': len(test_data.get('numbers', []))
        }
    }
    print(f"Code job returning: {json.dumps(result, indent=2)}")
    return result