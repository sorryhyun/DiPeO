"""Abstract interface for IR builders."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class IRMetadata(BaseModel):
    version: int
    generated_at: str
    source_files: int
    builder_type: str


class IRData(BaseModel):
    metadata: IRMetadata
    data: dict[str, Any]


class IRBuilderPort(ABC):
    @abstractmethod
    async def build_ir(
        self, source_data: dict[str, Any], config: dict[str, Any] | None = None
    ) -> IRData:
        pass

    @abstractmethod
    def validate_ir(self, ir_data: IRData) -> bool:
        pass

    @abstractmethod
    def get_cache_key(self, source_data: dict[str, Any]) -> str:
        """Generate deterministic cache key for source data."""
        pass
