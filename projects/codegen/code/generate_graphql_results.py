"""Generate unified GraphQL result types from operations."""

import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader


@dataclass
class OperationInfo:
    """Information about a GraphQL operation for result generation."""
    name: str
    return_type: str
    extra_fields: list[dict[str, str]]


def load_operations_data() -> dict[str, Any]:
    """Load the operations data from the prepared JSON file."""
    operations_file = Path('.temp/ast_cache/graphql_operations.json')

    if not operations_file.exists():
        print(f"Warning: Operations file not found at {operations_file}")
        return {}

    with open(operations_file, 'r') as f:
        return json.load(f)


def determine_return_type(operation_name: str, operation_type: str) -> str:
    """Determine the appropriate return type for an operation."""

    # Map operation patterns to return types
    if 'List' in operation_name or 'list' in operation_name.lower():
        # List operations
        if 'Diagram' in operation_name:
            return 'list[DomainDiagramType]'
        elif 'Node' in operation_name:
            return 'list[DomainNodeType]'
        elif 'Person' in operation_name:
            return 'list[DomainPersonType]'
        elif 'Execution' in operation_name:
            return 'list[ExecutionStateType]'
        elif 'ApiKey' in operation_name:
            return 'list[DomainApiKeyType]'
        elif 'Conversation' in operation_name:
            return 'list[ConversationType]'
        else:
            return 'list[JSON]'

    # Single entity operations
    if 'Diagram' in operation_name:
        return 'DomainDiagramType'
    elif 'Node' in operation_name:
        return 'DomainNodeType'
    elif 'Person' in operation_name:
        return 'DomainPersonType'
    elif 'Execution' in operation_name:
        return 'ExecutionStateType'
    elif 'ApiKey' in operation_name:
        return 'DomainApiKeyType'
    elif 'Conversation' in operation_name:
        return 'ConversationType'
    elif 'Delete' in operation_name:
        return 'None'
    elif 'File' in operation_name:
        return 'JSON'
    elif 'Test' in operation_name:
        return 'JSON'
    elif 'Convert' in operation_name or 'Format' in operation_name:
        return 'str'
    elif 'Validate' in operation_name or 'Validation' in operation_name:
        return 'bool'
    elif 'CliSession' in operation_name or 'Interactive' in operation_name:
        return 'JSON'
    elif operation_type == 'MUTATION':
        # Default for mutations
        return 'JSON'
    else:
        # Default for queries
        return 'Any'


def extract_extra_fields(operation_name: str) -> list[dict[str, str]]:
    """Extract any extra fields that should be included in specific result types."""
    extra_fields = []

    # Add operation-specific fields
    if 'Execution' in operation_name:
        if 'List' not in operation_name:
            extra_fields.append({'name': 'execution_id', 'type': 'str'})

    if 'Delete' in operation_name:
        extra_fields.append({'name': 'deleted_id', 'type': 'str'})
        extra_fields.append({'name': 'deleted_count', 'type': 'int'})

    if 'File' in operation_name:
        extra_fields.extend([
            {'name': 'path', 'type': 'str'},
            {'name': 'content', 'type': 'str'},
            {'name': 'size_bytes', 'type': 'int'},
            {'name': 'content_type', 'type': 'str'}
        ])

    if 'Test' in operation_name:
        extra_fields.extend([
            {'name': 'test_name', 'type': 'str'},
            {'name': 'duration_ms', 'type': 'float'},
            {'name': 'model_info', 'type': 'JSON'}
        ])

    if 'Validation' in operation_name or 'Validate' in operation_name:
        extra_fields.extend([
            {'name': 'warnings', 'type': 'list[str]'},
            {'name': 'errors', 'type': 'list[str]'},
            {'name': 'is_valid', 'type': 'bool'}
        ])

    if 'CliSession' in operation_name:
        extra_fields.extend([
            {'name': 'session_id', 'type': 'str'},
            {'name': 'execution_id', 'type': 'str'}
        ])

    if 'Interactive' in operation_name:
        extra_fields.extend([
            {'name': 'node_id', 'type': 'str'},
            {'name': 'execution_id', 'type': 'str'},
            {'name': 'response_data', 'type': 'JSON'}
        ])

    if 'Batch' in operation_name:
        extra_fields.extend([
            {'name': 'succeeded_count', 'type': 'int'},
            {'name': 'failed_count', 'type': 'int'},
            {'name': 'partial_failures', 'type': 'list[JSON]'}
        ])

    if 'List' in operation_name:
        extra_fields.extend([
            {'name': 'total_count', 'type': 'int'},
            {'name': 'has_more', 'type': 'bool'}
        ])
        if 'Execution' in operation_name:
            extra_fields.append({'name': 'active_count', 'type': 'int'})

    return extra_fields


def prepare_operations_for_template(operations_data: dict[str, Any]) -> list[OperationInfo]:
    """Prepare operation information for template rendering."""
    operations = []

    # Extract operations from the data
    if 'operations' in operations_data:
        for op_name, op_data in operations_data['operations'].items():
            operation_type = op_data.get('type', 'QUERY')

            # Skip subscription operations for now (they have different patterns)
            if operation_type == 'SUBSCRIPTION':
                continue

            return_type = determine_return_type(op_name, operation_type)
            extra_fields = extract_extra_fields(op_name)

            operations.append(OperationInfo(
                name=op_name,
                return_type=return_type,
                extra_fields=extra_fields
            ))

    return operations


def generate_results_file(output_path: Path) -> None:
    """Generate the unified results.py file."""

    # Load operations data
    operations_data = load_operations_data()

    # Prepare operations for template
    operations = prepare_operations_for_template(operations_data)

    # Set up Jinja2 environment
    template_dir = Path('projects/codegen/templates/strawberry')
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True
    )

    # Load and render template
    template = env.get_template('strawberry_results.j2')
    rendered = template.render(operations=operations)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(rendered)

    print(f"Generated unified results file: {output_path}")


def main():
    """Main entry point."""
    output_path = Path('dipeo/diagram_generated_staged/graphql/results.py')
    generate_results_file(output_path)


if __name__ == '__main__':
    main()
