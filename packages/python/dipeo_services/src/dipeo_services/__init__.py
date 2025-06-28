"""DiPeO Services - Simplified domain services for shared use."""

__version__ = "0.1.0"

# Import all services
from .file import SimpleFileService
from .memory import SimpleMemoryService
from .text import SimpleTextService
from .file_ops import SimpleFileOperationsService
from .conversation import SimpleConversationService
from .api_integration import APIIntegrationDomainService
from .notion_integration import NotionIntegrationDomainService

__all__ = [
    "SimpleFileService", 
    "SimpleMemoryService",
    "SimpleTextService",
    "SimpleFileOperationsService",
    "SimpleConversationService",
    "APIIntegrationDomainService",
    "NotionIntegrationDomainService",
]