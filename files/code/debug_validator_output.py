import json

def main(inputs):
    """Debug function to inspect all inputs and their structure."""
    print("\n=== DEBUG VALIDATOR OUTPUT ===")
    print(f"Number of inputs: {len(inputs)}")
    print(f"Input keys: {list(inputs.keys())}")
    
    # Detailed inspection of each input
    for key, value in inputs.items():
        print(f"\n--- Input '{key}' ---")
        print(f"Type: {type(value).__name__}")
        
        if isinstance(value, dict):
            print(f"Keys: {list(value.keys())}")
            # Check for validation output structure
            if 'valid' in value:
                print(f"Valid: {value.get('valid')}")
                print(f"Has 'data' key: {'data' in value}")
                if 'data' in value:
                    data = value['data']
                    print(f"Data type: {type(data).__name__}")
                    if isinstance(data, dict):
                        print(f"Data keys: {list(data.keys())[:10]}")  # First 10 keys
                        if 'nodeType' in data:
                            print(f"NodeType: {data['nodeType']}")
        elif isinstance(value, str):
            print(f"String value (first 200 chars): {value[:200]}")
        else:
            print(f"Value: {str(value)[:200]}")
    
    # Try different ways to access the data
    print("\n--- Attempting to extract spec data ---")
    
    # Method 1: Direct raw_data
    if 'raw_data' in inputs:
        print("Found 'raw_data' input")
        raw_data = inputs['raw_data']
        if isinstance(raw_data, dict) and 'nodeType' in raw_data:
            print(f"Success! Found nodeType: {raw_data['nodeType']}")
            return {"success": True, "spec": raw_data}
    
    # Method 2: Check for validation result structure
    for key, value in inputs.items():
        if isinstance(value, dict) and 'valid' in value and 'data' in value:
            print(f"Found validation result in '{key}'")
            data = value['data']
            if isinstance(data, dict) and 'nodeType' in data:
                print(f"Success! Found nodeType: {data['nodeType']}")
                return {"success": True, "spec": data}
    
    # Method 3: Check for direct spec data
    for key, value in inputs.items():
        if isinstance(value, dict) and 'nodeType' in value:
            print(f"Found spec data directly in '{key}'")
            print(f"Success! Found nodeType: {value['nodeType']}")
            return {"success": True, "spec": value}
    
    print("\nNo spec data found!")
    return {"success": False, "message": "Could not find spec data"}