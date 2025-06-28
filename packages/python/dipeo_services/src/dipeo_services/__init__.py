"""DiPeO Services - Simplified domain services for shared use."""

__version__ = "0.1.0"

# Import only the working services for now
from .file import SimpleFileService
from .memory import SimpleMemoryService
from .text import SimpleTextService
from .file_ops import SimpleFileOperationsService

__all__ = [
    "SimpleFileService", 
    "SimpleMemoryService",
    "SimpleTextService",
    "SimpleFileOperationsService",
]

# TODO: Add SimpleConversationService when it's updated to use correct domain models