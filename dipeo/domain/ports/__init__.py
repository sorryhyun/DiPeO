"""Domain port definitions - DEPRECATED.

⚠️ DEPRECATED: This module is being phased out in favor of per-context ports.
Use the following imports instead:
- dipeo.domain.conversation.ports for ConversationRepository, PersonRepository
- dipeo.domain.diagram.ports for TemplateProcessorPort, TemplateResult
- dipeo.domain.integrations.ports for APIKeyPort, ASTParserPort

This module now only provides backward compatibility re-exports.
"""

import warnings

# Show deprecation warning once on module import
warnings.warn(
    "dipeo.domain.ports is deprecated. Use per-context ports instead:\n"
    "  - dipeo.domain.conversation.ports for conversation repositories\n"
    "  - dipeo.domain.diagram.ports for diagram ports and template processing\n"
    "  - dipeo.domain.integrations.ports for API and parser ports\n"
    "  - Storage ports remain in dipeo.domain.ports for now (cross-cutting)",
    DeprecationWarning,
    stacklevel=2,
)

# Storage ports remain here for now (cross-cutting infrastructure)
from .storage import (
    Artifact,
    ArtifactRef,
    ArtifactStorePort,
    BlobStorePort,
    DiagramInfo,
    FileInfo,
    FileSystemPort,
)

# Re-export from new locations for backward compatibility
from dipeo.domain.conversation.ports import (
    ConversationRepository,
    PersonRepository,
)

from dipeo.domain.diagram.ports import (
    TemplateProcessorPort,
    TemplateResult,
)

from dipeo.domain.integrations.ports import (
    APIKeyPort,
    ASTParserPort,
)

__all__ = [
    # Storage ports (remain here)
    "BlobStorePort",
    "FileSystemPort", 
    "ArtifactStorePort",
    "FileInfo",
    "Artifact",
    "ArtifactRef",
    "DiagramInfo",
    # Repository ports (re-exported from conversation)
    "ConversationRepository",
    "PersonRepository",
    # Template ports (re-exported from diagram)
    "TemplateProcessorPort",
    "TemplateResult",
    # Integration ports (re-exported from integrations)
    "APIKeyPort",
    "ASTParserPort",
]