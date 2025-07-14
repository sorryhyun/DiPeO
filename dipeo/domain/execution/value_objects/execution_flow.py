"""Execution flow value objects."""

from dataclasses import dataclass, field
from enum import Enum


class FlowIssueType(Enum):
    """Types of flow validation issues."""
    NO_START_NODE = "no_start_node"
    NO_ENDPOINT_NODE = "no_endpoint_node"
    UNREACHABLE_NODE = "unreachable_node"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    INVALID_CONNECTION = "invalid_connection"
    MISSING_REQUIRED_INPUT = "missing_required_input"
    TYPE_MISMATCH = "type_mismatch"


@dataclass(frozen=True)
class FlowIssue:
    """Represents a single flow validation issue."""
    
    issue_type: FlowIssueType
    node_id: str | None = None
    message: str = ""
    related_nodes: set[str] = field(default_factory=set)
    
    @property
    def severity(self) -> str:
        """Get issue severity."""
        critical_issues = {
            FlowIssueType.NO_START_NODE,
            FlowIssueType.CIRCULAR_DEPENDENCY,
            FlowIssueType.INVALID_CONNECTION
        }
        return "critical" if self.issue_type in critical_issues else "warning"


@dataclass(frozen=True)
class FlowValidationResult:
    """Result of flow validation."""
    
    is_valid: bool
    issues: list[FlowIssue] = field(default_factory=list)
    
    @property
    def critical_issues(self) -> list[FlowIssue]:
        """Get only critical issues."""
        return [issue for issue in self.issues if issue.severity == "critical"]
    
    @property
    def warnings(self) -> list[FlowIssue]:
        """Get only warnings."""
        return [issue for issue in self.issues if issue.severity == "warning"]
    
    def add_issue(self, issue: FlowIssue) -> "FlowValidationResult":
        """Create new result with added issue."""
        new_issues = list(self.issues) + [issue]
        is_valid = not any(i.severity == "critical" for i in new_issues)
        return FlowValidationResult(is_valid=is_valid, issues=new_issues)


@dataclass(frozen=True)
class ExecutionFlow:
    """Represents the flow structure of a diagram."""
    
    nodes: dict[str, str]  # node_id -> node_type
    connections: dict[str, set[str]]  # source_id -> {target_ids}
    start_nodes: set[str] = field(default_factory=set)
    endpoint_nodes: set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Validate flow structure."""
        if not self.nodes:
            raise ValueError("Flow must have at least one node")
        
        # Note: In DiPeO, arrows connect to handles (e.g., node_2_default_output)
        # rather than directly to nodes. This is valid, so we skip strict validation
        # of connection endpoints against node IDs.
    
    def get_dependencies(self, node_id: str) -> set[str]:
        """Get all nodes that must complete before this node."""
        dependencies = set()
        for source, targets in self.connections.items():
            if node_id in targets:
                dependencies.add(source)
        return dependencies
    
    def get_descendants(self, node_id: str) -> set[str]:
        """Get all nodes downstream from this node."""
        descendants = set()
        to_visit = self.connections.get(node_id, set()).copy()
        
        while to_visit:
            current = to_visit.pop()
            if current not in descendants:
                descendants.add(current)
                to_visit.update(self.connections.get(current, set()))
        
        return descendants
    
    def find_cycles(self) -> list[list[str]]:
        """Find circular dependencies in the flow."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.connections.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:])
            
            rec_stack.remove(node)
        
        for node in self.nodes:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def find_unreachable_nodes(self) -> set[str]:
        """Find nodes not reachable from start nodes."""
        if not self.start_nodes:
            return set(self.nodes.keys())
        
        reachable = set()
        to_visit = self.start_nodes.copy()
        
        while to_visit:
            current = to_visit.pop()
            if current not in reachable:
                reachable.add(current)
                to_visit.update(self.connections.get(current, set()))
        
        return set(self.nodes.keys()) - reachable