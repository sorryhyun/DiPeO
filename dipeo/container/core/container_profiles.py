"""Container profile definitions for different usage contexts."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ContainerProfile:
    """Defines which services to initialize for a specific context."""
    
    name: str
    description: str
    
    # Service flags
    include_execution_service: bool = True
    include_state_management: bool = True  # state_store, message_router
    include_llm_services: bool = True
    include_conversation_manager: bool = True
    include_notion_service: bool = True
    include_flow_control: bool = True
    
    # Lazy loading flags  
    lazy_load_execution: bool = False
    lazy_load_llm: bool = False
    lazy_load_integrations: bool = False
    
    # Additional config
    config_overrides: dict[str, Any] = None
    
    def __post_init__(self):
        if self.config_overrides is None:
            self.config_overrides = {}


# Predefined profiles
PROFILES = {
    'full': ContainerProfile(
        name='full',
        description='Full container with all services (default)',
        include_execution_service=True,
        include_state_management=True,
        include_llm_services=True,
        include_conversation_manager=True,
        include_notion_service=True,
        include_flow_control=True,
    ),
    
    'edit': ContainerProfile(
        name='edit',
        description='Minimal container for diagram editing only',
        include_execution_service=False,
        include_state_management=False,
        include_llm_services=False,
        include_conversation_manager=False,
        include_notion_service=False,
        include_flow_control=False,
    ),
    
    'execution': ContainerProfile(
        name='execution',
        description='Full execution container with lazy loading',
        include_execution_service=True,
        include_state_management=True,
        include_llm_services=True,
        include_conversation_manager=True,
        include_notion_service=True,
        include_flow_control=True,
        lazy_load_execution=True,
        lazy_load_llm=True,
        lazy_load_integrations=True,
    ),
    
    'analysis': ContainerProfile(
        name='analysis',
        description='Container for diagram analysis and validation',
        include_execution_service=False,
        include_state_management=False,
        include_llm_services=False,
        include_conversation_manager=False,
        include_notion_service=False,
        include_flow_control=True,  # For condition analysis
    ),
    
    'cli': ContainerProfile(
        name='cli',
        description='CLI container with on-demand loading',
        include_execution_service=True,
        include_state_management=False,  # CLI doesn't need server state
        include_llm_services=True,
        include_conversation_manager=True,
        include_notion_service=True,
        include_flow_control=True,
        lazy_load_execution=True,
        lazy_load_llm=True,
        lazy_load_integrations=True,
    ),
}


def get_profile(name: str) -> ContainerProfile:
    """Get a container profile by name."""
    if name not in PROFILES:
        raise ValueError(f"Unknown profile: {name}. Available: {list(PROFILES.keys())}")
    return PROFILES[name]


def list_profiles() -> dict[str, str]:
    """List available profiles with descriptions."""
    return {name: profile.description for name, profile in PROFILES.items()}
