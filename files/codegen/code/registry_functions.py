"""
Registry update functions for DiPeO code generation.
Manages registration of new node types across various system files.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List

# Get project root from environment or use current working directory
PROJECT_ROOT = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point - provides information about available functions."""
    return {
        "message": "DiPeO Registry Functions",
        "available_functions": [
            "update_node_registration",
            "update_graphql_registry",
            "update_frontend_exports",
            "update_python_handlers",
            "verify_registrations"
        ],
        "description": "Functions for updating various registry files"
    }


def update_node_registration(inputs: Dict[str, Any]) -> str:
    """
    Update the main node type registration in dipeo/application/container/node_registry.py
    
    Inputs:
        spec_data: Node specification data
        dry_run: Whether to just simulate the update (default: False)
    """
    spec_data = inputs.get('spec_data', {})
    dry_run = inputs.get('dry_run', False)
    
    node_type = spec_data.get('nodeType', '')
    if not node_type:
        return "Error: No node type specified"
    
    registry_file = PROJECT_ROOT / "dipeo/application/container/node_registry.py"
    
    # Read current registry
    if registry_file.exists():
        with open(registry_file, 'r') as f:
            content = f.read()
    else:
        # Create new registry file
        content = '''"""
Node type registry for DiPeO execution engine.
Auto-generated - do not edit manually.
"""

from typing import Dict, Type
from dipeo.core.node_types import NodeHandler

# Registry of node types to their handler classes
NODE_HANDLERS: Dict[str, Type[NodeHandler]] = {
    # Built-in nodes
    "start": StartNodeHandler,
    "endpoint": EndpointNodeHandler,
    "condition": ConditionNodeHandler,
    "person_job": PersonJobNodeHandler,
    "code_job": CodeJobNodeHandler,
    "api_job": ApiJobNodeHandler,
    "template_job": TemplateJobNodeHandler,
    
    # Generated nodes
}
'''
    
    # Check if node is already registered
    if f'"{node_type}"' in content:
        return f"Node type '{node_type}' is already registered"
    
    # Add new node registration
    handler_class = f"{spec_data.get('pascalCase', node_type.title())}NodeHandler"
    
    # Find the insertion point (after "# Generated nodes" comment)
    insertion_point = content.find("# Generated nodes")
    if insertion_point == -1:
        # Add the comment if it doesn't exist
        content = content.rstrip() + "\n    # Generated nodes\n}\n"
        insertion_point = content.find("# Generated nodes")
    
    # Find the next line after the comment
    next_line = content.find('\n', insertion_point) + 1
    
    # Insert the new registration
    new_registration = f'    "{node_type}": {handler_class},\n'
    content = content[:next_line] + new_registration + content[next_line:]
    
    # Add import for the handler
    import_line = f"from dipeo.application.execution.handlers.{node_type} import {handler_class}\n"
    
    # Find where to insert the import (after other handler imports)
    import_section = re.search(r'(from dipeo\.application\.execution\.handlers\.\w+ import \w+\n)+', content)
    if import_section:
        insert_pos = import_section.end()
        content = content[:insert_pos] + import_line + content[insert_pos:]
    else:
        # Insert after the last import
        last_import = content.rfind('import ')
        last_import_end = content.find('\n', last_import) + 1
        content = content[:last_import_end] + import_line + "\n" + content[last_import_end:]
    
    if not dry_run:
        with open(registry_file, 'w') as f:
            f.write(content)
        return f"Successfully registered node type '{node_type}' in {registry_file}"
    else:
        return f"Would register node type '{node_type}' in {registry_file}"


