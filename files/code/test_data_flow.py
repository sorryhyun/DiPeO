import json

def main(inputs):
    print("="*50)
    print("DEBUG OUTPUT NODE")
    print("="*50)
    print(f"Input keys: {list(inputs.keys())}")
    
    for key, value in inputs.items():
        print(f"\nKey: {key}")
        print(f"Type: {type(value)}")
        if isinstance(value, str) and len(value) < 500:
            print(f"Value preview: {value[:200]}...")
        elif isinstance(value, dict):
            print(f"Dict keys: {list(value.keys())}")
            if value:
                print(f"Dict content: {str(value)[:200]}...")
        else:
            print(f"Value length: {len(str(value))}")
    
    # Try to parse the spec
    default_value = inputs.get('default', '')
    if isinstance(default_value, str):
        try:
            parsed = json.loads(default_value)
            print(f"\nParsed JSON type: {type(parsed)}")
            if isinstance(parsed, dict):
                print(f"Parsed keys: {list(parsed.keys())[:10]}")
                if 'nodeType' in parsed:
                    print(f"Found nodeType: {parsed['nodeType']}")
        except:
            print("\nFailed to parse as JSON")
    
    return {"debug": "complete", "inputs_examined": list(inputs.keys())}