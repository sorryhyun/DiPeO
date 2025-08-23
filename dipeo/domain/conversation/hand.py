from typing import Any, Optional, Sequence, TYPE_CHECKING
from dipeo.diagram_generated.domain_models import Message, ChatResult

if TYPE_CHECKING:
    from dipeo.application.execution.orchestrators.execution_orchestrator import ExecutionOrchestrator
    from dipeo.domain.conversation.person import Person


class ExecutionHand:
    """Executes LLM calls and tool operations on behalf of a Person.
    
    This class handles all execution-related tasks, providing a clean
    interface for LLM completions, tool usage, and execution tracking.
    """
    
    def __init__(self, orchestrator: "ExecutionOrchestrator"):
        """Initialize with orchestrator for execution management.
        
        Args:
            orchestrator: The execution orchestrator for managing completions
        """
        self._orchestrator = orchestrator
        self._execution_history: list[dict] = []  # Track execution history
    
    async def complete_with_messages(
        self,
        person: "Person",
        *,
        messages: Optional[Sequence[Message]] = None,
        execution_id: str,
        node_id: str,
        prompt: Optional[str] = None,
        llm_service=None,
        **kwargs: Any
    ) -> ChatResult:
        """Execute LLM completion with optional message override.
        
        Args:
            person: The person executing the completion
            messages: Optional messages to use (overrides person's view)
            execution_id: Unique execution identifier
            node_id: Node identifier for tracking
            prompt: The prompt to execute
            llm_service: LLM service to use
            **kwargs: Additional parameters for completion
            
        Returns:
            ChatResult from the completion
        """
        # Track execution start
        execution_record = {
            "execution_id": execution_id,
            "node_id": node_id,
            "person_id": str(person.id),
            "has_message_override": messages is not None,
        }
        
        try:
            # Use orchestrator's fast-path for execution
            if hasattr(self._orchestrator, 'execute_person_completion'):
                result = await self._orchestrator.execute_person_completion(
                    person=person,
                    execution_id=execution_id,
                    node_id=node_id,
                    prompt=prompt,
                    llm_service=llm_service,
                    all_messages=messages,  # Pass messages if provided
                    **kwargs
                )
                execution_record["status"] = "success"
                execution_record["result_text"] = getattr(result, "text", "")[:100]  # Store snippet
                return result
            else:
                # Fallback to direct person execution if orchestrator doesn't support it
                # This shouldn't happen in normal operation
                raise RuntimeError("Orchestrator doesn't support execute_person_completion")
                
        except Exception as e:
            execution_record["status"] = "error"
            execution_record["error"] = str(e)
            raise
        finally:
            self._execution_history.append(execution_record)
    
    async def execute_with_tools(
        self,
        person: "Person",
        *,
        prompt: str,
        tools: list[dict],
        execution_id: str,
        node_id: str,
        **kwargs: Any
    ) -> ChatResult:
        """Execute completion with tool usage capability.
        
        Args:
            person: The person executing with tools
            prompt: The prompt to execute
            tools: List of tool definitions
            execution_id: Unique execution identifier
            node_id: Node identifier
            **kwargs: Additional parameters
            
        Returns:
            ChatResult including tool calls if any
        """
        # TODO: Implement tool execution logic
        # This would integrate with the orchestrator's tool handling
        return await self.complete_with_messages(
            person=person,
            prompt=prompt,
            execution_id=execution_id,
            node_id=node_id,
            tools=tools,
            **kwargs
        )
    
    def get_execution_history(self) -> list[dict]:
        """Get the execution history for this hand.
        
        Returns:
            List of execution records
        """
        return self._execution_history.copy()
    
    def clear_execution_history(self):
        """Clear the execution history."""
        self._execution_history.clear()