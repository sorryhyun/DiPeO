# apps/server/src/utils/diagram_migrator.py
from typing import Dict, Any, List
import yaml
import uuid


class DiagramMigrator:
    """Validate and migrate diagram formats."""

    @staticmethod
    def migrate(diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate diagram from various formats to standard format."""
        # If it's YAML format, convert it first
        if isinstance(diagram, dict) and diagram.get('version') == '1.0' and 'workflow' in diagram:
            return DiagramMigrator.from_yaml_format(diagram)

        # Otherwise return as-is (already in correct format)
        return diagram.copy()

    @staticmethod
    def from_yaml_format(yaml_diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Convert YAML format to standard DiagramState format."""
        nodes = []
        arrows = []
        persons = []
        api_keys = []

        # Convert API keys
        for key_id, key_data in yaml_diagram.get('apiKeys', {}).items():
            api_keys.append({
                'id': key_id,
                'name': key_data['name'],
                'service': key_data['service']
            })

        # Convert persons
        for person_id, person_data in yaml_diagram.get('persons', {}).items():
            persons.append({
                'id': person_data.get('id', person_id),
                'label': DiagramMigrator._extract_label_from_id(person_data.get('id', person_id)),
                'modelName': person_data.get('model', 'gpt-4'),
                'service': person_data.get('service', 'chatgpt'),
                'apiKeyId': person_data.get('apiKeyId'),
                'systemPrompt': person_data.get('system')
            })

        # Convert workflow steps to nodes and arrows
        for step in yaml_diagram.get('workflow', []):
            node = DiagramMigrator._yaml_step_to_node(step)
            if node:
                nodes.append(node)

                # Create arrows from connections
                for conn in step.get('connections', []):
                    arrow_id = f"arrow-{uuid.uuid4().hex[:6]}"
                    arrow_dict = {
                        'id': arrow_id,
                        'source': step['id'],
                        'target': conn['to'],
                        'type': 'customArrow',
                        'data': {
                            'id': arrow_id,
                            'sourceBlockId': step['id'],
                            'targetBlockId': conn['to'],
                            'label': conn.get('label', 'flow'),
                            'contentType': conn.get('content_type'),
                            'branch': conn.get('branch'),
                            'objectKeyPath': conn.get('object_key_path'),
                            'controlPointOffsetX': conn.get('control_offset', {}).get('x', 0),
                            'controlPointOffsetY': conn.get('control_offset', {}).get('y', 0)
                        }
                    }
                    
                    # Only add handles if they have values
                    if conn.get('source_handle'):
                        arrow_dict['sourceHandle'] = conn['source_handle']
                    if conn.get('target_handle'):
                        arrow_dict['targetHandle'] = conn['target_handle']
                    
                    arrows.append(arrow_dict)

        return {
            'nodes': nodes,
            'arrows': arrows,
            'persons': persons,
            'apiKeys': api_keys
        }

    @staticmethod
    def _yaml_step_to_node(step: Dict[str, Any]) -> Dict[str, Any]:
        """Convert YAML workflow step to node format."""
        base_node = {
            'id': step['id'],
            'type': step['type'],
            'position': step.get('position', {'x': 0, 'y': 0}),
            'data': {
                'id': step['id'],
                'label': step.get('label', DiagramMigrator._extract_label_from_id(step['id']))
            }
        }

        # Add type-specific data
        if step['type'] == 'startNode':
            base_node['data']['type'] = 'start'

        elif step['type'] == 'personjobNode':
            base_node['data'].update({
                'type': 'person_job',
                'personId': step.get('person'),
                'defaultPrompt': step.get('prompt', ''),
                'firstOnlyPrompt': step.get('first_prompt', ''),
                'contextCleaningRule': step.get('forget', 'upon_request'),
                'iterationCount': step.get('max_iterations', 1),
                'mode': step.get('mode', 'sync')
            })

        elif step['type'] == 'conditionNode':
            base_node['data'].update({
                'type': 'condition',
                'conditionType': step.get('condition_type', 'expression'),
                'expression': step.get('expression', ''),
                'maxIterations': step.get('max_iterations')
            })

        elif step['type'] == 'dbNode':
            base_node['data'].update({
                'type': 'db',
                'subType': step.get('sub_type', 'fixed_prompt'),
                'sourceDetails': step.get('source', '')
            })

        elif step['type'] == 'jobNode':
            base_node['data'].update({
                'type': 'job',
                'subType': step.get('sub_type', 'code'),
                'sourceDetails': step.get('sourceDetails', step.get('code', ''))
            })

        elif step['type'] == 'endpointNode':
            base_node['data'].update({
                'type': 'endpoint',
                'saveToFile': bool(step.get('file')),
                'filePath': step.get('file', ''),
                'fileFormat': step.get('file_format', 'text')
            })

        return base_node

    @staticmethod
    def _extract_label_from_id(id_str: str) -> str:
        """Extract meaningful label from ID."""
        return id_str.replace('_', ' ').title()

    @staticmethod
    def validate_migration(diagram: Dict[str, Any]) -> List[str]:
        """Validate diagram structure."""
        warnings = []

        if 'nodes' not in diagram:
            warnings.append("Missing 'nodes' field")
        if 'arrows' not in diagram and 'edges' not in diagram:
            warnings.append("Missing 'arrows' or 'edges' field")

        for i, node in enumerate(diagram.get('nodes', [])):
            if 'id' not in node:
                warnings.append(f"Node at index {i} missing 'id' field")
            if 'type' not in node:
                warnings.append(f"Node at index {i} missing 'type' field")

        return warnings