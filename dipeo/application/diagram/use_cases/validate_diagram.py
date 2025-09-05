"""Use case for validating diagrams."""

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.base.validator import ValidationResult
from dipeo.domain.diagram.validation.diagram_validator import DiagramValidator


class ValidateDiagramUseCase:
    """Use case for validating diagram structure and semantics.

    This use case handles:
    - Structural validation (nodes, connections)
    - Semantic validation (business rules)
    - Providing warnings and recommendations
    """

    def __init__(self, diagram_validator: DiagramValidator | None = None):
        """Initialize the use case.

        Args:
            diagram_validator: Optional validator, creates default if not provided
        """
        self.diagram_validator = diagram_validator or DiagramValidator()

    def validate(self, domain_diagram: DomainDiagram) -> ValidationResult:
        """Validate a domain diagram.

        Args:
            domain_diagram: The diagram to validate

        Returns:
            ValidationResult containing errors and warnings
        """
        return self.diagram_validator.validate(domain_diagram)

    def validate_structure(self, domain_diagram: DomainDiagram) -> tuple[bool, list[str]]:
        """Validate only the structural aspects of a diagram.

        Args:
            domain_diagram: The diagram to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check for required nodes
        if not domain_diagram.nodes:
            errors.append("Diagram must have at least one node")
            return False, errors

        # Check for start node
        start_nodes = [n for n in domain_diagram.nodes if n.node_type == "StartNode"]
        if not start_nodes:
            errors.append("Diagram must have a StartNode")
        elif len(start_nodes) > 1:
            errors.append("Diagram can only have one StartNode")

        # Check for endpoint
        endpoint_nodes = [n for n in domain_diagram.nodes if n.node_type == "EndpointNode"]
        if not endpoint_nodes:
            errors.append("Diagram must have at least one EndpointNode")

        # Validate node IDs are unique
        node_ids = [node.id for node in domain_diagram.nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("Duplicate node IDs found")

        # Validate arrows reference existing nodes
        node_id_set = set(node_ids)
        for arrow in domain_diagram.arrows:
            if arrow.source_node_id not in node_id_set:
                errors.append(f"Arrow references non-existent source: {arrow.source_node_id}")
            if arrow.target_node_id not in node_id_set:
                errors.append(f"Arrow references non-existent target: {arrow.target_node_id}")

        return len(errors) == 0, errors

    def validate_semantics(
        self, domain_diagram: DomainDiagram
    ) -> tuple[bool, list[str], list[str]]:
        """Validate semantic/business rules of a diagram.

        Args:
            domain_diagram: The diagram to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        from dipeo.domain.execution import NodeConnectionRules

        errors = []
        warnings = []

        # Build node type lookup
        node_types = {node.id: node.node_type for node in domain_diagram.nodes}

        # Check connection rules
        for arrow in domain_diagram.arrows:
            source_type = node_types.get(arrow.source_node_id)
            target_type = node_types.get(arrow.target_node_id)

            if (
                source_type
                and target_type
                and not NodeConnectionRules.can_connect(source_type, target_type)
            ):
                errors.append(f"Invalid connection: {source_type} -> {target_type}")

        # Check for unreachable nodes
        reachable = self._find_reachable_nodes(domain_diagram)
        all_nodes = set(node.id for node in domain_diagram.nodes)
        unreachable = all_nodes - reachable

        if unreachable:
            for node_id in unreachable:
                warnings.append(f"Node {node_id} is unreachable from start")

        # Check for nodes with no outgoing connections (except endpoints)
        nodes_with_output = set(arrow.source_node_id for arrow in domain_diagram.arrows)
        for node in domain_diagram.nodes:
            if node.node_type != "EndpointNode" and node.id not in nodes_with_output:
                warnings.append(f"Node {node.id} has no outgoing connections")

        return len(errors) == 0, errors, warnings

    def _find_reachable_nodes(self, diagram: DomainDiagram) -> set[str]:
        """Find all nodes reachable from start nodes.

        Args:
            diagram: The diagram to analyze

        Returns:
            Set of reachable node IDs
        """
        # Build adjacency list
        graph = {}
        for arrow in diagram.arrows:
            if arrow.source_node_id not in graph:
                graph[arrow.source_node_id] = []
            graph[arrow.source_node_id].append(arrow.target_node_id)

        # Find start nodes
        start_nodes = [n.id for n in diagram.nodes if n.node_type == "StartNode"]

        # BFS from start nodes
        visited = set()
        queue = list(start_nodes)

        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)

            if node_id in graph:
                for neighbor in graph[node_id]:
                    if neighbor not in visited:
                        queue.append(neighbor)

        return visited
