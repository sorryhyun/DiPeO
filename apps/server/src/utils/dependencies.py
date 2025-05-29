
from functools import lru_cache

from ..services.api_key_service import APIKeyService
from ..services.llm_service import LLMService
from ..services.diagram_service import DiagramService
from ..services.unified_file_service import UnifiedFileService
from ..services.memory_service import MemoryService


@lru_cache()
def get_api_key_service() -> APIKeyService:
    """Get singleton APIKeyService instance."""
    return APIKeyService()


@lru_cache()
def get_llm_service() -> LLMService:
    """Get singleton LLMService instance."""
    return LLMService(get_api_key_service())


@lru_cache()
def get_diagram_service() -> DiagramService:
    """Get singleton DiagramService instance."""
    return DiagramService(get_llm_service())


@lru_cache()
def get_unified_file_service() -> UnifiedFileService:
    """Get singleton UnifiedFileService instance."""
    return UnifiedFileService()


@lru_cache()
def get_memory_service() -> MemoryService:
    """Get singleton MemoryService instance."""
    return MemoryService()