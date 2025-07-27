"""Prepare field configuration data for template rendering."""
from datetime import datetime
from typing import Any, Dict, List, Union


def prepare_field_config_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare field configuration data for template rendering.
    
    Args:
        inputs: Input data containing node_configs
        
    Returns:
        Dictionary with node_configs and timestamp
    """
    # Get the extracted field configs - it returns a dict with 'node_configs' key
    field_configs_data = inputs.get('node_configs', {})
    
    # Extract the actual node configs array
    if isinstance(field_configs_data, dict):
        node_configs = field_configs_data.get('node_configs', [])
    else:
        node_configs = field_configs_data
    
    print(f"Preparing template data with {len(node_configs)} node configs")
    if node_configs:
        print(f"First node config keys: {list(node_configs[0].keys()) if node_configs else []}")
    
    result = {
        'node_configs': node_configs,
        'now': datetime.now().isoformat()
    }
    
    return result