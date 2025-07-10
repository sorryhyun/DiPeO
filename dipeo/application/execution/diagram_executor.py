"""Main execution engine for DiPeO diagrams."""

from typing import Any, Dict, Optional
import logging

from dipeo.core.static import ExecutableDiagram
from dipeo.core.ports import LLMServicePort
from dipeo.infra.persistence.diagram import DiagramStorageAdapter
from ..state import ExecutionStateManager, ConversationStateManager

logger = logging.getLogger(__name__)


class ExecutionResult:
    """Result of a diagram execution."""
    
    def __init__(self, success: bool, node_results: Dict[str, Any], 
                 error: Optional[Exception] = None):
        self.success = success
        self.node_results = node_results
        self.error = error


class LLMFactory:
    """Factory for creating LLM service instances."""
    
    def __init__(self, llm_service: LLMServicePort):
        self._llm_service = llm_service
    
    def get_service(self) -> LLMServicePort:
        """Get the LLM service instance."""
        return self._llm_service


class DiagramExecutor:
    """Main execution engine for diagrams."""
    
    def __init__(self, 
                 diagram: ExecutableDiagram,
                 storage: DiagramStorageAdapter,
                 llm_factory: LLMFactory):
        self.diagram = diagram
        self.storage = storage
        self.llm_factory = llm_factory
        self.execution_state = ExecutionStateManager()
        self.conversation_state = ConversationStateManager()
    
    async def execute(self) -> ExecutionResult:
        """Orchestrate diagram execution.
        
        This method coordinates the execution of all nodes in the diagram
        according to the pre-calculated execution order, managing state
        and conversations between nodes.
        
        Returns:
            ExecutionResult containing success status and node results
        """
        try:
            # Validate diagram before execution
            validation_errors = self.diagram.validate()
            if validation_errors:
                error_msg = f"Diagram validation failed: {'; '.join(validation_errors)}"
                logger.error(error_msg)
                return ExecutionResult(
                    success=False,
                    node_results={},
                    error=ValueError(error_msg)
                )
            
            # Execute nodes in order
            for node_id in self.diagram.execution_order:
                node = self.diagram.get_node(node_id)
                if not node:
                    logger.warning(f"Node {node_id} not found in diagram")
                    continue
                
                # Check if node is ready to execute (dependencies completed)
                if not self._is_node_ready(node_id):
                    logger.info(f"Skipping node {node_id} - dependencies not met")
                    continue
                
                # Mark node as current
                self.execution_state.set_current_node(node_id)
                
                try:
                    # Execute the node based on its type
                    result = await self._execute_node(node)
                    
                    # Mark node as complete and store result
                    self.execution_state.mark_node_complete(node_id, result)
                    
                except Exception as e:
                    logger.error(f"Error executing node {node_id}: {e}")
                    return ExecutionResult(
                        success=False,
                        node_results=self.execution_state.node_results,
                        error=e
                    )
            
            # Execution completed successfully
            return ExecutionResult(
                success=True,
                node_results=self.execution_state.node_results,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Unexpected error during diagram execution: {e}")
            return ExecutionResult(
                success=False,
                node_results=self.execution_state.node_results,
                error=e
            )
    
    def _is_node_ready(self, node_id: str) -> bool:
        """Check if a node's dependencies are satisfied.
        
        A node is ready to execute if all its incoming edges come from
        nodes that have already been completed.
        
        Args:
            node_id: The ID of the node to check
            
        Returns:
            True if the node is ready to execute, False otherwise
        """
        incoming_edges = self.diagram.get_incoming_edges(node_id)
        
        for edge in incoming_edges:
            if not self.execution_state.is_node_complete(edge.source_node_id):
                return False
        
        return True
    
    async def _execute_node(self, node: Any) -> Any:
        """Execute a single node based on its type.
        
        This is a placeholder that will delegate to specific node handlers
        based on the node type. The actual implementation will be added
        when integrating with existing node execution logic.
        
        Args:
            node: The node to execute
            
        Returns:
            The result of node execution
        """
        # TODO: Integrate with existing node handlers
        # This will delegate to PersonJobNodeHandler, ConditionNodeHandler, etc.
        logger.info(f"Executing node {node.id} of type {node.type}")
        
        # For now, return a placeholder result
        return {
            "node_id": node.id,
            "node_type": node.type,
            "status": "completed",
            "output": f"Placeholder result for {node.type} node"
        }