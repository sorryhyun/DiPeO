"""Domain ports for diagram compilation and conversion.

This module defines the domain-owned contracts for diagram operations,
moving them from core/ports to domain ownership.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from dipeo.diagram_generated import DiagramFormat, DomainDiagram
    from dipeo.domain.base.storage_port import DiagramInfo
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram


# ============================================================================
# Diagram Compilation Port
# ============================================================================


class DiagramCompiler(Protocol):
    """Protocol for compiling between different diagram representations.

    This is the domain-owned contract for diagram compilation.
    Implementations transform DomainDiagram to ExecutableDiagram.
    """

    def compile(self, domain_diagram: "DomainDiagram") -> "ExecutableDiagram": ...


# ============================================================================
# Diagram Storage Serialization Port
# ============================================================================


class DiagramStorageSerializer(ABC):
    """Interface for serializing diagrams to/from storage formats.

    This is used ONLY for file persistence. Internal APIs should
    pass DomainDiagram objects directly.
    """

    @abstractmethod
    def serialize_for_storage(self, diagram: "DomainDiagram", format: str) -> str:
        pass

    @abstractmethod
    def deserialize_from_storage(
        self, content: str, format: str | None = None, diagram_path: str | None = None
    ) -> "DomainDiagram":
        pass

    def validate(self, content: str) -> tuple[bool, list[str]]:
        try:
            self.deserialize_from_storage(content)
            return True, []
        except Exception as e:
            return False, [str(e)]


# ============================================================================
# Format Strategy Port
# ============================================================================


class FormatStrategy(ABC):
    """Strategy for handling specific diagram formats.

    Each format (light, native, readable) has its own strategy.
    """

    @abstractmethod
    def parse(self, content: str) -> Any:
        pass

    @abstractmethod
    def format(self, data: Any) -> str:
        pass

    @abstractmethod
    def deserialize_to_domain(
        self, content: str, diagram_path: str | None = None
    ) -> "DomainDiagram":
        pass

    @abstractmethod
    def serialize_from_domain(self, diagram: "DomainDiagram") -> str:
        pass

    @abstractmethod
    def detect_confidence(self, data: dict[str, Any]) -> float:
        pass

    @property
    @abstractmethod
    def format_id(self) -> str:
        pass

    @property
    @abstractmethod
    def format_info(self) -> dict[str, str]:
        pass

    def quick_match(self, content: str) -> bool:
        try:
            self.parse(content)
            return True
        except Exception:
            return False


# Note: DiagramPort has been replaced with segregated interfaces.
# See dipeo.domain.diagram.segregated_ports for the new interfaces:
# - DiagramFilePort: File I/O operations
# - DiagramFormatPort: Format detection and conversion
# - DiagramRepositoryPort: CRUD and query operations
# - DiagramCompiler: Compilation (remains here)

# ============================================================================
# Template Processing Port
# ============================================================================


@dataclass
class TemplateResult:
    """Result of template processing with detailed feedback."""

    content: str
    missing_keys: list[str] = field(default_factory=list)
    used_keys: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class TemplateProcessorPort(Protocol):
    """Port for template processing functionality.

    Infrastructure layer must provide implementations for variable substitution,
    conditionals, loops, and other template processing features.
    """

    def process(self, template: str, context: dict[str, Any]) -> TemplateResult: ...

    def process_simple(self, template: str, context: dict[str, Any]) -> str: ...

    def process_single_brace(self, template: str, context: dict[str, Any]) -> str: ...

    def extract_variables(self, template: str) -> list[str]: ...