def update_graphql_registry(inputs: Dict[str, Any]) -> str:
    """
    Update GraphQL schema registry to include new node type.
    
    Inputs:
        spec_data: Node specification data
        dry_run: Whether to just simulate the update (default: False)
    """
    spec_data = inputs.get('spec_data', {})
    dry_run = inputs.get('dry_run', False)
    
    node_type = spec_data.get('nodeType', '')
    pascal_case = spec_data.get('pascalCase', node_type.title())
    
    registry_file = PROJECT_ROOT / "apps/server/src/dipeo_server/api/graphql/registry.py"
    
    # For GraphQL, we need to update the schema file
    schema_file = PROJECT_ROOT / "apps/server/src/dipeo_server/api/graphql/schema/nodes.graphql"
    
    if not schema_file.exists():
        return f"GraphQL schema file not found: {schema_file}"
    
    with open(schema_file, 'r') as f:
        content = f.read()
    
    # Check if already registered
    if f"{pascal_case}NodeData" in content:
        return f"Node type '{node_type}' already in GraphQL schema"
    
    # Add to NodeData union
    union_pattern = r'(union NodeData =[\s\S]*?)(\n\n)'
    
    def add_to_union(match):
        union_def = match.group(1)
        if not union_def.endswith('|'):
            union_def += '\n  |'
        union_def += f' {pascal_case}NodeData'
        return union_def + match.group(2)
    
    content = re.sub(union_pattern, add_to_union, content)
    
    # Add to NodeInput union  
    input_pattern = r'(union NodeInput =[\s\S]*?)(\n\n)'
    
    def add_to_input(match):
        union_def = match.group(1)
        if not union_def.endswith('|'):
            union_def += '\n  |'
        union_def += f' {pascal_case}NodeInput'
        return union_def + match.group(2)
    
    content = re.sub(input_pattern, add_to_input, content)
    
    if not dry_run:
        with open(schema_file, 'w') as f:
            f.write(content)
        return f"Successfully updated GraphQL schema for '{node_type}'"
    else:
        return f"Would update GraphQL schema for '{node_type}'"


def update_frontend_exports(inputs: Dict[str, Any]) -> str:
    """
    Update frontend index files to export new components.
    
    Inputs:
        spec_data: Node specification data
        files_generated: List of generated files
        dry_run: Whether to just simulate the update (default: False)
    """
    spec_data = inputs.get('spec_data', {})
    files_generated = inputs.get('files_generated', [])
    dry_run = inputs.get('dry_run', False)
    
    node_type = spec_data.get('nodeType', '')
    camel_case = spec_data.get('camelCase', '')
    pascal_case = spec_data.get('pascalCase', node_type.title())
    
    # Update component exports
    component_index = PROJECT_ROOT / "apps/web/src/features/diagram-editor/components/nodes/index.ts"
    
    if component_index.exists():
        with open(component_index, 'r') as f:
            content = f.read()
        
        # Check if already exported
        if f"export {{ {pascal_case}Node }}" not in content:
            # Add export
            export_line = f"export {{ {pascal_case}Node }} from './generated/{pascal_case}Node';\n"
            
            # Find insertion point (after other exports or at end)
            last_export = content.rfind('export {')
            if last_export != -1:
                insert_pos = content.find('\n', last_export) + 1
                content = content[:insert_pos] + export_line + content[insert_pos:]
            else:
                content += "\n" + export_line
            
            if not dry_run:
                with open(component_index, 'w') as f:
                    f.write(content)
    
    # Update config exports
    config_index = PROJECT_ROOT / "apps/web/src/features/diagram-editor/config/nodes/index.ts"
    
    if config_index.exists():
        with open(config_index, 'r') as f:
            content = f.read()
        
        # Add config export
        if f"{camel_case}Config" not in content:
            export_line = f"export {{ {camel_case}Config }} from './generated/{camel_case}Config';\n"
            export_line += f"export {{ {camel_case}Fields }} from './generated/{camel_case}Fields';\n"
            
            # Find insertion point
            last_export = content.rfind('export {')
            if last_export != -1:
                insert_pos = content.find('\n', last_export) + 1
                content = content[:insert_pos] + export_line + content[insert_pos:]
            else:
                content += "\n" + export_line
            
            if not dry_run:
                with open(config_index, 'w') as f:
                    f.write(content)
    
    return f"Successfully updated frontend exports for '{node_type}'"


