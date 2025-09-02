"""Extract integration-specific definitions from TypeScript AST."""

from typing import Dict, Any, List


def extract_integration_enums(ast_data: dict) -> List[dict]:
    """Extract enum definitions from integration.ts AST data."""
    # The typescript_ast node returns enums directly
    enums_from_ast = ast_data.get('enums', [])
    
    # Initialize result
    enums = []
    
    # Process each enum
    for enum in enums_from_ast:
        enum_name = enum.get('name', '')
        description = enum.get('jsDoc', '') or f'{enum_name} enum values'
        members = enum.get('members', [])
        
        # Extract values
        values = []
        for member in members:
            member_name = member.get('name', '')
            member_value = member.get('value', member_name)
            
            if member_name:
                values.append({
                    'name': member_name,
                    'value': member_value,
                    'python_name': member_name  # Keep original case for Python
                })
        
        # Add to results
        if enum_name and values:
            enums.append({
                'name': enum_name,
                'description': description,
                'values': values
            })
    
    return enums


def extract_integration_interfaces(ast_data: dict) -> List[dict]:
    """Extract interface definitions that should be in integrations module."""
    interfaces_from_ast = ast_data.get('interfaces', [])
    
    # Filter for specific integration interfaces we want to include
    integration_interfaces = [
        'ToolConfig', 'WebSearchResult', 'ImageGenerationResult', 
        'ToolOutput', 'LLMRequestOptions'
    ]
    
    interfaces = []
    for interface in interfaces_from_ast:
        if interface.get('name') in integration_interfaces:
            interfaces.append(interface)
    
    return interfaces


def main(inputs: dict) -> dict:
    """Main entry point for integration extraction."""
    # When loading from file, the content comes as a JSON string in 'default'
    ast_json = inputs.get('default', {})
    
    # Parse JSON if it's a string
    if isinstance(ast_json, str):
        try:
            import json
            ast_data = json.loads(ast_json)
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            return {
                'enums': [],
                'interfaces': [],
                'imports': {
                    'from_enums': ['LLMService', 'APIServiceType', 'ToolType'],
                    'from_execution': ['TokenUsage']
                }
            }
    else:
        ast_data = ast_json
    
    # Extract both enums and interfaces
    enums = extract_integration_enums(ast_data)
    interfaces = extract_integration_interfaces(ast_data)
    
    # Return structured data
    return {
        'enums': enums,
        'interfaces': interfaces,
        'imports': {
            'from_enums': ['LLMService', 'APIServiceType', 'ToolType'],
            'from_execution': ['TokenUsage']
        }
    }