from abc import ABC, abstractmethod
from typing import Any


class DiagramConverter(ABC):
    @abstractmethod
    def serialize(self, diagram: dict[str, Any]) -> str:
        pass

    @abstractmethod
    def deserialize(self, content: str) -> dict[str, Any]:
        pass

    def validate(self, content: str) -> tuple[bool, list[str]]:
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
    def parse(self, content: str) -> dict[str, Any]:
        pass

    @abstractmethod
    def format(self, data: dict[str, Any]) -> str:
        pass

    @abstractmethod
    def extract_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def extract_arrows(
        self, data: dict[str, Any], nodes: dict[str, Any]
    ) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def build_export_data(self, diagram: dict[str, Any]) -> dict[str, Any]:
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
