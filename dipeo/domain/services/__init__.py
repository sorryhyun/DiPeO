"""Domain services module.

This module provides backward compatibility references to services that have been moved
to their proper domain locations during the architectural refactoring.
"""

# Note: Services have been moved to their respective domain modules:
# - API services: dipeo.domain.api.services
# - File services: dipeo.domain.file.services  
# - Diagram services: dipeo.domain.diagram.services
# - Conversation services: dipeo.domain.conversation.services
# - Database services: dipeo.domain.db.services

# For backward compatibility, maintain empty references
InputResolutionService = None  # Moved to application layer
FlowControlService = None  # Moved to application layer
PersonJobOrchestrator = None  # Moved to application layer

__all__ = [
    "InputResolutionService",
    "FlowControlService",
    "PersonJobOrchestrator",
]