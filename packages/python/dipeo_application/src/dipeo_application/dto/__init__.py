"""Application layer DTOs."""

# Import all DTOs
from .diagram_dto import (
    CreateDiagramRequest,
    DiagramResponse,
    UpdateDiagramRequest,
    ListDiagramsRequest,
    ListDiagramsResponse,
)
from .execution_dto import (
    ExecutionStatus,
    NodeStatus,
    ExecuteDiagramRequest,
    ExecutionResponse,
    NodeExecutionStatus,
    ExecutionStatusResponse,
    ExecutionUpdate,
    ListExecutionsRequest,
    ListExecutionsResponse,
    NodeOutputRequest,
    NodeOutput,
    NodeOutputsResponse,
)
from .person_dto import (
    LLMService,
    ForgettingMode,
    CreatePersonRequest,
    PersonResponse,
    UpdatePersonRequest,
    PersonMemoryStats,
    ClearPersonMemoryRequest,
    ListPersonsRequest,
    ListPersonsResponse,
)
from .response_dto import (
    ApiResponse,
    ErrorDetail,
    PageInfo,
    PaginatedResponse,
    BatchOperationResult,
    ValidationError,
    HealthCheckResponse,
)

# Re-export generated DTOs when available
from .__generated__ import *  # noqa: F403, F401

__all__ = [
    # Diagram DTOs
    "CreateDiagramRequest",
    "DiagramResponse",
    "UpdateDiagramRequest",
    "ListDiagramsRequest",
    "ListDiagramsResponse",
    # Execution DTOs
    "ExecutionStatus",
    "NodeStatus",
    "ExecuteDiagramRequest",
    "ExecutionResponse",
    "NodeExecutionStatus",
    "ExecutionStatusResponse",
    "ExecutionUpdate",
    "ListExecutionsRequest",
    "ListExecutionsResponse",
    "NodeOutputRequest",
    "NodeOutput",
    "NodeOutputsResponse",
    # Person DTOs
    "LLMService",
    "ForgettingMode",
    "CreatePersonRequest",
    "PersonResponse",
    "UpdatePersonRequest",
    "PersonMemoryStats",
    "ClearPersonMemoryRequest",
    "ListPersonsRequest",
    "ListPersonsResponse",
    # Common DTOs
    "ApiResponse",
    "ErrorDetail",
    "PageInfo",
    "PaginatedResponse",
    "BatchOperationResult",
    "ValidationError",
    "HealthCheckResponse",
]