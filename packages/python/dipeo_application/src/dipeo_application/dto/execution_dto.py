"""DTOs for execution-related operations."""

from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ExecutionStatus(str, Enum):
    """Execution status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeStatus(str, Enum):
    """Node execution status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecuteDiagramRequest(BaseModel):
    """Request DTO for executing a diagram."""
    
    diagram_id: Optional[str] = Field(None, description="Diagram ID to execute")
    diagram_data: Optional[dict[str, Any]] = Field(None, description="Inline diagram data")
    variables: dict[str, Any] = Field(default_factory=dict, description="Execution variables")
    options: dict[str, Any] = Field(default_factory=dict, description="Execution options")
    interactive: bool = Field(False, description="Enable interactive mode")
    
    def validate_diagram_source(self) -> None:
        """Validate that either diagram_id or diagram_data is provided."""
        if not self.diagram_id and not self.diagram_data:
            raise ValueError("Either diagram_id or diagram_data must be provided")
        if self.diagram_id and self.diagram_data:
            raise ValueError("Only one of diagram_id or diagram_data should be provided")


class ExecutionResponse(BaseModel):
    """Response DTO for execution operations."""
    
    execution_id: str = Field(..., description="Unique execution ID")
    diagram_id: Optional[str] = Field(None, description="Associated diagram ID")
    status: ExecutionStatus = Field(..., description="Current execution status")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    @classmethod
    def from_state(cls, state: Any) -> "ExecutionResponse":
        """Create from execution state."""
        return cls(
            execution_id=state.execution_id,
            diagram_id=state.diagram_id,
            status=ExecutionStatus(state.status),
            started_at=state.started_at,
            completed_at=state.completed_at,
            error=state.error,
        )


class NodeExecutionStatus(BaseModel):
    """Status of a single node execution."""
    
    node_id: str = Field(..., description="Node ID")
    status: NodeStatus = Field(..., description="Node execution status")
    started_at: Optional[datetime] = Field(None, description="Node start time")
    completed_at: Optional[datetime] = Field(None, description="Node completion time")
    execution_count: int = Field(0, description="Number of times executed")
    error: Optional[str] = Field(None, description="Error message if failed")


class ExecutionStatusResponse(BaseModel):
    """Detailed execution status response."""
    
    execution: ExecutionResponse = Field(..., description="Execution summary")
    node_states: dict[str, NodeExecutionStatus] = Field(..., description="Node execution states")
    token_usage: Optional[dict[str, int]] = Field(None, description="Token usage statistics")
    variables: dict[str, Any] = Field(default_factory=dict, description="Execution variables")


class ExecutionUpdate(BaseModel):
    """Real-time execution update event."""
    
    type: str = Field(..., description="Update type")
    execution_id: str = Field(..., description="Execution ID")
    timestamp: datetime = Field(..., description="Update timestamp")
    data: dict[str, Any] = Field(..., description="Update data")


class ListExecutionsRequest(BaseModel):
    """Request DTO for listing executions."""
    
    diagram_id: Optional[str] = Field(None, description="Filter by diagram ID")
    status: Optional[ExecutionStatus] = Field(None, description="Filter by status")
    limit: int = Field(100, ge=1, le=1000, description="Results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")


class ListExecutionsResponse(BaseModel):
    """Response DTO for listing executions."""
    
    executions: list[ExecutionResponse] = Field(..., description="List of executions")
    total: int = Field(..., description="Total number of executions")
    limit: int = Field(..., description="Results per page")
    offset: int = Field(..., description="Current offset")


class NodeOutputRequest(BaseModel):
    """Request DTO for getting node outputs."""
    
    execution_id: str = Field(..., description="Execution ID")
    node_id: Optional[str] = Field(None, description="Specific node ID")


class NodeOutput(BaseModel):
    """Node output data."""
    
    node_id: str = Field(..., description="Node ID")
    success: bool = Field(..., description="Whether execution succeeded")
    result: Any = Field(..., description="Output result")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Output metadata")


class NodeOutputsResponse(BaseModel):
    """Response containing node outputs."""
    
    outputs: dict[str, NodeOutput] = Field(..., description="Node outputs by ID")