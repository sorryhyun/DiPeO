"""Main diagram resolver that orchestrates the resolution pipeline."""

from typing import List, Dict, Any, Optional, Tuple
import logging

from dipeo.models import DomainDiagram, DomainNode, NodeID, NodeType
from dipeo.core.static import ExecutableDiagram, ExecutableNode
from dipeo.utils.validation.validation_rules import ValidationRules, ValidationIssue, ValidationSeverity

from .handle_resolver import HandleResolver
from .arrow_transformer import ArrowTransformer
from .execution_order_calculator import ExecutionOrderCalculator


log = logging.getLogger(__name__)


class ResolutionError(Exception):
    """Raised when diagram resolution fails."""
    def __init__(self, message: str, errors: List[str]):
        self.errors = errors
        super().__init__(message)


class DiagramResolver:
    """Transforms DomainDiagram data structure into ExecutableDiagram domain object.
    
    This is the main orchestrator for the diagram resolution pipeline that:
    1. Resolves handle references to concrete node IDs
    2. Transforms arrows into executable edges with data flow
    3. Enriches nodes with runtime configuration
    4. Calculates and validates execution order
    5. Performs comprehensive validation
    """
    
    def __init__(self):
        """Initialize the DiagramResolver with its components."""
        self.handle_resolver = HandleResolver()
        self.arrow_transformer = ArrowTransformer()
        self.order_calculator = ExecutionOrderCalculator()
        self._validation_issues: List[ValidationIssue] = []
    
    async def resolve(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Transform DomainDiagram into ExecutableDiagram.
        
        Args:
            domain_diagram: Raw diagram data structure
            
        Returns:
            Fully resolved executable diagram
            
        Raises:
            ResolutionError: If resolution fails
        """
        log.info(f"Starting diagram resolution for {len(domain_diagram.nodes)} nodes")
        
        # Clear previous validation issues
        self._validation_issues = []
        errors: List[str] = []
        
        try:
            # 1. Validate input diagram structure
            self._validate_input_diagram(domain_diagram)
            
            # 2. Resolve handle references to concrete node IDs
            resolved_connections, handle_errors = self.handle_resolver.resolve_arrows(
                domain_diagram.arrows,
                domain_diagram.nodes
            )
            errors.extend(handle_errors)
            
            # 3. Create node lookup for efficiency
            node_map = {node.id: node for node in domain_diagram.nodes}
            
            # 4. Transform arrows into executable edges with data flow
            edges, transform_errors = self.arrow_transformer.transform_arrows(
                domain_diagram.arrows,
                resolved_connections,
                node_map
            )
            errors.extend(transform_errors)
            
            # 5. Enrich nodes with runtime configuration
            executable_nodes = self._create_executable_nodes(domain_diagram.nodes)
            
            # 6. Calculate and validate execution order
            execution_order, execution_groups, order_errors = self.order_calculator.calculate_order(
                domain_diagram.nodes,
                edges
            )
            errors.extend(order_errors)
            
            # 7. Validate execution groups
            self._validate_execution_groups(execution_groups)
            
            # 8. Create the executable diagram
            diagram = ExecutableDiagram(
                nodes=executable_nodes,
                edges=edges,
                execution_order=execution_order,
                metadata={
                    "name": domain_diagram.metadata.name if domain_diagram.metadata else None,
                    "created_at": domain_diagram.metadata.created if domain_diagram.metadata else None,
                    "updated_at": domain_diagram.metadata.modified if domain_diagram.metadata else None,
                    "execution_groups": [
                        {"level": g.level, "nodes": g.nodes} 
                        for g in execution_groups
                    ]
                }
            )
            
            # 9. Final validation of the executable diagram
            self._validate_executable_diagram(diagram)
            
            # Check for critical errors
            critical_errors = [
                issue for issue in self._validation_issues 
                if issue.severity == ValidationSeverity.ERROR
            ]
            
            if critical_errors or errors:
                all_errors = errors + [issue.message for issue in critical_errors]
                log.error(f"Resolution errors: {all_errors}")
                raise ResolutionError(
                    f"Diagram resolution failed with {len(all_errors)} errors",
                    all_errors
                )
            
            # Log warnings
            warnings = [
                issue for issue in self._validation_issues 
                if issue.severity == ValidationSeverity.WARNING
            ]
            if warnings:
                log.warning(f"Diagram resolved with {len(warnings)} warnings")
                for warning in warnings:
                    log.warning(f"  - {warning.message}")
            
            log.info(f"Successfully resolved diagram with {len(executable_nodes)} nodes "
                    f"and {len(edges)} edges")
            
            return diagram
            
        except ResolutionError:
            raise
        except Exception as e:
            log.error(f"Unexpected error during diagram resolution: {e}")
            raise ResolutionError(f"Diagram resolution failed: {str(e)}", [str(e)])
    
    def _validate_input_diagram(self, diagram: DomainDiagram) -> None:
        """Validate the input diagram structure.
        
        Args:
            diagram: The domain diagram to validate
        """
        # Check for empty diagram
        if not diagram.nodes:
            self._validation_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="structure",
                message="Diagram has no nodes"
            ))
        
        # Check for start nodes
        start_nodes = [n for n in diagram.nodes if n.type == NodeType.start]
        if not start_nodes:
            self._validation_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="structure",
                message="Diagram must have at least one start node"
            ))
        
        # Validate diagram size
        size_issues = ValidationRules.validate_diagram_size(
            len(diagram.nodes),
            len(diagram.arrows)
        )
        self._validation_issues.extend(size_issues)
        
        # Check for duplicate node IDs
        node_ids = [node.id for node in diagram.nodes]
        if len(node_ids) != len(set(node_ids)):
            self._validation_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="structure",
                message="Diagram contains duplicate node IDs"
            ))
    
    def _create_executable_nodes(
        self, 
        domain_nodes: List[DomainNode]
    ) -> List[ExecutableNode]:
        """Transform domain nodes into executable nodes.
        
        Args:
            domain_nodes: List of domain nodes
            
        Returns:
            List of executable nodes with runtime configuration
        """
        executable_nodes = []
        
        for node in domain_nodes:
            # Create executable node implementation
            exec_node = ExecutableNodeImpl(
                id=node.id,
                type=node.type,
                position=node.position,
                data=node.data or {}
            )
            
            # Validate node-specific configuration
            self._validate_node_config(node)
            
            executable_nodes.append(exec_node)
        
        return executable_nodes
    
    def _validate_node_config(self, node: DomainNode) -> None:
        """Validate node-specific configuration.
        
        Args:
            node: The node to validate
        """
        if node.type == NodeType.person_job:
            issues = ValidationRules.validate_person_node(node.data or {})
            for issue in issues:
                issue.node_id = node.id
            self._validation_issues.extend(issues)
        
        elif node.type == NodeType.condition:
            issues = ValidationRules.validate_condition_node(node.data or {})
            for issue in issues:
                issue.node_id = node.id
            self._validation_issues.extend(issues)
    
    def _validate_execution_groups(self, groups: List[Any]) -> None:
        """Validate execution groups.
        
        Args:
            groups: List of execution groups
        """
        issues = ValidationRules.validate_execution_groups(groups)
        self._validation_issues.extend(issues)
    
    def _validate_executable_diagram(self, diagram: ExecutableDiagram) -> None:
        """Perform final validation on the executable diagram.
        
        Args:
            diagram: The executable diagram to validate
        """
        # Use built-in validation
        diagram_errors = diagram.validate()
        for error in diagram_errors:
            self._validation_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="diagram",
                message=error
            ))
        
        # Validate node connections
        for node in diagram.nodes:
            incoming = len(diagram.get_incoming_edges(node.id))
            outgoing = len(diagram.get_outgoing_edges(node.id))
            
            conn_issues = ValidationRules.validate_node_connections(
                node.type,
                incoming,
                outgoing
            )
            for issue in conn_issues:
                issue.node_id = node.id
            self._validation_issues.extend(conn_issues)
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get a detailed validation report.
        
        Returns:
            Dictionary with validation statistics and issues
        """
        errors = [i for i in self._validation_issues if i.severity == ValidationSeverity.ERROR]
        warnings = [i for i in self._validation_issues if i.severity == ValidationSeverity.WARNING]
        info = [i for i in self._validation_issues if i.severity == ValidationSeverity.INFO]
        
        return {
            "total_issues": len(self._validation_issues),
            "errors": len(errors),
            "warnings": len(warnings),
            "info": len(info),
            "issues_by_category": self._group_issues_by_category(),
            "issues_by_node": self._group_issues_by_node(),
            "all_issues": [
                {
                    "severity": issue.severity.value,
                    "category": issue.category,
                    "message": issue.message,
                    "node_id": issue.node_id,
                    "details": issue.details
                }
                for issue in self._validation_issues
            ]
        }
    
    def _group_issues_by_category(self) -> Dict[str, int]:
        """Group validation issues by category."""
        categories: Dict[str, int] = {}
        for issue in self._validation_issues:
            categories[issue.category] = categories.get(issue.category, 0) + 1
        return categories
    
    def _group_issues_by_node(self) -> Dict[str, int]:
        """Group validation issues by node ID."""
        nodes: Dict[str, int] = {}
        for issue in self._validation_issues:
            if issue.node_id:
                nodes[issue.node_id] = nodes.get(issue.node_id, 0) + 1
        return nodes


class ExecutableNodeImpl:
    """Implementation of ExecutableNode protocol."""
    
    def __init__(
        self,
        id: NodeID,
        type: NodeType,
        position: Any,
        data: Dict[str, Any]
    ):
        self.id = id
        self.type = type
        self.position = position
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type.value,
            "position": {
                "x": self.position.x,
                "y": self.position.y
            },
            "data": self.data
        }