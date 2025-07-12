"""Server-specific persistence container with state store and message router."""

from dependency_injector import providers
from dipeo.container.runtime.persistence_container import PersistenceServicesContainer
from dipeo.infra import MessageRouter
from dipeo_server.infra.persistence.state_registry import state_store


class ServerPersistenceContainer(PersistenceServicesContainer):
    """Server-specific persistence container with proper overrides."""
    
    # Override state_store with server implementation
    state_store = providers.Singleton(lambda: state_store)
    
    # Override message_router with actual implementation  
    message_router = providers.Singleton(MessageRouter)