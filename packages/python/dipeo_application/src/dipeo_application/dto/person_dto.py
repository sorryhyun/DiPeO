"""DTOs for person (AI agent) related operations."""

from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class LLMService(str, Enum):
    """Available LLM services."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GROK = "grok"


class ForgettingMode(str, Enum):
    """Memory forgetting modes."""
    NO_FORGET = "no_forget"
    ON_EVERY_TURN = "on_every_turn"
    UPON_REQUEST = "upon_request"


class CreatePersonRequest(BaseModel):
    """Request DTO for creating a person."""
    
    name: str = Field(..., description="Person name")
    system_prompt: str = Field(..., description="System prompt for the AI")
    service: LLMService = Field(..., description="LLM service to use")
    model: str = Field(..., description="Model name")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature setting")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens")
    forgetting_mode: ForgettingMode = Field(
        ForgettingMode.NO_FORGET,
        description="Memory forgetting strategy"
    )


class PersonResponse(BaseModel):
    """Response DTO for person operations."""
    
    id: str = Field(..., description="Person ID")
    name: str = Field(..., description="Person name")
    service: LLMService = Field(..., description="LLM service")
    model: str = Field(..., description="Model name")
    temperature: float = Field(..., description="Temperature setting")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens")
    forgetting_mode: ForgettingMode = Field(..., description="Memory forgetting strategy")
    
    @classmethod
    def from_domain(cls, person: Any) -> "PersonResponse":
        """Create from domain model."""
        return cls(
            id=person.id,
            name=person.name,
            service=LLMService(person.service),
            model=person.model,
            temperature=person.temperature,
            max_tokens=person.max_tokens,
            forgetting_mode=ForgettingMode(
                getattr(person, 'forgetting_mode', 'no_forget')
            ),
        )


class UpdatePersonRequest(BaseModel):
    """Request DTO for updating a person."""
    
    name: Optional[str] = Field(None, description="New person name")
    system_prompt: Optional[str] = Field(None, description="New system prompt")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="New temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="New max tokens")
    forgetting_mode: Optional[ForgettingMode] = Field(None, description="New forgetting mode")


class PersonMemoryStats(BaseModel):
    """Person memory statistics."""
    
    person_id: str = Field(..., description="Person ID")
    message_count: int = Field(..., description="Number of messages in memory")
    total_tokens: int = Field(..., description="Total tokens used")
    memory_type: str = Field(..., description="Type of memory implementation")


class ClearPersonMemoryRequest(BaseModel):
    """Request DTO for clearing person memory."""
    
    person_id: str = Field(..., description="Person ID")
    execution_id: Optional[str] = Field(None, description="Specific execution context")


class ListPersonsRequest(BaseModel):
    """Request DTO for listing persons."""
    
    diagram_id: Optional[str] = Field(None, description="Filter by diagram ID")
    service: Optional[LLMService] = Field(None, description="Filter by LLM service")
    limit: int = Field(100, ge=1, le=1000, description="Results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")


class ListPersonsResponse(BaseModel):
    """Response DTO for listing persons."""
    
    persons: list[PersonResponse] = Field(..., description="List of persons")
    total: int = Field(..., description="Total number of persons")
    limit: int = Field(..., description="Results per page")
    offset: int = Field(..., description="Current offset")