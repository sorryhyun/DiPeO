#!/usr/bin/env python3
"""Automatically register generated nodes in the codebase."""

import json
import re
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path.cwd()

def load_all_node_specs() -> List[Dict[str, Any]]:
    """Load all node specifications from the specs directory."""
    spec_dir = BASE_DIR / "files/codegen/specifications/nodes"
    specs = []
    for spec_file in spec_dir.glob("*.json"):
        spec = json.loads(spec_file.read_text())
        specs.append(spec)
    return specs

def camel_case(s: str) -> str:
    """Convert to camelCase."""
    parts = s.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])

def pascal_case(s: str) -> str:
    """Convert to PascalCase."""
    return ''.join(part.capitalize() for part in s.split('_'))

def snake_case(s: str) -> str:
    """Convert to snake_case."""
    return s

def register_node_type_map(specs: List[Dict[str, Any]]):
    """Update NODE_TYPE_MAP in conversions.ts"""
    conv_file = BASE_DIR / "dipeo/models/src/conversions.ts"
    content = conv_file.read_text()
    
    # Find NODE_TYPE_MAP section
    map_start = content.find("export const NODE_TYPE_MAP = {")
    if map_start == -1:
        print("❌ Could not find NODE_TYPE_MAP in conversions.ts")
        return
    
    map_end = content.find("};", map_start)
    
    # Build new entries
    new_entries = []
    for spec in specs:
        node_type = spec['nodeType']
        pascal = pascal_case(node_type)
        entry = f'  {node_type}: "{pascal}Node"'
        new_entries.append(entry)
    
    # Replace map content
    new_map = f"export const NODE_TYPE_MAP = {{\n{',\\n'.join(new_entries)}\n}};"
    new_content = content[:map_start] + new_map + content[map_end + 2:]
    
    conv_file.write_text(new_content)
    print(f"✅ Updated NODE_TYPE_MAP with {len(specs)} node types")

def register_graphql_unions(specs: List[Dict[str, Any]]):
    """Update GraphQL schema unions."""
    schema_file = BASE_DIR / "apps/server/src/dipeo_server/api/graphql/schema/nodes.graphql"
    if not schema_file.exists():
        print("❌ GraphQL schema file not found")
        return
    
    content = schema_file.read_text()
    
    # Build union types
    node_types = []
    config_types = []
    for spec in specs:
        pascal = pascal_case(spec['nodeType'])
        node_types.append(f"{pascal}Node")
        config_types.append(f"{pascal}NodeConfig")
    
    # Update Node union
    node_union = f"union Node = {' | '.join(node_types)}"
    config_union = f"union NodeConfig = {' | '.join(config_types)}"
    
    # Replace unions in content
    content = re.sub(r'union Node = [^\n]+', node_union, content)
    content = re.sub(r'union NodeConfig = [^\n]+', config_union, content)
    
    schema_file.write_text(content)
    print(f"✅ Updated GraphQL unions with {len(specs)} node types")

def register_node_configs(specs: List[Dict[str, Any]]):
    """Generate nodeRegistry.ts file."""
    registry_file = BASE_DIR / "apps/web/src/features/diagram/config/nodeRegistry.ts"
    
    imports = []
    registrations = []
    
    for spec in specs:
        node_type = spec['nodeType']
        camel = camel_case(node_type)
        imports.append(f"import {{ {camel}Config }} from '@/__generated__/nodes/{node_type}NodeConfig';")
        registrations.append(f"  registerNodeConfig({camel}Config);")
    
    content = f"""// Auto-generated node registry
import {{ registerNodeConfig }} from '@/features/diagram-editor/config/nodeRegistry';

{chr(10).join(imports)}

export function registerAllNodes() {{
{chr(10).join(registrations)}
}}

// Call this on app initialization
registerAllNodes();
"""
    
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    registry_file.write_text(content)
    print(f"✅ Generated nodeRegistry.ts with {len(specs)} node configs")

def register_python_nodes(specs: List[Dict[str, Any]]):
    """Update generated_nodes.py."""
    nodes_file = BASE_DIR / "dipeo/core/static/generated_nodes.py"
    
    imports = []
    exports = []
    
    for spec in specs:
        snake = snake_case(spec['nodeType'])
        pascal = pascal_case(spec['nodeType'])
        imports.append(f"from .nodes.{snake}_node import {pascal}Node")
        exports.append(f'    "{pascal}Node"')
    
    content = f'''"""Auto-generated node imports and exports."""

{chr(10).join(imports)}

__all__ = [
{chr(10).join(exports)},
]
'''
    
    nodes_file.write_text(content)
    print(f"✅ Updated generated_nodes.py with {len(specs)} nodes")

def generate_handler_stubs(specs: List[Dict[str, Any]]):
    """Generate handler stubs for nodes that don't have them."""
    handlers_dir = BASE_DIR / "dipeo/application/execution/handlers"
    handlers_dir.mkdir(parents=True, exist_ok=True)
    
    generated_count = 0
    for spec in specs:
        snake = snake_case(spec['nodeType'])
        handler_file = handlers_dir / f"{snake}.py"
        
        if not handler_file.exists():
            pascal = pascal_case(spec['nodeType'])
            content = f'''"""Handler for {pascal}Node."""

from typing import Any, Dict
from dipeo.core.models import {pascal}Node
from dipeo.core.context import ExecutionContext

async def handle_{snake}_node(
    node: {pascal}Node,
    context: ExecutionContext,
    inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle {pascal}Node execution."""
    # TODO: Implement {snake} node logic
    return {{
        "result": f"Executed {{node.id}} with inputs: {{inputs}}"
    }}
'''
            handler_file.write_text(content)
            generated_count += 1
    
    print(f"✅ Generated {generated_count} new handler stubs")

def main():
    """Run all registration tasks."""
    print("🔧 Auto-registering generated nodes...")
    
    # Load all node specs
    specs = load_all_node_specs()
    print(f"📦 Found {len(specs)} node specifications")
    
    # Run registration tasks
    register_node_type_map(specs)
    register_graphql_unions(specs)
    register_node_configs(specs)
    register_python_nodes(specs)
    generate_handler_stubs(specs)
    
    print("\n✨ Node registration complete!")

if __name__ == "__main__":
    main()