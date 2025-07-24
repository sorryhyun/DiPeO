"""Pure generator for frontend node registry."""
from typing import Dict, Any, List
from ...shared.template_env import create_template_env


def generate_node_registry(
    frontend_configs: List[Dict[str, Any]], 
    backend_metadata: List[Dict[str, Any]], 
    template_content: str
) -> str:
    """
    Pure function: Generate node registry that combines frontend and backend information.
    
    Args:
        frontend_configs: List of frontend node configurations
        backend_metadata: List of backend node metadata
        template_content: Jinja2 template content
        
    Returns:
        Generated TypeScript registry code
    """
    env = create_template_env()
    
    # Create a mapping of node types to their information
    node_map = {}
    
    # Add frontend configs
    for config in frontend_configs:
        node_type = config.get('node_type', '')
        if node_type:
            node_map[node_type] = {
                'type': node_type,
                'displayName': config.get('displayName', node_type),
                'component': f"{node_type.title().replace('_', '')}NodeComponent",
                'config': f"{node_type}Config",
                'fields': f"{node_type}Fields",
                'category': config.get('category', 'General'),
                'icon': config.get('icon', 'BoxIcon'),
                'color': config.get('color', '#6B7280'),
            }
    
    # Merge backend metadata
    for metadata in backend_metadata:
        node_type = metadata.get('node_type', '')
        if node_type in node_map:
            node_map[node_type].update({
                'handler': metadata.get('handler', f"{node_type}_handler"),
                'validator': metadata.get('validator', f"validate_{node_type}"),
                'executor': metadata.get('executor', f"execute_{node_type}"),
            })
    
    # Convert to sorted list
    registry_entries = sorted(node_map.values(), key=lambda x: x['type'])
    
    # Group by category
    categories = {}
    for entry in registry_entries:
        category = entry.get('category', 'General')
        if category not in categories:
            categories[category] = []
        categories[category].append(entry)
    
    # Prepare context
    context = {
        'registry_entries': registry_entries,
        'categories': categories,
        'node_types': [entry['type'] for entry in registry_entries],
        'imports': _generate_imports(registry_entries),
    }
    
    template = env.from_string(template_content)
    return template.render(context)


def _generate_imports(registry_entries: List[Dict[str, Any]]) -> List[str]:
    """Generate import statements for the registry."""
    imports = []
    
    for entry in registry_entries:
        node_type = entry['type']
        pascal_case = node_type.title().replace('_', '')
        
        # Import component
        imports.append(f"import {{ {pascal_case}NodeComponent }} from '../components/nodes/{pascal_case}Node';")
        
        # Import config
        imports.append(f"import {{ {node_type}Config }} from './nodes/{pascal_case}Config';")
        
        # Import fields
        imports.append(f"import {{ {node_type}Fields }} from '../core/config/fields/{pascal_case}Fields';")
    
    # Add icon imports
    unique_icons = set(entry.get('icon', 'BoxIcon') for entry in registry_entries)
    if unique_icons:
        imports.append(f"import {{ {', '.join(sorted(unique_icons))} }} from 'lucide-react';")
    
    return imports


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for code_job node.
    
    Args:
        inputs: Dictionary containing:
            - frontend_configs: List of frontend configurations
            - backend_metadata: List of backend metadata
            - template_content: Template string
            
    Returns:
        Dictionary with:
            - generated_code: The generated registry code
            - filename: Suggested filename for the output
    """
    frontend_configs = inputs.get('frontend_configs', [])
    backend_metadata = inputs.get('backend_metadata', [])
    template_content = inputs.get('template_content', '')
    
    if not template_content:
        raise ValueError("template_content is required")
    
    generated_code = generate_node_registry(
        frontend_configs, 
        backend_metadata, 
        template_content
    )
    
    return {
        'generated_code': generated_code,
        'filename': 'nodeRegistry.ts'
    }