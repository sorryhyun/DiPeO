"""Format strategies for unified diagram converter."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import yaml
import json

from src.__generated__.models import DomainDiagram, DomainNode, DomainArrow
from .shared_components import (
    HandleGenerator, PositionCalculator, NodeTypeMapper, ArrowBuilder
)


class FormatStrategy(ABC):
    """Abstract base class for format conversion strategies."""
    
    @abstractmethod
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse content to intermediate format."""
        pass
    
    @abstractmethod
    def format(self, data: Dict[str, Any]) -> str:
        """Format intermediate data to string."""
        pass
    
    @abstractmethod
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract nodes from parsed data."""
        pass
    
    @abstractmethod
    def extract_arrows(self, data: Dict[str, Any], nodes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract arrows from parsed data."""
        pass
    
    @abstractmethod
    def build_export_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        """Build export data from domain diagram."""
        pass
    
    @abstractmethod
    def detect_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence that data matches this format."""
        pass
    
    @property
    @abstractmethod
    def format_id(self) -> str:
        """Unique identifier for this format."""
        pass
    
    @property
    @abstractmethod
    def format_info(self) -> Dict[str, str]:
        """Metadata about this format."""
        pass


class NativeJsonStrategy(FormatStrategy):
    """Strategy for native/domain JSON format."""
    
    @property
    def format_id(self) -> str:
        return "native"
    
    @property
    def format_info(self) -> Dict[str, str]:
        return {
            'name': 'Domain JSON',
            'description': 'Canonical format for diagram structure and execution',
            'extension': '.json',
            'supports_import': True,
            'supports_export': True
        }
    
    def parse(self, content: str) -> Dict[str, Any]:
        return json.loads(content)
    
    def format(self, data: Dict[str, Any]) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes = []
        nodes_data = data.get('nodes', {})
        
        # Handle both dict and list formats
        if isinstance(nodes_data, dict):
            for node_id, node_data in nodes_data.items():
                node = {
                    'id': node_id,
                    'type': node_data.get('type', 'unknown'),
                    'position': node_data.get('position', {'x': 0, 'y': 0}),
                    **node_data.get('data', {})
                }
                nodes.append(node)
        elif isinstance(nodes_data, list):
            for node_data in nodes_data:
                node = {
                    'id': node_data.get('id'),
                    'type': node_data.get('type', 'unknown'),
                    'position': node_data.get('position', {'x': 0, 'y': 0}),
                    **node_data.get('data', {})
                }
                nodes.append(node)
        
        return nodes
    
    def extract_arrows(self, data: Dict[str, Any], nodes: Dict[str, Any]) -> List[Dict[str, Any]]:
        arrows = []
        arrows_data = data.get('arrows', {})
        
        # Handle both dict and list formats
        if isinstance(arrows_data, dict):
            for arrow_id, arrow_data in arrows_data.items():
                arrows.append({
                    'id': arrow_id,
                    'source': arrow_data.get('source'),
                    'target': arrow_data.get('target')
                })
        elif isinstance(arrows_data, list):
            for arrow_data in arrows_data:
                arrows.append({
                    'id': arrow_data.get('id'),
                    'source': arrow_data.get('source'),
                    'target': arrow_data.get('target')
                })
        
        return arrows
    
    def build_export_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        return {
            'nodes': {
                node.id: {
                    'type': node.type,
                    'position': {'x': node.position.x, 'y': node.position.y} if hasattr(node.position, 'x') else node.position,
                    'data': node.data
                }
                for node in diagram.nodes
            },
            'handles': {
                handle.id: {
                    'nodeId': handle.node_id,
                    'label': handle.label,
                    'direction': handle.direction,
                    'dataType': handle.data_type,
                    'position': handle.position
                }
                for handle in diagram.handles
            },
            'arrows': {
                arrow.id: {
                    'source': arrow.source,
                    'target': arrow.target,
                    'data': arrow.data
                }
                for arrow in diagram.arrows
            },
            'persons': {person.id: person.model_dump() for person in diagram.persons},
            'api_keys': {api_key.id: api_key.model_dump() for api_key in diagram.api_keys},
            'metadata': diagram.metadata.model_dump() if diagram.metadata else None
        }
    
    def detect_confidence(self, data: Dict[str, Any]) -> float:
        if 'nodes' in data and 'handles' in data and 'arrows' in data:
            nodes = data.get('nodes', {})
            if isinstance(nodes, dict):
                return 0.95
            elif isinstance(nodes, list):
                return 0.9
        elif 'nodes' in data:
            return 0.5
        return 0.1


class LightYamlStrategy(FormatStrategy):
    """Strategy for light YAML format."""
    
    @property
    def format_id(self) -> str:
        return "light"
    
    @property
    def format_info(self) -> Dict[str, str]:
        return {
            'name': 'Light YAML',
            'description': 'Simplified format using labels instead of IDs',
            'extension': '.light.yaml',
            'supports_import': True,
            'supports_export': True
        }
    
    def parse(self, content: str) -> Dict[str, Any]:
        return yaml.safe_load(content) or {}
    
    def format(self, data: Dict[str, Any]) -> str:
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes = []
        node_list = data.get('nodes', [])
        
        for index, node_data in enumerate(node_list):
            if isinstance(node_data, dict):
                node = {
                    'id': node_data.get('label', f'node_{index}'),
                    'type': node_data.get('type', 'unknown'),
                    'label': node_data.get('label'),
                    **{k: v for k, v in node_data.items() if k not in ['type', 'label', 'arrows']}
                }
                nodes.append(node)
        return nodes
    
    def extract_arrows(self, data: Dict[str, Any], nodes: Dict[str, Any]) -> List[Dict[str, Any]]:
        arrows = []
        node_by_label = {n.get('label', n['id']): n['id'] for n in nodes}
        
        for node_data in data.get('nodes', []):
            if isinstance(node_data, dict) and 'arrows' in node_data:
                source_label = node_data.get('label')
                source_id = node_by_label.get(source_label)
                
                for arrow in node_data['arrows']:
                    if isinstance(arrow, dict):
                        target_label = arrow.get('to')
                        target_id = node_by_label.get(target_label)
                        
                        if source_id and target_id:
                            arrows.append({
                                'source': f"{source_id}_output",
                                'target': f"{target_id}_input"
                            })
        
        return arrows
    
    def build_export_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        nodes = []
        
        nodes_dict = {node.id: node for node in diagram.nodes}
        
        arrows_by_source = {}
        for arrow in diagram.arrows:
            source_node = arrow.source.split('_')[0]
            if source_node not in arrows_by_source:
                arrows_by_source[source_node] = []
            
            target_node = arrow.target.split('_')[0]
            target = nodes_dict.get(target_node)
            if target:
                arrows_by_source[source_node].append({
                    'to': target.data.get('label', target_node)
                })
        
        # Build node list
        for node in diagram.nodes:
            node_data = {
                'type': node.type,
                'label': node.data.get('label', node.id),
                **{k: v for k, v in node.data.items() if k != 'label'}
            }
            
            if node.id in arrows_by_source:
                node_data['arrows'] = arrows_by_source[node.id]
            
            nodes.append(node_data)
        
        result = {'nodes': nodes}
        
        if diagram.persons:
            result['persons'] = [person.model_dump() for person in diagram.persons]
        if diagram.api_keys:
            result['api_keys'] = [api_key.model_dump() for api_key in diagram.api_keys]
        
        return result
    
    def detect_confidence(self, data: Dict[str, Any]) -> float:
        if 'nodes' in data and isinstance(data['nodes'], list):
            has_labels = any(
                isinstance(n, dict) and 'label' in n 
                for n in data['nodes']
            )
            if has_labels:
                return 0.8
            return 0.5
        return 0.1


class ReadableYamlStrategy(FormatStrategy):
    """Strategy for readable YAML format."""
    
    def __init__(self):
        self.node_mapper = NodeTypeMapper()
    
    @property
    def format_id(self) -> str:
        return "readable"
    
    @property
    def format_info(self) -> Dict[str, str]:
        return {
            'name': 'Readable Workflow',
            'description': 'Human-friendly workflow format',
            'extension': '.readable.yaml',
            'supports_import': True,
            'supports_export': True
        }
    
    def parse(self, content: str) -> Dict[str, Any]:
        return yaml.safe_load(content) or {}
    
    def format(self, data: Dict[str, Any]) -> str:
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes = []
        
        workflow = data.get('workflow', [])
        for index, step in enumerate(workflow):
            if isinstance(step, dict):
                for step_name, step_data in step.items():
                    node = {
                        'id': step_name,
                        'type': self._determine_node_type(step_data),
                        'label': step_name,
                        **self._extract_properties(step_data)
                    }
                    nodes.append(node)
        
        return nodes
    
    def extract_arrows(self, data: Dict[str, Any], nodes: Dict[str, Any]) -> List[Dict[str, Any]]:
        arrows = []
        node_ids = {n['id'] for n in nodes}
        
        flow = data.get('flow', [])
        for connection in flow:
            if isinstance(connection, str) and ' -> ' in connection:
                parts = connection.split(' -> ')
                if len(parts) == 2:
                    source, target = parts[0].strip(), parts[1].strip()
                    if source in node_ids and target in node_ids:
                        arrows.append({
                            'source': f"{source}_output",
                            'target': f"{target}_input"
                        })
        
        return arrows
    
    def build_export_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        nodes_dict = {node.id: node for node in diagram.nodes}
        
        workflow = []
        for node in diagram.nodes:
            step_name = node.data.get('label', node.id)
            step_data = self._build_step_data(node)
            workflow.append({step_name: step_data})
        
        flow = []
        for arrow in diagram.arrows:
            source_node = arrow.source.split('_')[0]
            target_node = arrow.target.split('_')[0]
            
            source = nodes_dict.get(source_node)
            target = nodes_dict.get(target_node)
            
            if source and target:
                source_label = source.data.get('label', source_node)
                target_label = target.data.get('label', target_node)
                flow.append(f"{source_label} -> {target_label}")
        
        result = {'workflow': workflow}
        if flow:
            result['flow'] = flow
        
        config = {}
        if diagram.persons:
            config['persons'] = [person.model_dump() for person in diagram.persons]
        if diagram.api_keys:
            config['api_keys'] = [api_key.model_dump() for api_key in diagram.api_keys]
        
        if config:
            result['config'] = config
        
        return result
    
    def detect_confidence(self, data: Dict[str, Any]) -> float:
        if 'workflow' in data and isinstance(data['workflow'], list):
            if 'flow' in data and isinstance(data['flow'], list):
                return 0.9
            return 0.6
        return 0.1
    
    def _determine_node_type(self, step_data: Dict[str, Any]) -> str:
        """Determine node type from step data using shared NodeTypeMapper."""
        node_type = self.node_mapper.determine_node_type(step_data)
        return node_type.value
    
    def _extract_properties(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract properties from step data."""
        props = {}
        
        if 'prompt' in step_data:
            props['prompt'] = step_data['prompt']
        if 'person' in step_data:
            props['personId'] = step_data['person']
        if 'model' in step_data:
            props['model'] = step_data['model']
        if 'code' in step_data:
            props['code'] = step_data['code']
        if 'language' in step_data:
            props['language'] = step_data['language']
        if 'condition' in step_data:
            props['expression'] = step_data['condition']
        if 'data' in step_data:
            props['data'] = step_data['data']
        
        return props
    
    def _build_step_data(self, node: DomainNode) -> Dict[str, Any]:
        """Build step data from node."""
        data = {}
        
        if node.type == 'person_job':
            if 'prompt' in node.data:
                data['prompt'] = node.data['prompt']
            if 'personId' in node.data:
                data['person'] = node.data['personId']
        elif node.type == 'job':
            if 'code' in node.data:
                data['code'] = node.data['code']
            if 'language' in node.data:
                data['language'] = node.data['language']
        elif node.type == 'condition':
            if 'expression' in node.data:
                data['condition'] = node.data['expression']
        elif node.type == 'start':
            if 'data' in node.data:
                data['data'] = node.data['data']
        elif node.type == 'user_response':
            if 'prompt' in node.data:
                data['prompt'] = node.data['prompt']
        
        return data