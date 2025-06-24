from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from dipeo_domain import DomainDiagram


class DiagramConverter(ABC):

    @abstractmethod
    def serialize(self, diagram: DomainDiagram) -> str:
        pass

    @abstractmethod
    def deserialize(self, content: str) -> DomainDiagram:
        pass

    def validate(self, content: str) -> Tuple[bool, List[str]]:
        try:
            self.deserialize(content)
            return True, []
        except Exception as e:
            return False, [str(e)]

    def detect_format_confidence(self, content: str) -> float:
        try:
            self.deserialize(content)
            return 1.0
        except Exception:
            return 0.0


class FormatStrategy(ABC):

    @abstractmethod
    def parse(self, content: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def format(self, data: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def extract_arrows(
        self, data: Dict[str, Any], nodes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def build_export_data(self, diagram: DomainDiagram) -> Dict[str, Any]:
        pass

    @abstractmethod
    def detect_confidence(self, data: Dict[str, Any]) -> float:
        pass

    @property
    @abstractmethod
    def format_id(self) -> str:
        pass

    @property
    @abstractmethod
    def format_info(self) -> Dict[str, str]:
        pass

    def quick_match(self, content: str) -> bool:
        try:
            self.parse(content)
            return True
        except Exception:
            return False
