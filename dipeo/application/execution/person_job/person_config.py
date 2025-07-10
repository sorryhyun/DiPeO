"""Person configuration for execution without requiring full diagram."""

from dataclasses import dataclass
from typing import Optional, Any

from dipeo.models import PersonLLMConfig


@dataclass
class PersonConfig:
    """Configuration for a person, extracted from diagram.
    
    This class holds all person-specific data needed for execution,
    allowing services to operate without the full diagram.
    """
    id: str
    label: str
    llm_config: Optional[PersonLLMConfig] = None
    
    @property
    def display_name(self) -> str:
        """Get the display name for the person."""
        return self.label if self.label else self.id


@dataclass 
class NodeConnectionInfo:
    """Information about node connections for determining conversation output needs."""
    node_id: str
    has_conversation_output: bool = False
    has_conversation_input: bool = False