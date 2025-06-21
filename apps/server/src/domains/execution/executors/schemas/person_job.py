"""
PersonJob node schema - LLM tasks with memory management
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any

from .base import BaseNodeProps
from src.__generated__.models import LLMService, ForgettingMode


class PersonConfig(BaseModel):
    """Configuration for a person (LLM instance)"""
    id: Optional[str] = Field(None, description="Unique identifier for the person")
    name: Optional[str] = Field(None, description="Display name for the person")
    service: Optional[LLMService] = Field(None, description="LLM service provider")
    model: Optional[str] = Field(None, description="Model identifier", alias="modelName")
    api_key_id: str = Field(..., description="API key reference")
    systemPrompt: Optional[str] = Field(None, description="System prompt for the LLM")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="Sampling temperature")
    
    class Config:
        use_enum_values = True
        populate_by_name = True
    
    @field_validator('model', mode='before')
    @classmethod
    def model_name_alias(cls, v, info):
        """Handle both 'model' and 'modelName' fields"""
        if not v and info.data and 'modelName' in info.data:
            return info.data['modelName']
        return v


class PersonJobProps(BaseNodeProps):
    """Properties for PersonJob node"""
    personId: Optional[str] = Field(None, description="Reference to existing person")
    person: Optional[PersonConfig] = Field(None, description="Inline person configuration")
    
    # Prompts
    prompt: Optional[str] = Field(None, description="Main prompt template")
    defaultPrompt: Optional[str] = Field(None, description="Default prompt if no prompt provided")
    firstOnlyPrompt: Optional[str] = Field(None, description="Prompt to use only on first execution")
    
    # Execution control
    maxIteration: Optional[int] = Field(None, ge=1, description="Maximum number of executions")
    contextCleaningRule: ForgettingMode = Field(
        ForgettingMode.no_forget,
        description="Memory management strategy"
    )
    interactive: bool = Field(False, description="Enable interactive mode")
    
    @model_validator(mode='after')
    def validate_person_config(self):
        """Ensure either personId or person is provided"""
        if not self.personId and not self.person:
            raise ValueError("Either personId or person configuration must be provided")
        
        if self.personId and self.person:
            raise ValueError("Cannot provide both personId and person configuration")
        
        return self
    
    @model_validator(mode='after')
    def validate_prompts(self):
        """Ensure at least one prompt is provided"""
        if not any([self.prompt, self.defaultPrompt, self.firstOnlyPrompt]):
            raise ValueError("At least one prompt (prompt, defaultPrompt, or firstOnlyPrompt) must be provided")
        
        return self
    
    @field_validator('prompt', 'defaultPrompt', 'firstOnlyPrompt')
    @classmethod
    def validate_prompt_template(cls, v):
        """Basic validation for template syntax"""
        if v and '{{' in v and '}}' in v:
            # Check for balanced double braces
            open_count = v.count('{{')
            close_count = v.count('}}')
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