"""Execution plan value objects."""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from enum import Enum


class ExecutionMode(Enum):
    """Execution modes for nodes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


@dataclass(frozen=True)
class ExecutionStep:
    """Represents a single step in the execution plan."""
    
    node_id: str
    dependencies: Set[str] = field(default_factory=set)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    condition: Optional[str] = None  # For conditional nodes
    
    def __post_init__(self):
        """Validate execution step."""
        if not self.node_id:
            raise ValueError("Node ID cannot be empty")
        if self.execution_mode == ExecutionMode.CONDITIONAL and not self.condition:
            raise ValueError("Conditional execution requires a condition")
    
    def can_execute_after(self, completed_nodes: Set[str]) -> bool:
        """Check if this step can execute given completed nodes."""
        return self.dependencies.issubset(completed_nodes)


@dataclass(frozen=True)
class ExecutionPlan:
    """Represents a complete execution plan for a diagram."""
    
    steps: List[ExecutionStep]
    entry_points: Set[str] = field(default_factory=set)
    parallel_groups: Dict[int, Set[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate execution plan."""
        if not self.steps:
            raise ValueError("Execution plan must have at least one step")
        
        # Validate entry points exist in steps
        step_ids = {step.node_id for step in self.steps}
        if self.entry_points and not self.entry_points.issubset(step_ids):
            raise ValueError("Entry points must exist in execution steps")
        
        # Validate parallel groups
        for group_nodes in self.parallel_groups.values():
            if not group_nodes.issubset(step_ids):
                raise ValueError("Parallel group nodes must exist in execution steps")
    
    def get_next_steps(self, completed_nodes: Set[str]) -> List[ExecutionStep]:
        """Get the next steps that can be executed."""
        return [
            step for step in self.steps
            if step.node_id not in completed_nodes
            and step.can_execute_after(completed_nodes)
        ]
    
    def get_parallel_group(self, node_id: str) -> Optional[int]:
        """Get the parallel group for a node, if any."""
        for group_id, nodes in self.parallel_groups.items():
            if node_id in nodes:
                return group_id
        return None
    
    def is_complete(self, completed_nodes: Set[str]) -> bool:
        """Check if execution plan is complete."""
        all_nodes = {step.node_id for step in self.steps}
        return all_nodes.issubset(completed_nodes)
    
    def get_execution_order(self) -> List[List[str]]:
        """Get execution order as layers (nodes in same layer can run in parallel)."""
        layers = []
        completed = set()
        
        while not self.is_complete(completed):
            next_steps = self.get_next_steps(completed)
            if not next_steps:
                break  # Prevent infinite loop if there's a cycle
            
            layer = [step.node_id for step in next_steps]
            layers.append(layer)
            completed.update(layer)
        
        return layers