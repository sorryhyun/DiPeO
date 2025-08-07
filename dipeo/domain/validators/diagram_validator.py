"""Unified diagram validation service."""

from typing import Any

from dipeo.core.base.exceptions import ValidationError
from dipeo.domain.validators.base_validator import BaseValidator, ValidationResult, ValidationWarning
from dipeo.diagram_generated import (
    DomainDiagram,
    DomainNode,
    NodeType,
)
from dipeo.domain.diagram.handle import (
    extract_node_id_from_handle,
    parse_handle_id,
)


class DiagramValidator(BaseValidator):
    """Unified diagram validator combining structural and business logic validation."""
    
    def __init__(self, api_key_service: Any | None = None):
        self.api_key_service = api_key_service
    
    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        """Perform diagram validation."""
        if isinstance(target, dict):
            # Handle both backend format and frontend format
            if self._is_backend_format(target):
                self._validate_backend_format(target, result)
            else:
                try:
                    diagram = DomainDiagram.model_validate(target)
                    self._validate_diagram(diagram, result)
                except Exception as e:
                    result.add_error(ValidationError(f"Invalid diagram format: {e!s}"))
        elif isinstance(target, DomainDiagram):
            self._validate_diagram(target, result)
        else:
            result.add_error(ValidationError("Target must be a DomainDiagram or dict"))
    
    def _is_backend_format(self, data: dict[str, Any]) -> bool:
        """Check if the data is in backend format (nodes/arrows as dicts)."""
        nodes = data.get("nodes", {})
        arrows = data.get("arrows", {})
        return isinstance(nodes, dict) or isinstance(arrows, dict)
    
    def _validate_diagram(self, diagram: DomainDiagram, result: ValidationResult) -> None:
        """Validate a DomainDiagram object."""
        # Basic structure validation
        if not diagram.nodes:
            result.add_error(ValidationError("Diagram must have at least one node"))
            return
        
        # Check for duplicate node IDs
        node_ids = [node.id for node in diagram.nodes]
        if len(node_ids) != len(set(node_ids)):
            result.add_error(ValidationError("Duplicate node IDs found in diagram"))
        
        node_id_set = set(node_ids)
        
        # Validate start and endpoint nodes
        start_nodes = [n for n in diagram.nodes if n.type == NodeType.START]
        endpoint_nodes = [n for n in diagram.nodes if n.type == NodeType.ENDPOINT]
        
        if not start_nodes:
            result.add_error(ValidationError("Diagram must have at least one start node"))
        if not endpoint_nodes:
            result.add_warning(ValidationWarning("Diagram has no endpoint node - outputs may not be saved"))
        
        # Validate arrows
        if diagram.arrows:
            for arrow in diagram.arrows:
                source_node_id = extract_node_id_from_handle(arrow.source)
                target_node_id = extract_node_id_from_handle(arrow.target)
                
                if source_node_id not in node_id_set:
                    result.add_error(ValidationError(
                        f"Arrow '{arrow.id}' references non-existent source node '{source_node_id}'"
                    ))
                if target_node_id not in node_id_set:
                    result.add_error(ValidationError(
                        f"Arrow '{arrow.id}' references non-existent target node '{target_node_id}'"
                    ))
        
        # Validate node connections
        for node in diagram.nodes:
            self._validate_node_connections(node, diagram, result)
        
        # Find unreachable nodes
        unreachable = self._find_unreachable_nodes(diagram)
        for node_id in unreachable:
            result.add_warning(ValidationWarning(
                f"Node '{node_id}' is unreachable from any start node",
                field_name=f"node.{node_id}"
            ))
        
        # Validate persons references
        person_ids = {person.id for person in diagram.persons} if diagram.persons else set()
        
        if diagram.nodes:
            for node in diagram.nodes:
                if node.type in ["person_job", "person_batch_job"] and node.data:
                    person_id = node.data.get("personId")
                    if person_id and person_id not in person_ids:
                        result.add_error(ValidationError(
                            f"Node '{node.id}' references non-existent person '{person_id}'"
                        ))
        
        # Validate API keys if service is available
        if self.api_key_service and diagram.persons:
            for person in diagram.persons:
                if person.api_key_id and not self.api_key_service.get_api_key(person.api_key_id):
                    result.add_error(ValidationError(
                        f"Person '{person.id}' references non-existent API key '{person.api_key_id}'"
                    ))
    
    def _validate_backend_format(self, data: dict[str, Any], result: ValidationResult) -> None:
        """Validate backend format diagram."""
        nodes = data.get("nodes", {})
        if not nodes:
            result.add_error(ValidationError("Diagram must have at least one node"))
            return
        
        if not isinstance(nodes, dict):
            result.add_error(ValidationError("Nodes must be a dictionary with node IDs as keys"))
            return
        
        node_ids = set(nodes.keys())
        
        # Check for start nodes
        start_nodes = [
            nid for nid, node in nodes.items()
            if node.get("type") == "start" or node.get("data", {}).get("type") == "start"
        ]
        if not start_nodes:
            result.add_error(ValidationError("Diagram must have at least one 'start' node"))
        
        # Validate arrows
        arrows = data.get("arrows", {})
        if isinstance(arrows, dict):
            for arrow_id, arrow in arrows.items():
                source = arrow.get("source", "")
                source_node_id = source.split(":", 1)[0] if ":" in source else source
                
                target = arrow.get("target", "")
                target_node_id = target.split(":", 1)[0] if ":" in target else target
                
                if source_node_id not in node_ids:
                    result.add_error(ValidationError(
                        f"Arrow '{arrow_id}' references non-existent source node '{source_node_id}'"
                    ))
                if target_node_id not in node_ids:
                    result.add_error(ValidationError(
                        f"Arrow '{arrow_id}' references non-existent target node '{target_node_id}'"
                    ))
        
        # Validate person references
        persons = data.get("persons", {})
        if isinstance(persons, dict):
            person_ids = set(persons.keys())
            
            for node_id, node in nodes.items():
                node_type = node.get("type", "")
                if node_type in ["person_job", "person_batch_job", "personJobNode", "personBatchJobNode"]:
                    node_data = node.get("data", {})
                    person_id = node_data.get("personId")
                    if person_id and person_id not in person_ids:
                        result.add_error(ValidationError(
                            f"Node '{node_id}' references non-existent person '{person_id}'"
                        ))
            
            # Validate API keys
            if self.api_key_service:
                for person_id, person in persons.items():
                    api_key_id = person.get("apiKeyId") or person.get("api_key_id")
                    if api_key_id and not self.api_key_service.get_api_key(api_key_id):
                        result.add_error(ValidationError(
                            f"Person '{person_id}' references non-existent API key '{api_key_id}'"
                        ))
    
    def _validate_node_connections(self, node: DomainNode, diagram: DomainDiagram, result: ValidationResult) -> None:
        """Validate connections for a specific node."""
        # Get incoming and outgoing arrows
        incoming = []
        outgoing = []
        
        for arrow in diagram.arrows:
            if extract_node_id_from_handle(arrow.target) == node.id:
                incoming.append(arrow)
            if extract_node_id_from_handle(arrow.source) == node.id:
                outgoing.append(arrow)
        
        # Validate based on node type
        if node.type == NodeType.START and incoming:
            result.add_error(ValidationError(f"Start node '{node.id}' should not have incoming connections"))
        
        if node.type == NodeType.ENDPOINT and outgoing:
            result.add_error(ValidationError(f"Endpoint node '{node.id}' should not have outgoing connections"))
        
        if node.type == NodeType.CONDITION:
            # Condition nodes should have true/false branches
            handles = [parse_handle_id(arrow.source)[1] for arrow in outgoing]
            handle_values = [h.value for h in handles if h]
            
            if "condtrue" not in handle_values:
                result.add_warning(ValidationWarning(f"Condition node '{node.id}' missing true branch"))
            if "condfalse" not in handle_values:
                result.add_warning(ValidationWarning(f"Condition node '{node.id}' missing false branch"))
    
    def _find_unreachable_nodes(self, diagram: DomainDiagram) -> set[str]:
        """Find nodes that cannot be reached from any start node."""
        # Build adjacency list
        graph = {}
        for node in diagram.nodes:
            graph[node.id] = []
        
        for arrow in diagram.arrows:
            source_id = extract_node_id_from_handle(arrow.source)
            target_id = extract_node_id_from_handle(arrow.target)
            if source_id in graph:
                graph[source_id].append(target_id)
        
        # Find all nodes reachable from start nodes
        start_nodes = [n.id for n in diagram.nodes if n.type == NodeType.START]
        reachable = set()
        
        def dfs(node_id: str):
            if node_id in reachable:
                return
            reachable.add(node_id)
            for neighbor in graph.get(node_id, []):
                dfs(neighbor)
        
        for start_id in start_nodes:
            dfs(start_id)
        
        # Find unreachable nodes
        all_nodes = set(n.id for n in diagram.nodes)
        return all_nodes - reachable


# Convenience methods for backward compatibility
def validate_or_raise(diagram: DomainDiagram | dict[str, Any], api_key_service: Any | None = None) -> None:
    """Validate diagram and raise ValidationError if invalid."""
    validator = DiagramValidator(api_key_service)
    result = validator.validate(diagram)
    if not result.is_valid:
        errors = [str(error) for error in result.errors]
        raise ValidationError("; ".join(errors))


def is_valid(diagram: DomainDiagram | dict[str, Any], api_key_service: Any | None = None) -> bool:
    """Check if diagram is valid."""
    validator = DiagramValidator(api_key_service)
    result = validator.validate(diagram)
    return result.is_valid