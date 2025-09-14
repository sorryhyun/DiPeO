"""Infrastructure adapter for diagram serialization.

This adapter wraps the existing diagram converter implementations
to implement the domain DiagramStorageSerializer port.
"""

import contextlib
import logging
from typing import TYPE_CHECKING

from dipeo.domain.diagram.ports import DiagramStorageSerializer, FormatStrategy

if TYPE_CHECKING:
    from dipeo.diagram_generated import DomainDiagram

logger = logging.getLogger(__name__)


class UnifiedSerializerAdapter(DiagramStorageSerializer):
    """Adapter that uses format strategies directly for serialization.

    This adapter provides a unified interface for diagram serialization
    using the domain format strategies.
    """

    def __init__(self):
        self._strategies = {}
        self._initialized = False
        self._initialize_converter()

    def _initialize_converter(self):
        from dipeo.domain.diagram.strategies import (
            ExecutableJsonStrategy,
            LightYamlStrategy,
            NativeJsonStrategy,
            ReadableYamlStrategy,
        )

        self._strategies = {
            "native": NativeJsonStrategy(),
            "json": NativeJsonStrategy(),  # Alias
            "light": LightYamlStrategy(),
            "readable": ReadableYamlStrategy(),
            "executable": ExecutableJsonStrategy(),
        }

    async def initialize(self):
        if self._initialized:
            return

        self._initialized = True

    def serialize_for_storage(self, diagram: "DomainDiagram", format: str) -> str:
        format = format.lower() if format else "native"
        if format in ["yaml", "yml"]:
            format = "light"
        strategy = self._strategies.get(format)
        if not strategy:
            raise ValueError(f"Unknown format: {format}")

        return strategy.serialize_from_domain(diagram)

    def deserialize_from_storage(
        self, content: str, format: str | None = None, diagram_path: str | None = None
    ) -> "DomainDiagram":
        if not format:
            format = self._detect_format(content)

        format = format.lower() if format else "native"
        if format in ["yaml", "yml"]:
            if "version: light" in content or "format: light" in content:
                format = "light"
            elif "version: readable" in content:
                format = "readable"
            else:
                format = "light"
        strategy = self._strategies.get(format)
        if not strategy:
            raise ValueError(f"Unknown format: {format}")

        return strategy.deserialize_to_domain(content, diagram_path)

    def _detect_format(self, content: str) -> str:
        import json

        import yaml

        try:
            data = json.loads(content)
            if isinstance(data, dict):
                if "nodes" in data and "arrows" in data:
                    return "native"
                elif "executable" in data:
                    return "executable"
        except json.JSONDecodeError:
            pass

        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                if "version" in data:
                    if data["version"] == "light":
                        return "light"
                    elif data["version"] == "readable":
                        return "readable"
                elif "format" in data and data["format"] == "light":
                    return "light"
        except yaml.YAMLError:
            pass

        return "native"


class FormatStrategyAdapter(DiagramStorageSerializer):
    """Adapter that uses format strategies for serialization.

    This adapter delegates to specific format strategies based on
    the requested format.
    """

    def __init__(self):
        self._strategies: dict[str, FormatStrategy] = {}
        self._initialize_strategies()

    def _initialize_strategies(self):
        from dipeo.domain.diagram.strategies import (
            ExecutableJsonStrategy,
            LightYamlStrategy,
            NativeJsonStrategy,
            ReadableYamlStrategy,
        )

        self._strategies["native"] = NativeJsonStrategy()
        self._strategies["json"] = NativeJsonStrategy()  # Alias
        self._strategies["light"] = LightYamlStrategy()
        self._strategies["readable"] = ReadableYamlStrategy()
        self._strategies["executable"] = ExecutableJsonStrategy()

    def register_strategy(self, format_id: str, strategy: FormatStrategy):
        self._strategies[format_id] = strategy

    def serialize_for_storage(self, diagram: "DomainDiagram", format: str) -> str:
        strategy = self._strategies.get(format)
        if not strategy:
            raise ValueError(f"No strategy registered for format: {format}")

        return strategy.serialize_from_domain(diagram)

    def deserialize_from_storage(
        self, content: str, format: str | None = None, diagram_path: str | None = None
    ) -> "DomainDiagram":
        if format:
            strategy = self._strategies.get(format)
            if not strategy:
                raise ValueError(f"No strategy registered for format: {format}")
            return strategy.deserialize_to_domain(content, diagram_path)

        import json

        import yaml

        data = None
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            with contextlib.suppress(yaml.YAMLError):
                data = yaml.safe_load(content)

        if data:
            best_strategy = None
            best_confidence = 0.0

            for format_id, strategy in self._strategies.items():
                try:
                    confidence = strategy.detect_confidence(data)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_strategy = strategy
                except Exception as e:
                    logger.debug(f"Error checking {format_id} format: {e}")

            if best_strategy and best_confidence > 0.5:
                logger.info(f"Auto-detected format with confidence {best_confidence}")
                return best_strategy.deserialize_to_domain(content, diagram_path)

        for format_id, strategy in self._strategies.items():
            try:
                if strategy.quick_match(content):
                    logger.info(f"Format matched by quick check: {format_id}")
                    return strategy.deserialize_to_domain(content, diagram_path)
            except Exception:
                continue

        raise ValueError("Could not detect format or deserialize content")


class CachingSerializerAdapter(DiagramStorageSerializer):
    """Decorator that adds caching to serialization operations.

    This can significantly speed up repeated serialization of the same diagrams.
    """

    def __init__(self, base_serializer: DiagramStorageSerializer, cache_size: int = 50):
        self.base_serializer = base_serializer
        self.cache_size = cache_size
        self._serialize_cache: dict[str, str] = {}
        self._deserialize_cache: dict[str, DomainDiagram] = {}

    def _get_serialize_key(self, diagram: "DomainDiagram", format: str) -> str:
        return f"{diagram.id}_{format}_{len(diagram.nodes)}_{len(diagram.arrows)}"

    def _get_deserialize_key(self, content: str, format: str | None) -> str:
        import hashlib

        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{content_hash}_{format}"

    def serialize_for_storage(self, diagram: "DomainDiagram", format: str) -> str:
        cache_key = self._get_serialize_key(diagram, format)

        if cache_key in self._serialize_cache:
            return self._serialize_cache[cache_key]

        result = self.base_serializer.serialize_for_storage(diagram, format)

        if len(self._serialize_cache) >= self.cache_size:
            first_key = next(iter(self._serialize_cache))
            del self._serialize_cache[first_key]

        self._serialize_cache[cache_key] = result
        return result

    def deserialize_from_storage(
        self, content: str, format: str | None = None, diagram_path: str | None = None
    ) -> "DomainDiagram":
        cache_key = self._get_deserialize_key(content, format)

        if cache_key in self._deserialize_cache:
            return self._deserialize_cache[cache_key]

        result = self.base_serializer.deserialize_from_storage(content, format, diagram_path)

        if len(self._deserialize_cache) >= self.cache_size:
            first_key = next(iter(self._deserialize_cache))
            del self._deserialize_cache[first_key]

        self._deserialize_cache[cache_key] = result
        return result
