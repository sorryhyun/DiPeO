"""
PersonJob node schema - LLM tasks with memory management
"""

from typing import Any, Dict, Optional

from dipeo_domain import ForgettingMode, PersonConfiguration
from pydantic import Field, field_validator, model_validator

from .base import BaseNodeProps


class PersonJobProps(BaseNodeProps):
    """Properties for PersonJob node"""

    personId: Optional[str] = Field(None, description="Reference to existing person")
    person: Optional[PersonConfiguration] = Field(
        None, description="Inline person configuration"
    )

    # Prompts
    prompt: Optional[str] = Field(None, description="Main prompt template")
    defaultPrompt: Optional[str] = Field(
        None, description="Default prompt if no prompt provided"
    )
    firstOnlyPrompt: Optional[str] = Field(
        None, description="Prompt to use only on first execution"
    )

    # Execution control
    maxIteration: Optional[int] = Field(
        None, ge=1, description="Maximum number of executions"
    )
    contextCleaningRule: ForgettingMode = Field(
        ForgettingMode.no_forget, description="Memory management strategy"
    )
    interactive: bool = Field(False, description="Enable interactive mode")

    @model_validator(mode="after")
    def validate_person_config(self):
        """Ensure either personId or person is provided"""
        if not self.personId and not self.person:
            raise ValueError("Either personId or person configuration must be provided")

        if self.personId and self.person:
            raise ValueError("Cannot provide both personId and person configuration")

        return self

    @model_validator(mode="after")
    def validate_prompts(self):
        """Ensure at least one prompt is provided"""
        if not any([self.prompt, self.defaultPrompt, self.firstOnlyPrompt]):
            raise ValueError(
                "At least one prompt (prompt, defaultPrompt, or firstOnlyPrompt) must be provided"
            )

        return self

    @field_validator("prompt", "defaultPrompt", "firstOnlyPrompt")
    @classmethod
    def validate_prompt_template(cls, v):
        """Basic validation for template syntax"""
        if v and "{{" in v and "}}" in v:
            # Check for balanced double braces
            open_count = v.count("{{")
            close_count = v.count("}}")
            if open_count != close_count:
                raise ValueError("Unbalanced template braces in prompt")
        return v

    def get_effective_prompt(self, execution_count: int = 0) -> Optional[str]:
        """Get the appropriate prompt based on execution count"""
        if execution_count == 0 and self.firstOnlyPrompt:
            return self.firstOnlyPrompt
        return self.prompt or self.defaultPrompt

    def substitute_variables(self, prompt: str, inputs: Dict[str, Any]) -> str:
        """Substitute variables in prompt template"""
        if not prompt:
            return prompt

        result = prompt
        for key, value in inputs.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))

        return result


class PersonBatchJobProps(PersonJobProps):
    """Properties for PersonBatchJob node"""

    batchSize: int = Field(1, ge=1, description="Number of items to process in batch")

    class Config:
        use_enum_values = True
