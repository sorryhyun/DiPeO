"""Pydantic input models for Claude Code tools."""

from pydantic import BaseModel, Field


class MemorySelectionInput(BaseModel):
    """Input model for memory message selection tool."""

    message_ids: list[str] = Field(
        description="List of message IDs to select for context"
    )


class DecisionInput(BaseModel):
    """Input model for binary decision making tool."""

    decision: bool = Field(
        description="True for YES, False for NO"
    )


class SubagentPersistInput(BaseModel):
    """Base input model for subagent persistence operations."""

    content: str = Field(
        description="Content to persist"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Optional metadata for the persisted content"
    )
