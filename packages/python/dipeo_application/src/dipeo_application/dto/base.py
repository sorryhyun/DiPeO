"""Base classes for DTOs with common patterns."""

from typing import TypeVar, Generic, Optional, Any, List, Dict, Type
from pydantic import BaseModel, Field
from datetime import datetime
from abc import ABC, abstractmethod


T = TypeVar("T")
D = TypeVar("D")


class BaseDTO(BaseModel):
    """Base class for all DTOs with common configuration."""

    model_config = {
        # Allow population by field name
        "populate_by_name": True,
        # Use enum values
        "use_enum_values": True,
        # Enable JSON schema
        "json_schema_extra": {"example": {}},
    }


class ConvertibleDTO(BaseDTO, ABC, Generic[D]):
    """Base class for DTOs that can convert to/from domain models."""

    @classmethod
    @abstractmethod
    def from_domain(cls: Type[T], domain_model: D) -> T:
        """Convert from domain model to DTO."""
        pass

    @abstractmethod
    def to_domain(self) -> D:
        """Convert from DTO to domain model."""
        pass


class RequestDTO(BaseDTO):
    """Base class for request DTOs with validation."""

    def validate_request(self) -> None:
        """Override to add custom validation logic."""
        pass


class ResponseDTO(BaseDTO, Generic[T]):
    """Base class for response DTOs."""

    success: bool = Field(True, description="Whether the operation succeeded")
    data: Optional[T] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )

    @classmethod
    def ok(cls, data: T) -> "ResponseDTO[T]":
        """Create a successful response."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> "ResponseDTO[T]":
        """Create a failed response."""
        return cls(success=False, error=error)


class PaginatedResponseDTO(ResponseDTO[List[T]], Generic[T]):
    """Base class for paginated responses."""

    total: int = Field(0, description="Total number of items")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Items per page")
    pages: int = Field(1, description="Total number of pages")

    def model_post_init(self, __context: Any) -> None:
        """Calculate total pages after initialization."""
        if self.page_size > 0:
            self.pages = (self.total + self.page_size - 1) // self.page_size


class ListRequestDTO(RequestDTO):
    """Base class for list/query requests with pagination."""

    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.page_size


class BatchRequestDTO(RequestDTO, Generic[T]):
    """Base class for batch operations."""

    items: List[T] = Field(
        ..., min_items=1, max_items=1000, description="Items to process"
    )
    continue_on_error: bool = Field(False, description="Continue processing on error")


class BatchResponseDTO(ResponseDTO[List[T]], Generic[T]):
    """Base class for batch operation responses."""

    succeeded: int = Field(0, description="Number of successful operations")
    failed: int = Field(0, description="Number of failed operations")
    errors: Dict[int, str] = Field(default_factory=dict, description="Errors by index")
