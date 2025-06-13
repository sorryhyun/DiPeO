"""GraphQL mutation definitions."""
import strawberry
from typing import Optional

from .types.results import (
    DiagramResult, ExecutionResult, NodeResult, PersonResult,
    ApiKeyResult, DeleteResult, TestApiKeyResult
)
from .types.scalars import DiagramID, ExecutionID, NodeID, PersonID, ApiKeyID, ArrowID
from .types.inputs import (
    CreateDiagramInput, CreateNodeInput, UpdateNodeInput,
    CreateArrowInput, CreatePersonInput, UpdatePersonInput,
    CreateApiKeyInput, ExecuteDiagramInput, ExecutionControlInput,
    InteractiveResponseInput
)

@strawberry.type
class Mutation:
    """Root mutation type for DiPeO GraphQL API."""
    
    # Diagram mutations
    @strawberry.mutation
    async def create_diagram(self, input: CreateDiagramInput, info) -> DiagramResult:
        """Create a new diagram."""
        # Implementation will call diagram service
        pass
    
    @strawberry.mutation
    async def delete_diagram(self, id: DiagramID, info) -> DeleteResult:
        """Delete a diagram."""
        pass
    
    # Node mutations
    @strawberry.mutation
    async def create_node(
        self, 
        diagram_id: DiagramID, 
        input: CreateNodeInput,
        info
    ) -> NodeResult:
        """Create a new node in a diagram."""
        pass
    
    @strawberry.mutation
    async def update_node(self, input: UpdateNodeInput, info) -> NodeResult:
        """Update an existing node."""
        pass
    
    @strawberry.mutation
    async def delete_node(self, id: NodeID, info) -> DeleteResult:
        """Delete a node from a diagram."""
        pass
    
    # Arrow mutations
    @strawberry.mutation
    async def create_arrow(
        self, 
        diagram_id: DiagramID,
        input: CreateArrowInput,
        info
    ) -> DiagramResult:
        """Create a new arrow between handles."""
        pass
    
    @strawberry.mutation
    async def delete_arrow(self, id: ArrowID, info) -> DeleteResult:
        """Delete an arrow."""
        pass
    
    # Person mutations
    @strawberry.mutation
    async def create_person(
        self,
        diagram_id: DiagramID,
        input: CreatePersonInput,
        info
    ) -> PersonResult:
        """Create a new person (LLM agent)."""
        pass
    
    @strawberry.mutation
    async def update_person(self, input: UpdatePersonInput, info) -> PersonResult:
        """Update an existing person."""
        pass
    
    @strawberry.mutation
    async def delete_person(self, id: PersonID, info) -> DeleteResult:
        """Delete a person."""
        pass
    
    # API Key mutations
    @strawberry.mutation
    async def create_api_key(self, input: CreateApiKeyInput, info) -> ApiKeyResult:
        """Create a new API key."""
        pass
    
    @strawberry.mutation
    async def test_api_key(self, id: ApiKeyID, info) -> TestApiKeyResult:
        """Test an API key to verify it works."""
        pass
    
    @strawberry.mutation
    async def delete_api_key(self, id: ApiKeyID, info) -> DeleteResult:
        """Delete an API key."""
        pass
    
    # Execution mutations
    @strawberry.mutation
    async def execute_diagram(self, input: ExecuteDiagramInput, info) -> ExecutionResult:
        """Start executing a diagram."""
        pass
    
    @strawberry.mutation
    async def control_execution(
        self, 
        input: ExecutionControlInput,
        info
    ) -> ExecutionResult:
        """Control a running execution (pause, resume, abort, skip)."""
        pass
    
    @strawberry.mutation
    async def submit_interactive_response(
        self,
        input: InteractiveResponseInput,
        info
    ) -> ExecutionResult:
        """Submit a response to an interactive prompt."""
        pass
    
    @strawberry.mutation
    async def clear_conversations(self, info) -> DeleteResult:
        """Clear all conversation history."""
        pass