"""Generate Python handler stubs from TypeScript node specifications."""
import os
import sys
from pathlib import Path
from typing import Any

from projects.codegen.code.core.utils import parse_dipeo_output

# Add DiPeO base to path
sys.path.append(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))


def parse_jsdoc_annotations(jsdoc: str | None) -> dict[str, Any]:
    """Parse JSDoc comments for @dipeo annotations.

    Extracts:
    - @dipeo.services: List of required services
    - @dipeo.timeout: Timeout value in milliseconds
    """
    if not jsdoc:
        return {}

    annotations = {}
    lines = jsdoc.split('\n')

    for line in lines:
        line = line.strip()

        # Parse @dipeo.services annotation
        if '@dipeo.services' in line:
            # Extract array value like ["llm", "kvStore"]
            start = line.find('[')
            end = line.find(']')
            if start != -1 and end != -1:
                services_str = line[start:end+1]
                # Parse as JSON array using the utility
                services = parse_dipeo_output(services_str)
                if services:
                    annotations['services'] = services

        # Parse @dipeo.timeout annotation
        elif '@dipeo.timeout' in line:
            # Extract numeric value
            parts = line.split('@dipeo.timeout')
            if len(parts) > 1:
                timeout_str = parts[1].strip()
                # Extract first number from the string
                timeout_num = ''
                for char in timeout_str:
                    if char.isdigit():
                        timeout_num += char
                    elif timeout_num:
                        break
                if timeout_num:
                    annotations['timeout'] = int(timeout_num)

    return annotations


def extract_handler_stub_data(
    ast_data: dict,
    node_specs: dict,
    existing_handlers: list[str]
) -> list[dict[str, Any]]:
    """Extract data for generating handler stubs.

    Args:
        ast_data: Parsed TypeScript AST data
        node_specs: Node specification data
        existing_handlers: List of node types that already have handlers

    Returns:
        List of handler stub configurations
    """
    handler_stubs = []
    interfaces = ast_data.get('interfaces', [])

    # Build interface lookup
    interface_lookup = {
        iface['name']: iface
        for iface in interfaces
    }

    # Process each node specification
    for spec in node_specs:
        node_type = spec.get('nodeType')
        if not node_type:
            continue

        # Skip if handler already exists
        if node_type.lower() in [h.lower() for h in existing_handlers]:
            continue

        # Find the corresponding data interface
        interface_name = f"{node_type.replace('_', '')}NodeData"
        data_interface = None

        # Search for the interface
        for iface_name, iface in interface_lookup.items():
            if iface_name.lower() == interface_name.lower():
                data_interface = iface
                break

        if not data_interface:
            # Try alternative naming patterns
            alt_names = [
                f"{node_type}Data",
                f"{node_type.title().replace('_', '')}NodeData",
                f"{node_type.title().replace('_', '')}Data"
            ]
            for alt_name in alt_names:
                if alt_name in interface_lookup:
                    data_interface = interface_lookup[alt_name]
                    break

        # Parse JSDoc annotations if available
        jsdoc_annotations = {}
        if data_interface and 'jsdoc' in data_interface:
            jsdoc_annotations = parse_jsdoc_annotations(data_interface.get('jsdoc'))

        # Prepare handler stub data
        stub_data = {
            'node_type': node_type,
            'node_type_upper': node_type.upper(),
            'handler_class_name': f"{node_type.title().replace('_', '')}NodeHandler",
            'data_model_name': f"{node_type.title().replace('_', '')}NodeData",
            'display_name': spec.get('displayName', node_type.replace('_', ' ').title()),
            'services': jsdoc_annotations.get('services', []),
            'timeout': jsdoc_annotations.get('timeout'),
            'description': spec.get('description', ''),
            'category': spec.get('category', 'general')
        }

        handler_stubs.append(stub_data)

    return handler_stubs


def detect_existing_handlers() -> list[str]:
    """Detect which node types already have handlers implemented.

    Returns:
        List of node type strings that have existing handlers
    """
    handlers_dir = Path(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO')) / 'dipeo' / 'application' / 'execution' / 'handlers'
    existing_handlers = []

    if not handlers_dir.exists():
        return existing_handlers

    # Map of handler files/dirs to node types
    handler_mappings = {
        'api_job.py': 'api_job',
        'code_job': 'code_job',
        'condition': 'condition',
        'db.py': 'db',
        'endpoint.py': 'endpoint',
        'hook.py': 'hook',
        'integrated_api.py': 'integrated_api',
        'json_schema_validator.py': 'json_schema_validator',
        'person_job': 'person_job',
        'person_batch_job': 'person_batch_job',
        'start.py': 'start',
        'sub_diagram': 'sub_diagram',
        'template_job.py': 'template_job',
        'typescript_ast.py': 'typescript_ast',
        'user_response.py': 'user_response'
    }

    # Check for each known handler
    for item in handlers_dir.iterdir():
        name = item.name
        if name in handler_mappings:
            existing_handlers.append(handler_mappings[name])
        # Also check for pattern-based naming
        elif name.endswith('.py') and not name.startswith('_'):
            # Convert filename to node type (e.g., person_job.py -> person_job)
            node_type = name[:-3]  # Remove .py
            existing_handlers.append(node_type)
        elif item.is_dir() and (item / '__init__.py').exists():
            # Directory-based handler
            existing_handlers.append(item.name)

    return existing_handlers


def main(ast_data: dict, node_specs: dict) -> dict:
    """Main entry point for handler stub generation.

    Args:
        ast_data: Parsed TypeScript AST data
        node_specs: Node specification data

    Returns:
        Handler stub generation data
    """
    # Detect existing handlers
    existing_handlers = detect_existing_handlers()

    # Extract handler stub data
    handler_stubs = extract_handler_stub_data(
        ast_data,
        node_specs,
        existing_handlers
    )

    return {
        'handler_stubs': handler_stubs,
        'total_stubs': len(handler_stubs),
        'existing_handlers': existing_handlers,
        'message': f"Found {len(handler_stubs)} node types needing handler stubs"
    }


def generate_from_cache() -> dict:
    """Generate handler stubs from cached AST and spec data."""
    # Load cached AST data
    ast_cache_dir = Path(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO')) / '.temp' / 'ast_cache'
    specs_dir = Path(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO')) / 'temp' / 'specifications' / 'nodes'

    # Aggregate all AST data
    all_interfaces = []
    if ast_cache_dir.exists():
        for ast_file in ast_cache_dir.glob('*.json'):
            with ast_file.open() as f:
                content = f.read()
                ast_data = parse_dipeo_output(content)
                all_interfaces.extend(ast_data.get('interfaces', []))

    # Load node specifications
    node_specs = []
    if specs_dir.exists():
        for spec_file in specs_dir.glob('*.spec.ts.json'):
            with spec_file.open() as f:
                content = f.read()
                spec_data = parse_dipeo_output(content)
                if 'nodeType' in spec_data:
                    node_specs.append(spec_data)

    # Generate handler stub data
    ast_data = {'interfaces': all_interfaces}
    return main(ast_data, node_specs)
