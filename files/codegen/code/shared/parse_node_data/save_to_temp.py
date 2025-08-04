import json
import os


def main(inputs):
    """Save interface data to temporary file."""
    # Get interface data - handle both dict and string inputs
    if isinstance(inputs, str):
        # If inputs is a string, parse it as JSON
        interface_data = json.loads(inputs) if inputs else {}
    else:
        interface_data = inputs.get('interface_data', {})
    
    # Create temp directory if it doesn't exist
    temp_dir = '.temp/codegen/node_data'
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save to temp file
    node_type = interface_data.get('node_type', 'unknown')
    temp_file = os.path.join(temp_dir, f"{node_type}.json")
    
    with open(temp_file, 'w') as f:
        json.dump(interface_data, f, indent=2)
    
    return {"saved": temp_file}