def main(inputs):
    import json
    import os
    
    # Ensure output directory exists
    os.makedirs('output/test', exist_ok=True)
    
    # Save debug info to file
    with open('output/test/debug_inputs.json', 'w') as f:
        json.dump(inputs, f, indent=2)
    
    # Check what we actually received
    default_data = inputs.get("default", {})
    
    # Save processed data
    result = {
        "nodeType": default_data.get("nodeType", "MISSING"),
        "displayName": default_data.get("displayName", "MISSING"),
        "debug_info": f"Received keys: {list(default_data.keys())}"
    }
    
    with open('output/test/debug_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    return result