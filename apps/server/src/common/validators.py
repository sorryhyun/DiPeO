"""
Central diagram validation utility
"""
from typing import Dict, List, Optional, Any, Union
from src.domains.diagram.models import DomainDiagram
from .services import APIKeyService


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
        
        # Handle dict format (storage format)
        if isinstance(diagram, dict):
            # For storage context, validate dict format directly
            if context == "storage":
                return self._validate_storage_format(diagram)
            
            # For other contexts, try to convert to DomainDiagram
            try:
                # Convert dict format to list format for DomainDiagram
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
        
        # Basic structure validation
        if not diagram.nodes:
            errors.append("Diagram must have at least one node")
        
        # Node validation
        node_ids = set(node.id for node in diagram.nodes) if diagram.nodes else set()
        
        # For execution context, check for start nodes
        if context == "execution":
            start_nodes = [n for n in diagram.nodes if n.type == "start"] if diagram.nodes else []
            if not start_nodes:
                errors.append("Diagram must have at least one 'start' node for execution")
        
        # Arrow validation - check node references
        if diagram.arrows:
            for arrow in diagram.arrows:
                # Parse source handle
                if ":" in arrow.source:
                    source_node_id, _ = arrow.source.split(":", 1)
                else:
                    source_node_id = arrow.source
                
                # Parse target handle  
                if ":" in arrow.target:
                    target_node_id, _ = arrow.target.split(":", 1)
                else:
                    target_node_id = arrow.target
                
                # Check if nodes exist
                if source_node_id not in node_ids:
                    errors.append(f"Arrow '{arrow.id}' references non-existent source node '{source_node_id}'")
                if target_node_id not in node_ids:
                    errors.append(f"Arrow '{arrow.id}' references non-existent target node '{target_node_id}'")
        
        # Person validation
        person_ids = set(person.id for person in diagram.persons) if diagram.persons else set()
        
        # Validate person references in nodes
        if diagram.nodes:
            for node in diagram.nodes:
                if node.type in ["person_job", "person_batch_job"] and node.data:
                    person_id = node.data.get("personId")
                    if person_id and person_id not in person_ids:
                        errors.append(f"Node '{node.id}' references non-existent person '{person_id}'")
        
        # API key validation (only if api_key_service provided)
        if self.api_key_service and diagram.persons:
            for person in diagram.persons:
                if person.api_key_id:
                    if not self.api_key_service.get_api_key(person.api_key_id):
                        errors.append(f"Person '{person.id}' references non-existent API key '{person.api_key_id}'")
        
        return errors
    
    def _validate_storage_format(self, diagram: Dict[str, Any]) -> List[str]:
        """Validate diagram in storage format (dict with dicts)"""
        errors = []
        
        # Basic structure validation
        nodes = diagram.get('nodes', {})
        if not nodes:
            errors.append("Diagram must have at least one node")
        
        # Ensure nodes is a dict
        if not isinstance(nodes, dict):
            errors.append("Nodes must be a dictionary with node IDs as keys")
            return errors
        
        node_ids = set(nodes.keys())
        
        # Arrow validation
        arrows = diagram.get('arrows', {})
        if isinstance(arrows, dict):
            for arrow_id, arrow in arrows.items():
                # Parse source handle
                source = arrow.get('source', '')
                if ":" in source:
                    source_node_id, _ = source.split(":", 1)
                else:
                    source_node_id = source
                
                # Parse target handle  
                target = arrow.get('target', '')
                if ":" in target:
                    target_node_id, _ = target.split(":", 1)
                else:
                    target_node_id = target
                
                # Check if nodes exist
                if source_node_id not in node_ids:
                    errors.append(f"Arrow '{arrow_id}' references non-existent source node '{source_node_id}'")
                if target_node_id not in node_ids:
                    errors.append(f"Arrow '{arrow_id}' references non-existent target node '{target_node_id}'")
        
        # Person validation
        persons = diagram.get('persons', {})
        if isinstance(persons, dict):
            person_ids = set(persons.keys())
            
            # Validate person references in nodes
            for node_id, node in nodes.items():
                node_type = node.get('type', '')
                if node_type in ["person_job", "person_batch_job", "personJobNode", "personBatchJobNode"]:
                    node_data = node.get('data', {})
                    person_id = node_data.get('personId')
                    if person_id and person_id not in person_ids:
                        errors.append(f"Node '{node_id}' references non-existent person '{person_id}'")
            
            # API key validation
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
            from .exceptions import ValidationError
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