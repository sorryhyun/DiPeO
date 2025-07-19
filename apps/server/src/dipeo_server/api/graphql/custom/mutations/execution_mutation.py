"""GraphQL mutations for Execution management - Auto-generated."""

import logging
import uuid
from typing import Optional
from datetime import datetime

import strawberry
from dipeo.models import Execution

from ...context import GraphQLContext
from ...generated.types import (
    CreateExecutionInput,
    UpdateExecutionInput,
    ExecutionResult,
    ExecutionID,
    DeleteResult,
    JSONScalar,
    MutationResult,
    DiagramID,
    ExecutionType,
)

logger = logging.getLogger(__name__)


@strawberry.type
class ExecutionMutations:
    """Handles Execution CRUD operations."""
    
    @strawberry.mutation
    async def create_execution(
        self,
        execution_input: CreateExecutionInput,
        info: strawberry.Info[GraphQLContext],
    ) -> ExecutionResult:
        """Create a new Execution."""
        try:
            context: GraphQLContext = info.context
            # Get CRUD adapter for standardized interface
            crud_registry = context.get_service("crud_registry")
            if not crud_registry:
                from dipeo.application.services import create_crud_registry
                crud_registry = create_crud_registry(context.service_registry)
            execution_service = crud_registry.get_adapter("execution_service")
            if not execution_service:
                raise ValueError("CRUD adapter for execution_service not found")
            
            # Extract fields from input
            data = {
                "diagram_id": getattr(execution_input, "diagram_id", None),
                "variables": getattr(execution_input, "variables", None),
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            # Validate required fields
            required_fields = ["variables"]
            missing = [f for f in required_fields if f not in data or data[f] is None]
            if missing:
                return ExecutionResult(
                    success=False,
                    error=f"Missing required fields: {', '.join(missing)}"
                )
            
            # Create the entity
            entity_id = f"execution_{str(uuid.uuid4())[:8]}"
            
            # Build domain model
            execution_data = Execution(
                id=ExecutionID(entity_id),
                **data
            )
            
            # Save through service
            saved_entity = await execution_service.create(data)
            

            
            # Convert to GraphQL type if needed
            execution_graphql = ExecutionType.from_pydantic(saved_entity)
            
            return ExecutionResult(
                success=True,
                execution=execution_graphql,
                message=f"Execution created successfully with ID: {entity_id}"
            )
            
        except ValueError as e:
            logger.error(f"Validation error creating Execution: {e}")
            return ExecutionResult(
                success=False, 
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to create Execution: {e}", exc_info=True)
            return ExecutionResult(
                success=False, 
                error=f"Failed to create Execution: {str(e)}"
            )

    @strawberry.mutation
    async def update_execution(
        self,
        execution_input: UpdateExecutionInput,
        info: strawberry.Info[GraphQLContext],
    ) -> ExecutionResult:
        """Update an existing Execution."""
        try:
            context: GraphQLContext = info.context
            # Get CRUD adapter for standardized interface
            crud_registry = context.get_service("crud_registry")
            if not crud_registry:
                from dipeo.application.services import create_crud_registry
                crud_registry = create_crud_registry(context.service_registry)
            execution_service = crud_registry.get_adapter("execution_service")
            if not execution_service:
                raise ValueError("CRUD adapter for execution_service not found")
            
            # Get existing entity
            existing = await execution_service.get(execution_input.id)
            if not existing:
                return ExecutionResult(
                    success=False,
                    error=f"Execution with ID {execution_input.id} not found"
                )
            
            # Build updates
            updates = {}
            if execution_input.status is not None:
                updates["status"] = execution_input.status
            if execution_input.node_states is not None:
                updates["node_states"] = execution_input.node_states
            if execution_input.node_outputs is not None:
                updates["node_outputs"] = execution_input.node_outputs
            if execution_input.token_usage is not None:
                updates["token_usage"] = execution_input.token_usage
            if execution_input.error is not None:
                updates["error"] = execution_input.error
            if execution_input.variables is not None:
                updates["variables"] = execution_input.variables
            if execution_input.exec_counts is not None:
                updates["exec_counts"] = execution_input.exec_counts
            if execution_input.executed_nodes is not None:
                updates["executed_nodes"] = execution_input.executed_nodes
            if execution_input.ended_at is not None:
                updates["ended_at"] = execution_input.ended_at
            
            if not updates:
                return ExecutionResult(
                    success=False,
                    error="No fields to update"
                )
            

            
            # Apply updates
            updated_entity = await execution_service.update(execution_input.id, updates)
            
            # Convert to GraphQL type if needed
            execution_graphql = ExecutionType.from_pydantic(updated_entity)
            
            return ExecutionResult(
                success=True,
                execution=execution_graphql,
                message=f"Execution updated successfully"
            )
            
        except ValueError as e:
            logger.error(f"Validation error updating Execution: {e}")
            return ExecutionResult(
                success=False,
                error=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to update Execution: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                error=f"Failed to update Execution: {str(e)}"
            )

    @strawberry.mutation
    async def updateNodeState(
        self,
        execution_id: str,
        node_id: str,
        state: str,
        info: strawberry.Info[GraphQLContext],
    ) -> ExecutionType:
        """updateNodeState - Custom mutation for Execution."""
        try:
            context: GraphQLContext = info.context
            # Get CRUD adapter for standardized interface
            crud_registry = context.get_service("crud_registry")
            if not crud_registry:
                from dipeo.application.services import create_crud_registry
                crud_registry = create_crud_registry(context.service_registry)
            execution_service = crud_registry.get_adapter("execution_service")
            if not execution_service:
                raise ValueError("CRUD adapter for execution_service not found")
            
            # Custom implementation
            result = await execution_service.update_node_state(execution_id, node_id, state)
            return ExecutionType.from_pydantic(result)
            
        except ValueError as e:
            logger.error(f"Validation error in updateNodeState: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to execute updateNodeState: {e}", exc_info=True)
            raise

    @strawberry.mutation
    async def addNodeOutput(
        self,
        execution_id: str,
        node_id: str,
        output: str,
        info: strawberry.Info[GraphQLContext],
    ) -> ExecutionType:
        """addNodeOutput - Custom mutation for Execution."""
        try:
            context: GraphQLContext = info.context
            # Get CRUD adapter for standardized interface
            crud_registry = context.get_service("crud_registry")
            if not crud_registry:
                from dipeo.application.services import create_crud_registry
                crud_registry = create_crud_registry(context.service_registry)
            execution_service = crud_registry.get_adapter("execution_service")
            if not execution_service:
                raise ValueError("CRUD adapter for execution_service not found")
            
            # Custom implementation
            result = await execution_service.add_node_output(execution_id, node_id, output)
            return ExecutionType.from_pydantic(result)
            
        except ValueError as e:
            logger.error(f"Validation error in addNodeOutput: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to execute addNodeOutput: {e}", exc_info=True)
            raise
