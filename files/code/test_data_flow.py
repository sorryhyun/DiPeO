import json

def main(inputs):
    print(f"DEBUG: Received inputs: {list(inputs.keys())}")
    for key, value in inputs.items():
        value_str = str(value)[:100] if not isinstance(value, dict) else f"dict with keys: {list(value.keys())}"
        print(f"DEBUG: {key} = {type(value).__name__} - {value_str}")
    
    # The validation node outputs a dict with 'valid', 'data', etc.
    raw_data = inputs.get("raw_data", {})
    print(f"DEBUG: raw_data type: {type(raw_data).__name__}")
    print(f"DEBUG: raw_data keys: {list(raw_data.keys())}")
    
    # Extract the actual spec data from raw_data.data
    spec_data = raw_data.get("data", {})
    print(f"DEBUG: spec_data type: {type(spec_data).__name__}")
    
    if isinstance(spec_data, dict):
        print(f"DEBUG: spec_data keys: {list(spec_data.keys())}")
        if "nodeType" in spec_data:
            print(f"DEBUG: Found nodeType: {spec_data['nodeType']}")
            print(f"DEBUG: Full spec data:")
            print(json.dumps(spec_data, indent=2))

    return {"result": "Debug complete", "data": spec_data}
