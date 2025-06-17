"""LLM-friendly YAML format converter."""
import yaml
from typing import Dict, Any, List
from .base import DiagramConverter
from ..models.domain import (
    DomainDiagram, DomainNode, DomainArrow, 
    NodeType, Vec2
)


class LLMYamlConverter(DiagramConverter):
    """Converts between DomainDiagram and LLM-friendly format."""
    
    def serialize(self, diagram: DomainDiagram) -> str:
        """Convert domain diagram to LLM-friendly YAML."""
        # This is a simplified format optimized for LLM understanding
        llm_format = {
            'workflow_summary': {
                'purpose': diagram.metadata.description if diagram.metadata else 'AI workflow automation',
                'total_steps': len(diagram.nodes),
                'ai_agents': len(diagram.persons),
                'connections': len(diagram.arrows)
            }
        }
        
        # Add context about agents
        if diagram.persons:
            llm_format['ai_agents'] = []
            for person in diagram.persons.values():
                agent_desc = {
                    'name': person.label,
                    'role': person.systemPrompt or 'General AI assistant',
                    'model': f"{person.service.value} {person.model}",
                    'capabilities': self._describe_capabilities(person)
                }
                llm_format['ai_agents'].append(agent_desc)
        
        # Describe workflow in natural language
        llm_format['workflow_steps'] = []
        
        # Group nodes by type
        nodes_by_type = {}
        for node in diagram.nodes.values():
            node_type = node.type.value
            if node_type not in nodes_by_type:
                nodes_by_type[node_type] = []
            nodes_by_type[node_type].append(node)
        
        # Process nodes in logical order
        step_number = 1
        processed = set()
        
        # Start with start nodes
        for node in nodes_by_type.get('start', []):
            if node.id not in processed:
                step = self._describe_node_step(node, diagram, step_number)
                llm_format['workflow_steps'].append(step)
                processed.add(node.id)
                step_number += 1
        
        # Process remaining nodes following connections
        remaining_nodes = [n for n in diagram.nodes.values() if n.id not in processed]
        while remaining_nodes:
            for node in remaining_nodes[:]:
                # Check if all predecessors are processed
                predecessors = [a.source.split(':')[0] for a in diagram.arrows.values() 
                              if a.target.startswith(node.id + ':')]
                if all(p in processed for p in predecessors) or not predecessors:
                    step = self._describe_node_step(node, diagram, step_number)
                    llm_format['workflow_steps'].append(step)
                    processed.add(node.id)
                    remaining_nodes.remove(node)
                    step_number += 1
        
        # Add data flow description
        if diagram.arrows:
            llm_format['data_flow'] = []
            for arrow in diagram.arrows.values():
                source_node = self._find_node_by_handle(diagram, arrow.source)
                target_node = self._find_node_by_handle(diagram, arrow.target)
                
                if source_node and target_node:
                    flow_desc = {
                        'from': source_node.data.get('label', source_node.type.value),
                        'to': target_node.data.get('label', target_node.type.value),
                        'description': self._describe_connection(source_node, target_node, arrow)
                    }
                    llm_format['data_flow'].append(flow_desc)
        
        # Add execution notes
        llm_format['execution_notes'] = self._generate_execution_notes(diagram)
        
        return yaml.dump(llm_format, default_flow_style=False, sort_keys=False, 
                        allow_unicode=True, width=80)
    
    def deserialize(self, content: str) -> DomainDiagram:
        """Convert LLM-friendly YAML to domain diagram."""
        # This format is write-only as it's too abstract to reliably parse back
        raise NotImplementedError(
            "LLM format is write-only. Use native, light, or readable formats for import."
        )
    
    def _describe_capabilities(self, person) -> str:
        """Generate natural language description of agent capabilities."""
        capabilities = []
        
        if person.service.value == 'openai':
            if 'gpt-4' in person.model:
                capabilities.append("Advanced reasoning and analysis")
            else:
                capabilities.append("General text processing")
        elif person.service.value == 'anthropic':
            capabilities.append("Complex reasoning and coding")
        elif person.service.value == 'google':
            capabilities.append("Multimodal understanding")
        
        if person.systemPrompt:
            if 'code' in person.systemPrompt.lower():
                capabilities.append("Code generation")
            if 'analyze' in person.systemPrompt.lower():
                capabilities.append("Data analysis")
            if 'creative' in person.systemPrompt.lower():
                capabilities.append("Creative writing")
        
        return ", ".join(capabilities) if capabilities else "General AI capabilities"
    
    def _describe_node_step(self, node: DomainNode, diagram: DomainDiagram, 
                           step_num: int) -> Dict[str, Any]:
        """Create natural language description of a node."""
        step = {
            'step': step_num,
            'name': node.data.get('label', f"{node.type.value} operation"),
            'type': self._humanize_node_type(node.type),
            'description': ''
        }
        
        # Add type-specific descriptions
        if node.type == NodeType.START:
            step['description'] = "Initialize the workflow"
            if 'input' in node.data:
                step['initial_data'] = node.data['input']
        
        elif node.type == NodeType.PERSON_JOB:
            person_id = node.data.get('personId')
            if person_id and person_id in diagram.persons:
                person = diagram.persons[person_id]
                step['ai_agent'] = person.label
                step['description'] = f"{person.label} processes the input"
            else:
                step['description'] = "AI agent processes the task"
            
            if 'task' in node.data:
                step['task'] = node.data['task']
        
        elif node.type == NodeType.CONDITION:
            step['description'] = "Evaluate condition and branch"
            if 'condition' in node.data:
                step['condition'] = node.data['condition']
        
        elif node.type == NodeType.JOB:
            lang = node.data.get('language', 'code')
            step['description'] = f"Execute {lang} code"
            if 'code' in node.data:
                step['code_preview'] = node.data['code'][:100] + '...' if len(node.data['code']) > 100 else node.data['code']
        
        elif node.type == NodeType.ENDPOINT:
            step['description'] = "Output final results"
        
        elif node.type == NodeType.DB:
            step['description'] = "Database operation"
        
        # Add connections info
        outgoing = [a for a in diagram.arrows.values() if a.source.startswith(node.id + ':')]
        if outgoing:
            targets = []
            for arrow in outgoing:
                target_node = self._find_node_by_handle(diagram, arrow.target)
                if target_node:
                    targets.append(target_node.data.get('label', 'next step'))
            step['leads_to'] = targets
        
        return step
    
    def _humanize_node_type(self, node_type: NodeType) -> str:
        """Convert node type to human-readable string."""
        type_map = {
            NodeType.START: "Workflow Start",
            NodeType.PERSON_JOB: "AI Task",
            NodeType.CONDITION: "Decision Point",
            NodeType.JOB: "Code Execution",
            NodeType.ENDPOINT: "Output/Result",
            NodeType.DB: "Data Operation",
            NodeType.USER_RESPONSE: "User Interaction",
            NodeType.NOTION: "Notion Integration",
            NodeType.PERSON_BATCH_JOB: "Batch AI Processing"
        }
        return type_map.get(node_type, node_type.value)
    
    def _find_node_by_handle(self, diagram: DomainDiagram, handle_id: str):
        """Find node that owns a handle."""
        node_id = handle_id.split(':')[0]
        return diagram.nodes.get(node_id)
    
    def _describe_connection(self, source_node: DomainNode, target_node: DomainNode, 
                           arrow: DomainArrow) -> str:
        """Generate natural language description of a connection."""
        if source_node.type == NodeType.CONDITION:
            handle_name = arrow.source.split(':')[1]
            if handle_name == 'true':
                return "When condition is true"
            elif handle_name == 'false':
                return "When condition is false"
        
        if source_node.type == NodeType.PERSON_JOB and target_node.type == NodeType.PERSON_JOB:
            return "AI output passed to next AI agent"
        
        if target_node.type == NodeType.ENDPOINT:
            return "Final output saved"
        
        return "Data flows to next step"
    
    def _generate_execution_notes(self, diagram: DomainDiagram) -> List[str]:
        """Generate helpful notes about the workflow."""
        notes = []
        
        # Check for parallel paths
        nodes_with_multiple_outputs = []
        for node in diagram.nodes.values():
            outgoing = [a for a in diagram.arrows.values() if a.source.startswith(node.id + ':')]
            if len(outgoing) > 1 and node.type != NodeType.CONDITION:
                nodes_with_multiple_outputs.append(node.data.get('label', node.id))
        
        if nodes_with_multiple_outputs:
            notes.append(f"Parallel execution possible at: {', '.join(nodes_with_multiple_outputs)}")
        
        # Check for loops
        # Simple cycle detection
        if self._has_cycles(diagram):
            notes.append("This workflow contains loops/cycles")
        
        # Check for isolated nodes
        isolated = []
        for node in diagram.nodes.values():
            incoming = [a for a in diagram.arrows.values() if a.target.startswith(node.id + ':')]
            outgoing = [a for a in diagram.arrows.values() if a.source.startswith(node.id + ':')]
            if not incoming and not outgoing and node.type != NodeType.START:
                isolated.append(node.data.get('label', node.id))
        
        if isolated:
            notes.append(f"Isolated nodes found: {', '.join(isolated)}")
        
        # Memory considerations
        if diagram.persons:
            with_memory = [p.label for p in diagram.persons.values() 
                          if p.forgettingMode.value != 'none']
            if with_memory:
                notes.append(f"Agents with memory management: {', '.join(with_memory)}")
        
        return notes
    
    def _has_cycles(self, diagram: DomainDiagram) -> bool:
        """Simple cycle detection."""
        visited = set()
        rec_stack = set()
        
        def has_cycle_util(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            
            # Check all neighbors
            for arrow in diagram.arrows.values():
                if arrow.source.startswith(node_id + ':'):
                    neighbor_id = arrow.target.split(':')[0]
                    if neighbor_id not in visited:
                        if has_cycle_util(neighbor_id):
                            return True
                    elif neighbor_id in rec_stack:
                        return True
            
            rec_stack.remove(node_id)
            return False
        
        # Check all nodes
        for node_id in diagram.nodes:
            if node_id not in visited:
                if has_cycle_util(node_id):
                    return True
        
        return False
    
    def detect_format_confidence(self, content: str) -> float:
        """Detect if content is LLM YAML format."""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return 0.0
            
            score = 0.0
            
            # Check for LLM format indicators
            if 'workflow_summary' in data:
                score += 0.3
            if 'ai_agents' in data:
                score += 0.3
            if 'workflow_steps' in data:
                score += 0.2
            if 'data_flow' in data:
                score += 0.1
            if 'execution_notes' in data:
                score += 0.1
            
            return min(score, 1.0)
        except:
            return 0.0