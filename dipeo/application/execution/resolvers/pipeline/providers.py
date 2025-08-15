"""Provider system for explicit input injection.

Providers are explicit, typed sources that nodes must opt into via their InputSpecs.
This replaces the implicit special_inputs injection, making data flow explicit and predictable.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

from dipeo.diagram_generated.enums import ContentType
from dipeo.core.execution.envelope import Envelope, get_envelope_factory


class Provider(Protocol):
    """Protocol for input providers."""
    
    name: str
    content_type: ContentType
    
    async def provide(self, context: Any) -> Envelope | None:
        """Provide the input envelope."""
        ...


@dataclass
class ConversationProvider:
    """Provides conversation state for nodes that opt in."""
    
    name: str = "_conversation"
    content_type: ContentType = ContentType.OBJECT
    
    async def provide(self, context: Any) -> Envelope | None:
        """Provide conversation state envelope."""
        # Get conversation state from context
        if not hasattr(context, 'conversation_manager'):
            return None
            
        person_id = getattr(context, 'current_person_id', None)
        if not person_id:
            return None
            
        conv_state = await context.conversation_manager.get_state(person_id)
        if not conv_state:
            return None
            
        factory = get_envelope_factory()
        trace_id = getattr(context, 'execution_id', str(uuid4()))
        
        if hasattr(factory, 'conversation'):
            return factory.conversation(
                conv_state,
                produced_by="provider/conversation",
                trace_id=trace_id
            )
        else:
            # Use JSON for strict factory
            return factory.json(
                conv_state,
                produced_by="provider/conversation",
                trace_id=trace_id
            )


@dataclass
class VariablesProvider:
    """Provides execution variables for nodes that opt in."""
    
    name: str = "_variables"
    content_type: ContentType = ContentType.OBJECT
    
    async def provide(self, context: Any) -> Envelope | None:
        """Provide variables envelope."""
        if not hasattr(context, 'variables') or not context.variables:
            return None
            
        factory = get_envelope_factory()
        trace_id = getattr(context, 'execution_id', str(uuid4()))
        
        return factory.json(
            dict(context.variables),
            produced_by="provider/variables",
            trace_id=trace_id
        )


@dataclass
class FirstExecutionProvider:
    """Provides first execution mapping for PersonJob nodes."""
    
    name: str = "_first_execution"
    content_type: ContentType = ContentType.OBJECT
    
    async def provide(self, context: Any) -> Envelope | None:
        """Provide first execution mapping envelope.
        
        This provider handles the special case where PersonJob nodes
        receive inputs on their first execution only.
        """
        # This would need access to edge metadata to determine mappings
        # For now, return None as this needs deeper integration
        return None


class ProviderRegistry:
    """Registry for available providers."""
    
    def __init__(self):
        self._providers: dict[str, Provider] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default providers."""
        self.register(ConversationProvider())
        self.register(VariablesProvider())
        self.register(FirstExecutionProvider())
    
    def register(self, provider: Provider):
        """Register a provider."""
        self._providers[provider.name] = provider
    
    def get(self, name: str) -> Provider | None:
        """Get a provider by name."""
        return self._providers.get(name)
    
    def all(self) -> dict[str, Provider]:
        """Get all providers."""
        return self._providers.copy()


# Global registry instance
_registry = ProviderRegistry()


def get_provider(name: str) -> Provider | None:
    """Get a provider by name from the global registry."""
    return _registry.get(name)


def register_provider(provider: Provider):
    """Register a provider in the global registry."""
    _registry.register(provider)


def get_all_providers() -> dict[str, Provider]:
    """Get all registered providers."""
    return _registry.all()