"""Common response DTOs for API operations."""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""

    success: bool = Field(..., description="Whether the operation succeeded")
    data: Optional[T] = Field(None, description="Response data if successful")
    error: Optional["ErrorDetail"] = Field(None, description="Error details if failed")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        return cls(success=True, data=data, error=None)

    @classmethod
    def fail(cls, error: "ErrorDetail") -> "ApiResponse[T]":
        return cls(success=False, data=None, error=error)


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    field_errors: Optional[dict[str, list[str]]] = Field(
        None, description="Field-specific errors"
    )
    trace_id: Optional[str] = Field(None, description="Request trace ID for debugging")


class PageInfo(BaseModel):
    """Pagination information."""

    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Current offset")
    page: int = Field(..., description="Current page number (1-based)")
    pages: int = Field(..., description="Total number of pages")

    @classmethod
    def from_params(cls, total: int, limit: int, offset: int) -> "PageInfo":
        """Create from pagination parameters."""
        page = (offset // limit) + 1
        pages = (total + limit - 1) // limit  # Ceiling division
        return cls(
            total=total,
            limit=limit,
            offset=offset,
            page=page,
            pages=pages,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    items: list[T] = Field(..., description="List of items")
    page_info: PageInfo = Field(..., description="Pagination information")


class BatchOperationResult(BaseModel):
    """Result of a batch operation."""

    total: int = Field(..., description="Total items processed")
    succeeded: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: list[ErrorDetail] = Field(
        default_factory=list, description="List of errors"
    )


class ValidationError(BaseModel):
    """Validation error details."""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(..., description="Invalid value provided")


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Check timestamp"
    )
    services: dict[str, bool] = Field(..., description="Status of dependent services")
