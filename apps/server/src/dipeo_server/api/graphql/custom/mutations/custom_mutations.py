"""Custom GraphQL mutations for executing diagrams and testing API keys."""

import logging
import asyncio
from typing import Optional, Any
from datetime import datetime, UTC

import strawberry
from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase

from ...context import GraphQLContext
from ...generated.types import (
    ExecuteDiagramInput,
    ExecutionControlInput,
    InteractiveResponseInput,
    ApiKeyResult,
    ExecutionResult,
    ExecutionType,
    ExecutionID,
    ApiKeyID,
    JSONScalar,
)

logger = logging.getLogger(__name__)


@strawberry.type
class ExecutionOperationResult:
    """Result of execution operations."""
    success: bool
    execution: Optional[ExecutionType] = None
    execution_id: Optional[ExecutionID] = None
    message: Optional[str] = None
    error: Optional[str] = None


@strawberry.type
class CustomMutations:
    """Custom mutations for diagram execution and API key operations."""

    @strawberry.mutation(description="Execute a diagram with given variables")
    async def execute_diagram(
        self,
        data: ExecuteDiagramInput,
        info: strawberry.Info[GraphQLContext],
    ) -> ExecutionOperationResult:
        """Execute a diagram and return the execution ID."""
        try:
            context: GraphQLContext = info.context
            
            # Get required services
            integrated_service = context.get_service("integrated_diagram_service")
            execution_state_store = context.get_service("execution_state_store")
            event_emitter = context.get_service("event_emitter")
            api_key_service = context.get_service("api_key_service")
            llm_factory = context.get_service("llm_factory")
            
            # Initialize use case
            use_case = ExecuteDiagramUseCase(
                integrated_diagram_service=integrated_service,
                execution_state_store=execution_state_store,
                event_emitter=event_emitter,
                api_key_service=api_key_service,
                llm_factory=llm_factory,
            )
            
            # Prepare execution parameters
            diagram_id = data.diagram_id if data.diagram_id else None
            diagram_data = data.diagram_data if data.diagram_data else None
            
            if not diagram_id and not diagram_data:
                return ExecutionOperationResult(
                    success=False,
                    error="Either diagram_id or diagram_data must be provided"
                )
            
            # Execute the diagram
            execution_id = await use_case.execute(
                diagram_id=diagram_id,
                diagram_data=diagram_data,
                variables=data.variables or {},
                debug_mode=data.debug_mode,
                max_iterations=data.max_iterations,
                timeout_seconds=data.timeout_seconds,
            )
            
            # Get execution details
            execution = await execution_state_store.get_execution(execution_id)
            
            return ExecutionOperationResult(
                success=True,
                execution=execution,
                execution_id=execution_id,
                message=f"Diagram execution started with ID: {execution_id}"
            )
            
        except ValueError as e:
            logger.error(f"Validation error executing diagram: {e}")
            return ExecutionOperationResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to execute diagram: {e}", exc_info=True)
            return ExecutionOperationResult(
                success=False,
                error=f"Failed to execute diagram: {str(e)}"
            )

    @strawberry.mutation(description="Test an API key")
    async def test_api_key(
        self,
        id: ApiKeyID,
        info: strawberry.Info[GraphQLContext],
    ) -> ApiKeyResult:
        """Test if an API key is valid."""
        try:
            context: GraphQLContext = info.context
            api_key_service = context.get_service("api_key_service")
            llm_factory = context.get_service("llm_factory")
            
            # Get the API key
            api_key = await api_key_service.get(id)
            if not api_key:
                return ApiKeyResult(
                    success=False,
                    error=f"API key with ID {id} not found"
                )
            
            # Test the API key by trying to create an LLM instance
            try:
                # Create a test person with minimal config
                test_person = {
                    "id": "test",
                    "label": "Test",
                    "api_key_id": str(api_key.id),
                    "llm_config": {
                        "service": api_key.service.value,
                        "model": self._get_default_model(api_key.service.value),
                    }
                }
                
                # Try to create LLM instance
                llm = llm_factory.create_llm(
                    person=test_person,
                    api_keys={str(api_key.id): {"key": api_key.key, "service": api_key.service.value}}
                )
                
                # Try a simple test call
                response = await llm.generate("Hi", max_tokens=5)
                
                return ApiKeyResult(
                    success=True,
                    api_key=api_key,
                    message=f"API key '{api_key.label}' is valid and working"
                )
                
            except Exception as test_error:
                logger.warning(f"API key test failed: {test_error}")
                return ApiKeyResult(
                    success=False,
                    api_key=api_key,
                    error=f"API key test failed: {str(test_error)}"
                )
            
        except Exception as e:
            logger.error(f"Failed to test API key: {e}", exc_info=True)
            return ApiKeyResult(
                success=False,
                error=f"Failed to test API key: {str(e)}"
            )

    @strawberry.mutation(description="Control execution (pause, resume, stop)")
    async def control_execution(
        self,
        data: ExecutionControlInput,
        info: strawberry.Info[GraphQLContext],
    ) -> ExecutionOperationResult:
        """Control an active execution."""
        try:
            context: GraphQLContext = info.context
            execution_state_store = context.get_service("execution_state_store")
            event_emitter = context.get_service("event_emitter")
            
            # Get current execution
            execution = await execution_state_store.get_execution(data.execution_id)
            if not execution:
                return ExecutionOperationResult(
                    success=False,
                    error=f"Execution {data.execution_id} not found"
                )
            
            # Perform action
            action = data.action.lower()
            
            if action == "pause":
                # TODO: Implement pause functionality
                return ExecutionOperationResult(
                    success=False,
                    error="Pause functionality not yet implemented"
                )
            elif action == "resume":
                # TODO: Implement resume functionality
                return ExecutionOperationResult(
                    success=False,
                    error="Resume functionality not yet implemented"
                )
            elif action == "stop":
                # Update execution status
                await execution_state_store.update_execution(
                    data.execution_id,
                    status="stopped",
                    ended_at=datetime.now(UTC).isoformat()
                )
                
                # Emit stop event
                await event_emitter.emit_event({
                    "type": "execution.stopped",
                    "execution_id": str(data.execution_id),
                    "timestamp": datetime.now(UTC).isoformat()
                })
                
                # Get updated execution
                execution = await execution_state_store.get_execution(data.execution_id)
                
                return ExecutionOperationResult(
                    success=True,
                    execution=execution,
                    message=f"Execution {data.execution_id} stopped"
                )
            else:
                return ExecutionOperationResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            logger.error(f"Failed to control execution: {e}", exc_info=True)
            return ExecutionOperationResult(
                success=False,
                error=f"Failed to control execution: {str(e)}"
            )

    @strawberry.mutation(description="Submit response to interactive prompt")
    async def submit_interactive_response(
        self,
        data: InteractiveResponseInput,
        info: strawberry.Info[GraphQLContext],
    ) -> ExecutionOperationResult:
        """Submit a response to an interactive prompt."""
        try:
            context: GraphQLContext = info.context
            execution_state_store = context.get_service("execution_state_store")
            event_emitter = context.get_service("event_emitter")
            
            # Get current execution
            execution = await execution_state_store.get_execution(data.execution_id)
            if not execution:
                return ExecutionOperationResult(
                    success=False,
                    error=f"Execution {data.execution_id} not found"
                )
            
            # Emit response event
            await event_emitter.emit_event({
                "type": "interactive.response",
                "execution_id": str(data.execution_id),
                "node_id": str(data.node_id),
                "response": data.response,
                "timestamp": datetime.now(UTC).isoformat()
            })
            
            return ExecutionOperationResult(
                success=True,
                execution=execution,
                message="Interactive response submitted"
            )
            
        except Exception as e:
            logger.error(f"Failed to submit interactive response: {e}", exc_info=True)
            return ExecutionOperationResult(
                success=False,
                error=f"Failed to submit response: {str(e)}"
            )

    def _get_default_model(self, service: str) -> str:
        """Get default model for a service."""
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-haiku-20240307",
            "google": "gemini-1.5-flash",
            "gemini": "gemini-1.5-flash",
            "bedrock": "anthropic.claude-3-haiku-20240307-v1:0",
            "vertex": "claude-3-haiku@20240307",
            "deepseek": "deepseek-chat",
        }
        return defaults.get(service, "gpt-4o-mini")