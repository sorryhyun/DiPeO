"""
Diagram validation logic
"""
from typing import Dict, List, Optional, Any, Union
from .models import DomainDiagram
from dipeo_server.core.services import APIKeyService


class DiagramValidator:
    """Centralized diagram validation logic"""
    
    def __init__(self, api_key_service: Optional[APIKeyService] = None):
        self.api_key_service = api_key_service
    
    def validate(self, diagram: Union[DomainDiagram, Dict[str, Any]], 
                 context: str = "general") -> List[str]:
        """
        Validate a diagram and return list of errors (empty if valid)
        
        Args:
            diagram: Diagram to validate (DomainDiagram or dict)
            context: Validation context ('general', 'execution', 'storage')
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if isinstance(diagram, dict):
            if context == "storage":
                return self._validate_storage_format(diagram)
            
            try:
                converted_data = {
                    'nodes': list(diagram.get('nodes', {}).values()) if isinstance(diagram.get('nodes'), dict) else diagram.get('nodes', []),
                    'arrows': list(diagram.get('arrows', {}).values()) if isinstance(diagram.get('arrows'), dict) else diagram.get('arrows', []),
                    'handles': list(diagram.get('handles', {}).values()) if isinstance(diagram.get('handles'), dict) else diagram.get('handles', []),
                    'persons': list(diagram.get('persons', {}).values()) if isinstance(diagram.get('persons'), dict) else diagram.get('persons', []),
                    'api_keys': list(diagram.get('api_keys', {}).values()) if isinstance(diagram.get('api_keys'), dict) else diagram.get('api_keys', []),
                    'metadata': diagram.get('metadata', {})
                }
                diagram = DomainDiagram.model_validate(converted_data)
            except Exception as e:
                errors.append(f"Invalid diagram format: {str(e)}")
                return errors
        
        if not diagram.nodes:
            errors.append("Diagram must have at least one node")
        
        node_ids = set(node.id for node in diagram.nodes) if diagram.nodes else set()
        
        if context == "execution":
            start_nodes = [n for n in diagram.nodes if n.type == "start"] if diagram.nodes else []
            if not start_nodes:
                errors.append("Diagram must have at least one 'start' node for execution")
        
        if diagram.arrows:
            for arrow in diagram.arrows:
                if ":" in arrow.source:
                    source_node_id, _ = arrow.source.split(":", 1)
                else:
                    source_node_id = arrow.source
                
                if ":" in arrow.target:
                    target_node_id, _ = arrow.target.split(":", 1)
                else:
                    target_node_id = arrow.target
                
                if source_node_id not in node_ids:
                    errors.append(f"Arrow '{arrow.id}' references non-existent source node '{source_node_id}'")
                if target_node_id not in node_ids:
                    errors.append(f"Arrow '{arrow.id}' references non-existent target node '{target_node_id}'")
        
        person_ids = set(person.id for person in diagram.persons) if diagram.persons else set()
        
        if diagram.nodes:
            for node in diagram.nodes:
                if node.type in ["person_job", "person_batch_job"] and node.data:
                    person_id = node.data.get("personId")
                    if person_id and person_id not in person_ids:
                        errors.append(f"Node '{node.id}' references non-existent person '{person_id}'")
        
        if self.api_key_service and diagram.persons:
            for person in diagram.persons:
                if person.api_key_id:
                    if not self.api_key_service.get_api_key(person.api_key_id):
                        errors.append(f"Person '{person.id}' references non-existent API key '{person.api_key_id}'")
        
        return errors
    
    def _validate_storage_format(self, diagram: Dict[str, Any]) -> List[str]:
        """Validate diagram in storage format (dict with dicts)"""
        errors = []
        
        nodes = diagram.get('nodes', {})
        if not nodes:
            errors.append("Diagram must have at least one node")
        
        if not isinstance(nodes, dict):
            errors.append("Nodes must be a dictionary with node IDs as keys")
            return errors
        
        node_ids = set(nodes.keys())
        
        arrows = diagram.get('arrows', {})
        if isinstance(arrows, dict):
            for arrow_id, arrow in arrows.items():
                source = arrow.get('source', '')
                if ":" in source:
                    source_node_id, _ = source.split(":", 1)
                else:
                    source_node_id = source
                
                target = arrow.get('target', '')
                if ":" in target:
                    target_node_id, _ = target.split(":", 1)
                else:
                    target_node_id = target
                
                if source_node_id not in node_ids:
                    errors.append(f"Arrow '{arrow_id}' references non-existent source node '{source_node_id}'")
                if target_node_id not in node_ids:
                    errors.append(f"Arrow '{arrow_id}' references non-existent target node '{target_node_id}'")
        
        persons = diagram.get('persons', {})
        if isinstance(persons, dict):
            person_ids = set(persons.keys())
            
            for node_id, node in nodes.items():
                node_type = node.get('type', '')
                if node_type in ["person_job", "person_batch_job", "personJobNode", "personBatchJobNode"]:
                    node_data = node.get('data', {})
                    person_id = node_data.get('personId')
                    if person_id and person_id not in person_ids:
                        errors.append(f"Node '{node_id}' references non-existent person '{person_id}'")
            
            if self.api_key_service:
                for person_id, person in persons.items():
                    api_key_id = person.get('apiKeyId') or person.get('api_key_id')
                    if api_key_id:
                        if not self.api_key_service.get_api_key(api_key_id):
                            errors.append(f"Person '{person_id}' references non-existent API key '{api_key_id}'")
        
        return errors
    
    def validate_or_raise(self, diagram: Union[DomainDiagram, Dict[str, Any]], 
                         context: str = "general") -> None:
        """
        Validate a diagram and raise ValidationError if invalid
        
        Args:
            diagram: Diagram to validate
            context: Validation context
            
        Raises:
            ValidationError: If diagram is invalid
        """
        errors = self.validate(diagram, context)
        if errors:
            from dipeo_server.core.exceptions import ValidationError
            raise ValidationError("; ".join(errors))
    
    def is_valid(self, diagram: Union[DomainDiagram, Dict[str, Any]], 
                 context: str = "general") -> bool:
        """
        Check if diagram is valid
        
        Args:
            diagram: Diagram to validate
            context: Validation context
            
        Returns:
            True if valid, False otherwise
        """
        return len(self.validate(diagram, context)) == 0


__all__ = ['DiagramValidator']