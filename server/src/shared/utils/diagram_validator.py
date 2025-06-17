"""
Central diagram validation utility
"""
from typing import Dict, List, Optional, Any, Union
from src.domains.diagram.models.domain import DomainDiagram
from src.shared.services.api_key_service import APIKeyService


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
        
        # Convert dict to DomainDiagram if needed
        if isinstance(diagram, dict):
            try:
                diagram = DomainDiagram.from_dict(diagram)
            except Exception as e:
                errors.append(f"Invalid diagram format: {str(e)}")
                return errors
        
        # Basic structure validation
        if not diagram.nodes:
            errors.append("Diagram must have at least one node")
        
        # Node validation
        node_ids = set(diagram.nodes.keys()) if diagram.nodes else set()
        
        # For execution context, check for start nodes
        if context == "execution":
            start_nodes = [n for n in diagram.nodes.values() 
                          if n.type == "start"] if diagram.nodes else []
            if not start_nodes:
                errors.append("Diagram must have at least one 'start' node for execution")
        
        # Arrow validation - check node references
        if diagram.arrows:
            for arrow_id, arrow in diagram.arrows.items():
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
                    errors.append(f"Arrow '{arrow_id}' references non-existent source node '{source_node_id}'")
                if target_node_id not in node_ids:
                    errors.append(f"Arrow '{arrow_id}' references non-existent target node '{target_node_id}'")
        
        # Person validation
        person_ids = set(diagram.persons.keys()) if diagram.persons else set()
        
        # Validate person references in nodes
        if diagram.nodes:
            for node_id, node in diagram.nodes.items():
                if node.type in ["person_job", "person_batch_job"] and node.data:
                    person_id = node.data.get("personId")
                    if person_id and person_id not in person_ids:
                        errors.append(f"Node '{node_id}' references non-existent person '{person_id}'")
        
        # API key validation (only if api_key_service provided)
        if self.api_key_service and diagram.persons:
            for person_id, person in diagram.persons.items():
                if person.api_key_id:
                    if not self.api_key_service.get_api_key(person.api_key_id):
                        errors.append(f"Person '{person_id}' references non-existent API key '{person.api_key_id}'")
        
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
            from ..exceptions.exceptions import ValidationError
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