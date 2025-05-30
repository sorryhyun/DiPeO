#!/usr/bin/env python3
"""
LLM-Friendly YAML Importer for AgentDiagram
A single, simple format that LLMs can easily generate
"""

import yaml
import re
from typing import Dict, List, Any, Tuple, Optional
import random
import string
import json


# Backward compatibility wrapper
class DiagramMigrator:
    """Wrapper class for backward compatibility with DiagramMigrator interface."""
    
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
        # Use the new importer for conversion
        importer = LLMYamlImporter()
        # Convert the workflow format to the new flow format
        # This is a simplified conversion - you may need to adjust based on your needs
        return importer.import_yaml(yaml.dump(yaml_diagram))


class LLMYamlImporter:
    """
    Import LLM-friendly YAML format into AgentDiagram JSON.
    """

    def __init__(self):
        self.node_map = {}  # name -> node_id
        self.person_map = {}  # name -> person_id

    def import_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """Import LLM-friendly YAML and convert to AgentDiagram format."""
        try:
            data = yaml.safe_load(yaml_content)

            # Parse flow to build graph structure
            flow_edges = self._parse_flow(data.get('flow', {}))

            # Extract node names and types
            node_info = self._analyze_nodes(flow_edges, data)

            # Build diagram components
            nodes = self._build_nodes(node_info, data)
            arrows = self._build_arrows(flow_edges)
            persons = self._build_persons(node_info, data)
            api_keys = self._extract_api_keys(persons)

            return {
                'nodes': nodes,
                'arrows': arrows,
                'persons': persons,
                'apiKeys': api_keys
            }

        except Exception as e:
            # Return minimal valid diagram on error
            return {
                'nodes': [{
                    'id': 'error-node',
                    'type': 'startNode',
                    'position': {'x': 0, 'y': 0},
                    'data': {'id': 'error-node', 'label': f'Import Error: {str(e)}'}
                }],
                'arrows': [],
                'persons': [],
                'apiKeys': []
            }

    def _parse_flow(self, flow_data: Any) -> List[Dict[str, Any]]:
        """Parse flow section into edge list."""
        edges = []

        if isinstance(flow_data, dict):
            # Dictionary format: key -> value
            for source, targets in flow_data.items():
                if isinstance(targets, str):
                    # Single target
                    edge = self._parse_edge(source, targets)
                    if edge:
                        edges.append(edge)
                elif isinstance(targets, list):
                    # Multiple targets
                    for target in targets:
                        edge = self._parse_edge(source, str(target))
                        if edge:
                            edges.append(edge)

        elif isinstance(flow_data, list):
            # List format
            for item in flow_data:
                if isinstance(item, str):
                    edge = self._parse_edge_string(item)
                    if edge:
                        edges.append(edge)

        return edges

    def _parse_edge(self, source: str, target_str: str) -> Optional[Dict[str, Any]]:
        """Parse a single edge definition."""
        # Pattern: target [condition]: "variable"
        match = re.match(r'(\w+)(?:\s*\[([^\]]+)\])?(?:\s*:\s*"([^"]+)")?', target_str.strip())
        if match:
            target, condition, variable = match.groups()
            return {
                'source': source.strip(),
                'target': target.strip(),
                'condition': condition.strip() if condition else None,
                'variable': variable.strip() if variable else None
            }
        return None

    def _parse_edge_string(self, edge_str: str) -> Optional[Dict[str, Any]]:
        """Parse edge string format: source -> target [condition]: "variable" """
        match = re.match(
            r'(\w+)\s*->\s*(\w+)(?:\s*\[([^\]]+)\])?(?:\s*:\s*"([^"]+)")?',
            edge_str.strip()
        )
        if match:
            source, target, condition, variable = match.groups()
            return {
                'source': source.strip(),
                'target': target.strip(),
                'condition': condition.strip() if condition else None,
                'variable': variable.strip() if variable else None
            }
        return None

    def _analyze_nodes(self, edges: List[Dict[str, Any]], data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analyze edges to determine node types and properties."""
        node_info = {}

        # Collect all nodes
        for edge in edges:
            for node in [edge['source'], edge['target']]:
                if node not in node_info:
                    node_info[node] = {
                        'name': node,
                        'type': self._infer_node_type(node, data),
                        'has_prompt': node in data.get('prompts', {}),
                        'has_agent': node in data.get('agents', {}),
                        'incoming': [],
                        'outgoing': []
                    }

            # Track connections
            node_info[edge['source']]['outgoing'].append(edge)
            node_info[edge['target']]['incoming'].append(edge)

        # Refine node types based on connections
        for name, info in node_info.items():
            # Nodes with conditions become condition nodes
            if any(e.get('condition') for e in info['outgoing']):
                info['type'] = 'condition'
            # Nodes with prompts become person jobs (unless already typed)
            elif info['has_prompt'] and info['type'] == 'generic':
                info['type'] = 'personjob'

        return node_info

    def _infer_node_type(self, name: str, data: Dict[str, Any]) -> str:
        """Infer node type from name and context."""
        name_lower = name.lower()

        if name_lower == 'start':
            return 'start'
        elif name_lower == 'end':
            return 'endpoint'
        elif name in data.get('prompts', {}):
            return 'personjob'
        elif 'condition' in name_lower or 'check' in name_lower or 'if' in name_lower:
            return 'condition'
        elif 'data' in name_lower or 'file' in name_lower or 'load' in name_lower:
            return 'db'
        else:
            return 'generic'

    def _build_nodes(self, node_info: Dict[str, Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build node objects with positions."""
        nodes = []
        positions = self._calculate_positions(node_info)

        for name, info in node_info.items():
            node_id = f"{self._node_type_to_id(info['type'])}-{self._generate_id()}"
            self.node_map[name] = node_id

            node = {
                'id': node_id,
                'type': f"{self._node_type_to_id(info['type'])}Node",
                'position': positions[name],
                'data': {
                    'id': node_id,
                    'label': name.replace('_', ' ').title(),
                    'type': self._node_type_to_data_type(info['type'])
                }
            }

            # Add type-specific data
            if info['type'] == 'personjob':
                prompt = data.get('prompts', {}).get(name, '')
                node['data']['defaultPrompt'] = prompt

                # Check if this node needs an agent
                if name in data.get('agents', {}):
                    # Person ID will be set after persons are created
                    node['data']['personId'] = None  # Placeholder

            elif info['type'] == 'condition':
                # Try to extract condition from outgoing edges
                conditions = [e['condition'] for e in info['outgoing'] if e.get('condition')]
                if conditions:
                    # Simple heuristic: if all conditions are if/if not, use expression
                    node['data']['conditionType'] = 'expression'
                    node['data']['expression'] = f"{name}_check"  # Placeholder

            elif info['type'] == 'db':
                # Check for data source
                if name in data.get('data', {}):
                    source = data['data'][name]
                    if isinstance(source, str) and source.endswith(('.txt', '.json', '.csv')):
                        node['data']['subType'] = 'file'
                        node['data']['sourceDetails'] = source
                    else:
                        node['data']['subType'] = 'fixed_prompt'
                        node['data']['sourceDetails'] = str(source)

            nodes.append(node)

        return nodes

    def _build_arrows(self, edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build arrow objects from edges."""
        arrows = []

        for edge in edges:
            source_id = self.node_map.get(edge['source'])
            target_id = self.node_map.get(edge['target'])

            if not source_id or not target_id:
                continue

            arrow_id = f"arrow-{self._generate_id()}"
            arrow = {
                'id': arrow_id,
                'source': source_id,
                'target': target_id,
                'type': 'customArrow',
                'data': {
                    'id': arrow_id,
                    'sourceBlockId': source_id,
                    'targetBlockId': target_id,
                    'label': edge.get('variable', ''),
                    'contentType': 'variable' if edge.get('variable') else 'raw_text'
                }
            }

            # Add condition branch
            if edge.get('condition'):
                condition = edge['condition']
                if 'not' in condition or condition.startswith('!'):
                    arrow['data']['branch'] = 'false'
                else:
                    arrow['data']['branch'] = 'true'

            arrows.append(arrow)

        return arrows

    def _build_persons(self, node_info: Dict[str, Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build person objects for agents."""
        persons = []
        agents_data = data.get('agents', {})

        # Default agent for nodes with prompts but no specific agent
        default_person_id = f"PERSON_{self._generate_id()}"
        default_person = {
            'id': default_person_id,
            'label': 'Default Assistant',
            'modelName': 'gpt-4',
            'service': 'chatgpt'
        }
        need_default = False

        # Create persons from agents section
        for agent_name, agent_config in agents_data.items():
            person_id = f"PERSON_{self._generate_id()}"
            self.person_map[agent_name] = person_id

            if isinstance(agent_config, str):
                # Simple format: just system prompt
                person = {
                    'id': person_id,
                    'label': agent_name.replace('_', ' ').title(),
                    'modelName': 'gpt-4',
                    'service': 'chatgpt',
                    'systemPrompt': agent_config
                }
            else:
                # Full format
                person = {
                    'id': person_id,
                    'label': agent_name.replace('_', ' ').title(),
                    'modelName': agent_config.get('model', 'gpt-4'),
                    'service': agent_config.get('service', 'chatgpt')
                }
                if 'system' in agent_config:
                    person['systemPrompt'] = agent_config['system']
                if 'temperature' in agent_config:
                    person['temperature'] = agent_config['temperature']

            persons.append(person)

        # Update nodes with person IDs
        for node in self.node_map:
            if node in self.person_map:
                # Find and update the node
                need_default = True

        # Add default person if needed
        if need_default or (not persons and any(info['has_prompt'] for info in node_info.values())):
            persons.append(default_person)
            self.person_map['_default'] = default_person_id

        return persons

    def _extract_api_keys(self, persons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract unique API keys from persons."""
        api_keys = {}

        for person in persons:
            service = person.get('service', 'chatgpt')
            if service not in api_keys:
                api_key_id = f"APIKEY_{self._generate_id()}"
                api_keys[service] = {
                    'id': api_key_id,
                    'name': f"{service.title()} API Key",
                    'service': service
                }

        # Update persons with API key IDs
        for person in persons:
            service = person.get('service', 'chatgpt')
            person['apiKeyId'] = api_keys[service]['id']

        return list(api_keys.values())

    def _calculate_positions(self, node_info: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Calculate node positions using simple layout."""
        positions = {}

        # Find start node or nodes with no incoming edges
        start_nodes = [
            name for name, info in node_info.items()
            if info['type'] == 'start' or not info['incoming']
        ]

        if not start_nodes:
            start_nodes = [list(node_info.keys())[0]]

        # Simple BFS layout
        visited = set()
        queue = [(node, 0, 0) for node in start_nodes]
        level_counts = {}

        while queue:
            node, level, index = queue.pop(0)
            if node in visited:
                continue

            visited.add(node)

            # Position calculation
            x = level * 250
            y = index * 150
            positions[node] = {'x': x, 'y': y}

            # Queue children
            if node in node_info:
                children = [e['target'] for e in node_info[node]['outgoing']]
                for i, child in enumerate(children):
                    if child not in visited:
                        next_level = level + 1
                        level_counts[next_level] = level_counts.get(next_level, 0) + 1
                        queue.append((child, next_level, level_counts[next_level] - 1))

        return positions

    def _node_type_to_id(self, node_type: str) -> str:
        """Convert node type to ID prefix."""
        mapping = {
            'start': 'startNode',
            'endpoint': 'endpointNode',
            'personjob': 'personjobNode',
            'condition': 'conditionNode',
            'db': 'dbNode',
            'job': 'jobNode',
            'generic': 'personjobNode'  # Default to personjob
        }
        return mapping.get(node_type, 'personjobNode')

    def _node_type_to_data_type(self, node_type: str) -> str:
        """Convert node type to data type field."""
        mapping = {
            'start': 'start',
            'endpoint': 'endpoint',
            'personjob': 'person_job',
            'condition': 'condition',
            'db': 'db',
            'job': 'job',
            'generic': 'person_job'
        }
        return mapping.get(node_type, 'person_job')

    def _generate_id(self) -> str:
        """Generate a random 6-character ID."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


# Simple usage function
def import_llm_yaml(yaml_content: str) -> Dict[str, Any]:
    """Simple function to import LLM-friendly YAML."""
    importer = LLMYamlImporter()
    return importer.import_yaml(yaml_content)


# Example usage
if __name__ == '__main__':
    example_yaml = """
flow:
  START -> topic_analyzer: "topic"
  topic_analyzer -> technical_writer [if technical]: "analysis"
  topic_analyzer -> creative_writer [if creative]: "analysis"
  technical_writer -> editor: "draft"
  creative_writer -> editor: "draft"
  editor -> END: "final_article"

prompts:
  topic_analyzer: |
    Analyze this topic and determine if it's technical or creative.
    Topic: {{topic}}
    Respond with either 'TECHNICAL' or 'CREATIVE'.

  technical_writer: "Write a technical article about: {{analysis}}"
  creative_writer: "Write a creative piece about: {{analysis}}"
  editor: "Edit and polish this draft: {{draft}}"

agents:
  topic_analyzer:
    model: gpt-4
    system: "You are an expert at categorizing topics."
  technical_writer:
    system: "You are a technical writer specializing in clear explanations."
  creative_writer:
    system: "You are a creative writer with a flair for storytelling."
    """

    result = import_llm_yaml(example_yaml)
    print(json.dumps(result, indent=2))