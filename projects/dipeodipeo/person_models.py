"""
Pydantic models for person (LLM agent) generation via LLM.
Defines the structure for generating optimized person definitions.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class PersonDefinition(BaseModel):
    """Definition for a single person (LLM agent) in the DiPeO workflow."""

    identifier: str = Field(
        description="Unique identifier for this person (e.g., 'data_validator', 'analyzer')"
    )
    service: Literal["openai", "anthropic", "claude-code"] = Field(
        default="openai", description="LLM service provider"
    )
    model: str = Field(
        default="gpt-5-nano-2025-08-07",
        description="Model to use (e.g., 'gpt-5-nano-2025-08-07', 'gpt-5-mini-2025-08-07')",
    )
    api_key_id: str = Field(
        default="APIKEY_52609F", description="API key identifier for the service"
    )
    system_prompt: str = Field(
        description="Optimized system prompt defining the agent's role, responsibilities, and guidelines"
    )
    description: str = Field(
        description="Brief description of what this agent does in the workflow"
    )
    recommended_for: list[str] = Field(
        default_factory=list, description="List of task types this agent is recommended for"
    )


class PersonGenerationOutput(BaseModel):
    """Output structure for person generation containing all agent definitions."""

    persons: list[PersonDefinition] = Field(
        description="List of person definitions for the workflow"
    )
    person_types: list[str] = Field(
        description="List of person type identifiers for use in diagram structure"
    )
    rationale: Optional[str] = Field(
        default=None, description="Explanation of why these specific persons were created"
    )
