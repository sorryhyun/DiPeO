"""Subagent configuration models."""

from pydantic import BaseModel, Field


class SubagentConfig(BaseModel):
    """Configuration for a subagent.

    Subagents are child agents that can be spawned by a parent agent
    during execution. They inherit the model from the parent unless
    explicitly specified.

    Attributes:
        name: Unique identifier for the subagent
        description: Human-readable description (shown to parent agent)
        prompt: Inline system prompt for the subagent
        prompt_file: Path to file containing system prompt (relative to diagram)
        tools: List of tool names the subagent can use
        model: Model to use (default "inherit" uses parent's model)
        characteristics_file: Path to behavioral characteristics file
    """

    name: str = Field(description="Unique identifier for the subagent")
    description: str = Field(description="Description shown to parent agent when deciding to invoke")
    prompt: str | None = Field(
        default=None,
        description="Inline system prompt for the subagent"
    )
    prompt_file: str | None = Field(
        default=None,
        description="Path to file containing system prompt"
    )
    tools: list[str] = Field(
        default_factory=list,
        description="List of tool names the subagent can use"
    )
    model: str = Field(
        default="inherit",
        description="Model to use ('inherit' uses parent's model)"
    )
    characteristics_file: str | None = Field(
        default=None,
        description="Path to behavioral characteristics file"
    )

    def get_effective_prompt(self, base_path: str | None = None) -> str | None:
        """Get the effective prompt, loading from file if needed.

        Args:
            base_path: Base path for resolving relative file paths

        Returns:
            The system prompt string, or None if not specified
        """
        if self.prompt:
            return self.prompt

        if self.prompt_file and base_path:
            from pathlib import Path
            prompt_path = Path(base_path) / self.prompt_file
            if prompt_path.exists():
                return prompt_path.read_text()

        return None


class SubagentReference(BaseModel):
    """Reference to a subagent in a node configuration.

    This is used when a node references subagents defined at the diagram level.
    """

    name: str = Field(description="Name of the subagent to use")
    override_tools: list[str] | None = Field(
        default=None,
        description="Override tools for this specific invocation"
    )
