"""Protocol for calculating execution order dynamically at runtime."""

from abc import abstractmethod
from typing import Protocol, Sequence

from dipeo.diagram_generated import NodeID
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.core.execution.execution_context import ExecutionContext


class DynamicOrderCalculator(Protocol):
    """Calculates node execution order based on runtime context.
    
    This protocol enables dynamic execution ordering that can adapt to
    runtime conditions such as conditional branches, loops, and dynamic
    dependencies.
    """
    
    @abstractmethod
    def get_ready_nodes(
        self,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> list[ExecutableNode]:
        """Get nodes that are ready to execute based on current context.
        
        A node is ready when:
        - All its dependencies have completed successfully
        - It hasn't already been executed (unless it's a loop node)
        - Any conditional dependencies are satisfied
        - It's not currently running
        
        Args:
            diagram: The executable diagram
            context: Current execution context with node states
            
        Returns:
            List of nodes ready for execution
        """
        ...
    
    @abstractmethod
    def get_next_batch(
        self,
        diagram: ExecutableDiagram,
        context: ExecutionContext,
        max_parallel: int = 10
    ) -> list[ExecutableNode]:
        """Get the next batch of nodes to execute in parallel.
        
        This method considers parallelization hints and resource constraints
        to determine which ready nodes can be executed together.
        
        Args:
            diagram: The executable diagram
            context: Current execution context
            max_parallel: Maximum number of nodes to run in parallel
            
        Returns:
            Batch of nodes to execute together
        """
        ...
    
    @abstractmethod
    def should_terminate(
        self,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> bool:
        """Check if execution should terminate.
        
        Execution terminates when:
        - All nodes have completed or failed
        - A critical error has occurred
        - Maximum execution time has been exceeded
        - User has requested cancellation
        
        Args:
            diagram: The executable diagram
            context: Current execution context
            
        Returns:
            True if execution should stop
        """
        ...
    
    @abstractmethod
    def get_blocked_nodes(
        self,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> list[tuple[NodeID, str]]:
        """Get nodes that are blocked and the reason why.
        
        This helps with debugging and error reporting by identifying
        nodes that cannot proceed due to failed dependencies or
        other blocking conditions.
        
        Args:
            diagram: The executable diagram
            context: Current execution context
            
        Returns:
            List of (node_id, reason) tuples for blocked nodes
        """
        ...
    
    @abstractmethod
    def resolve_conditional_dependencies(
        self,
        node: ExecutableNode,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> bool:
        """Check if conditional dependencies for a node are satisfied.
        
        This handles nodes that depend on conditional branches,
        ensuring they only execute when their branch is taken.
        
        Args:
            node: The node to check
            diagram: The executable diagram
            context: Current execution context
            
        Returns:
            True if the node's conditional dependencies are satisfied
        """
        ...
    
    @abstractmethod
    def handle_loop_node(
        self,
        node: ExecutableNode,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> bool:
        """Determine if a loop node should execute another iteration.
        
        Args:
            node: The loop node
            diagram: The executable diagram
            context: Current execution context
            
        Returns:
            True if the node should execute again
        """
        ...
    
    @abstractmethod
    def get_execution_stats(
        self,
        diagram: ExecutableDiagram,
        context: ExecutionContext
    ) -> dict[str, any]:
        """Get statistics about the current execution.
        
        Returns metrics such as:
        - Total nodes
        - Completed nodes
        - Failed nodes
        - Average execution time
        - Parallelization efficiency
        
        Args:
            diagram: The executable diagram
            context: Current execution context
            
        Returns:
            Dictionary of execution statistics
        """
        ...