"""Abstract interface for IR builders."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


class IRMetadata(BaseModel):
    """Metadata for generated IR."""

    version: int
    generated_at: str
    source_files: int
    builder_type: str


class IRData(BaseModel):
    """Unified IR data structure."""

    metadata: IRMetadata
    data: dict[str, Any]


class IRBuilderPort(ABC):
    """Abstract interface for IR builders."""

    @abstractmethod
    async def build_ir(
        self, source_data: dict[str, Any], config: Optional[dict[str, Any]] = None
    ) -> IRData:
        """Build IR from source data.

        Args:
            source_data: Input data to build IR from
            config: Optional configuration parameters

        Returns:
            IRData containing the built IR
        """
        pass

    @abstractmethod
    def validate_ir(self, ir_data: IRData) -> bool:
        """Validate IR structure.

        Args:
            ir_data: IR data to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def get_cache_key(self, source_data: dict[str, Any]) -> str:
        """Generate cache key for source data.

        Args:
            source_data: Input data to generate cache key for

        Returns:
            Deterministic cache key string
        """
        pass