def update_python_handlers(inputs: Dict[str, Any]) -> str:
    """
    Create or update Python handler registration.
    
    Inputs:
        spec_data: Node specification data
        dry_run: Whether to just simulate the update (default: False)
    """
    spec_data = inputs.get('spec_data', {})
    dry_run = inputs.get('dry_run', False)
    
    node_type = spec_data.get('nodeType', '')
    handler_file = PROJECT_ROOT / f"dipeo/application/execution/handlers/{node_type}.py"
    
    # Check if handler already exists
    if handler_file.exists():
        return f"Handler already exists: {handler_file}"
    
    # Create handler stub
    handler_content = f'''"""
Handler for {node_type} node type.
Auto-generated stub - implement the handle method.
"""

from typing import Dict, Any
from dipeo.core.node_types import NodeHandler, NodeResult
from dipeo.core.exceptions import NodeExecutionError


class {spec_data.get('pascalCase', node_type.title())}NodeHandler(NodeHandler):
    """Handler for {node_type} nodes."""
    
    async def handle(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> NodeResult:
        """
        Process {node_type} node.
        
        Args:
            inputs: Input data from connected nodes
            context: Execution context
            
        Returns:
            NodeResult with output data
        """
        # TODO: Implement {node_type} logic
        
        # Get node data
        node_data = self.node.data
        
        # Process inputs
        # ...
        
        # Return result
        return NodeResult(
            success=True,
            data={{"message": f"Executed {node_type} node: {{self.node.id}}"}}
        )
'''
    
    if not dry_run:
        handler_file.parent.mkdir(parents=True, exist_ok=True)
        with open(handler_file, 'w') as f:
            f.write(handler_content)
        return f"Created handler stub: {handler_file}"
    else:
        return f"Would create handler stub: {handler_file}"


def verify_registrations(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify that all registrations are complete for a node type.
    
    Inputs:
        spec_data: Node specification data
    """
    spec_data = inputs.get('spec_data', {})
    node_type = spec_data.get('nodeType', '')
    
    checks = {
        'node_registry': False,
        'graphql_schema': False,
        'frontend_exports': False,
        'handler_exists': False,
        'typescript_model': False,
        'python_model': False
    }
    
    issues = []
    
    # Check node registry
    registry_file = PROJECT_ROOT / "dipeo/application/container/node_registry.py"
    if registry_file.exists():
        with open(registry_file, 'r') as f:
            if f'"{node_type}"' in f.read():
                checks['node_registry'] = True
            else:
                issues.append(f"Node type '{node_type}' not found in node registry")
    
    # Check GraphQL schema
    schema_file = PROJECT_ROOT / "apps/server/src/dipeo_server/api/graphql/schema/nodes.graphql"
    if schema_file.exists():
        with open(schema_file, 'r') as f:
            content = f.read()
            if f"{spec_data.get('pascalCase', node_type.title())}NodeData" in content:
                checks['graphql_schema'] = True
            else:
                issues.append(f"Node type '{node_type}' not found in GraphQL schema")
    
    # Check handler
    handler_file = PROJECT_ROOT / f"dipeo/application/execution/handlers/{node_type}.py"
    if handler_file.exists():
        checks['handler_exists'] = True
    else:
        issues.append(f"Handler not found: {handler_file}")
    
    # Check TypeScript model
    ts_model = PROJECT_ROOT / f"dipeo/models/src/nodes/{node_type}Node.ts"
    if ts_model.exists():
        checks['typescript_model'] = True
    else:
        issues.append(f"TypeScript model not found: {ts_model}")
    
    all_valid = all(checks.values())
    
    return {
        'valid': all_valid,
        'checks': checks,
        'issues': issues,
        'summary': f"{'✓' if all_valid else '✗'} {sum(checks.values())}/{len(checks)} checks passed"
    }