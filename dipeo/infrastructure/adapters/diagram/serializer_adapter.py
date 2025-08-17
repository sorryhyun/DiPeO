"""Infrastructure adapter for diagram serialization.

This adapter wraps the existing diagram converter implementations
to implement the domain DiagramStorageSerializer port.
"""

import logging
from typing import TYPE_CHECKING, Any

from dipeo.domain.diagram.ports import DiagramStorageSerializer, FormatStrategy

if TYPE_CHECKING:
    from dipeo.diagram_generated import DomainDiagram

logger = logging.getLogger(__name__)


class UnifiedSerializerAdapter(DiagramStorageSerializer):
    """Adapter that wraps the existing UnifiedDiagramConverter.
    
    This adapter provides backward compatibility with the existing
    converter implementation while implementing the new domain port.
    """
    
    def __init__(self):
        """Initialize the serializer adapter."""
        self._converter = None
        self._initialize_converter()
    
    def _initialize_converter(self):
        """Initialize the underlying converter implementation."""
        from dipeo.infrastructure.services.diagram import DiagramConverterService
        self._converter = DiagramConverterService()
        logger.info("Initialized DiagramConverterService")
    
    def serialize_for_storage(self, diagram: "DomainDiagram", format: str) -> str:
        """Serialize a DomainDiagram to string for file storage.
        
        Args:
            diagram: The DomainDiagram to serialize
            format: Target format ('json', 'yaml', 'light', 'readable', 'native')
            
        Returns:
            String representation for file storage
        """
        if not self._converter:
            raise RuntimeError("Converter not initialized")
        
        logger.debug(f"Serializing diagram {diagram.id} to {format} format")
        
        # Map format names to converter method
        if format in ["json", "native"]:
            return self._converter.serialize_native(diagram)
        elif format == "yaml":
            return self._converter.serialize_native_yaml(diagram) 
        elif format == "light":
            return self._converter.serialize_light(diagram)
        elif format == "readable":
            return self._converter.serialize_readable(diagram)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def deserialize_from_storage(self, content: str, format: str | None = None) -> "DomainDiagram":
        """Deserialize file content to DomainDiagram.
        
        Args:
            content: String content from file
            format: Optional format hint, will auto-detect if not provided
            
        Returns:
            DomainDiagram instance
        """
        if not self._converter:
            raise RuntimeError("Converter not initialized")
        
        logger.debug(f"Deserializing content with format hint: {format}")
        
        # Let the converter auto-detect if no format specified
        return self._converter.deserialize(content, format_hint=format)


class FormatStrategyAdapter(DiagramStorageSerializer):
    """Adapter that uses format strategies for serialization.
    
    This adapter delegates to specific format strategies based on
    the requested format.
    """
    
    def __init__(self):
        """Initialize the format strategy adapter."""
        self._strategies: dict[str, FormatStrategy] = {}
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize format strategies."""
        # Use the converter service for now as strategies don't exist yet
        # This is a placeholder implementation
        logger.info("Format strategies not implemented yet, using placeholder")
    
    def register_strategy(self, format_id: str, strategy: FormatStrategy):
        """Register a new format strategy.
        
        Args:
            format_id: Identifier for the format
            strategy: The strategy implementation
        """
        self._strategies[format_id] = strategy
        logger.debug(f"Registered strategy for format: {format_id}")
    
    def serialize_for_storage(self, diagram: "DomainDiagram", format: str) -> str:
        """Serialize using the appropriate format strategy.
        
        Args:
            diagram: The DomainDiagram to serialize
            format: Target format
            
        Returns:
            String representation for file storage
        """
        strategy = self._strategies.get(format)
        if not strategy:
            raise ValueError(f"No strategy registered for format: {format}")
        
        logger.debug(f"Serializing with {format} strategy")
        return strategy.serialize_from_domain(diagram)
    
    def deserialize_from_storage(self, content: str, format: str | None = None) -> "DomainDiagram":
        """Deserialize using the appropriate format strategy.
        
        Args:
            content: String content from file
            format: Optional format hint
            
        Returns:
            DomainDiagram instance
        """
        if format:
            # Use specified format
            strategy = self._strategies.get(format)
            if not strategy:
                raise ValueError(f"No strategy registered for format: {format}")
            return strategy.deserialize_to_domain(content)
        
        # Auto-detect format
        logger.debug("Auto-detecting format from content")
        
        # Try to parse as JSON/YAML first to get structure
        import json
        import yaml
        
        data = None
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError:
                pass
        
        if data:
            # Check each strategy's confidence
            best_strategy = None
            best_confidence = 0.0
            
            for format_id, strategy in self._strategies.items():
                try:
                    confidence = strategy.detect_confidence(data)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_strategy = strategy
                        logger.debug(f"Format {format_id} confidence: {confidence}")
                except Exception as e:
                    logger.debug(f"Error checking {format_id} format: {e}")
            
            if best_strategy and best_confidence > 0.5:
                logger.info(f"Auto-detected format with confidence {best_confidence}")
                return best_strategy.deserialize_to_domain(content)
        
        # Fallback: try each strategy
        for format_id, strategy in self._strategies.items():
            try:
                if strategy.quick_match(content):
                    logger.info(f"Format matched by quick check: {format_id}")
                    return strategy.deserialize_to_domain(content)
            except Exception:
                continue
        
        raise ValueError("Could not detect format or deserialize content")


class CachingSerializerAdapter(DiagramStorageSerializer):
    """Decorator that adds caching to serialization operations.
    
    This can significantly speed up repeated serialization of the same diagrams.
    """
    
    def __init__(self, base_serializer: DiagramStorageSerializer, cache_size: int = 50):
        """Initialize the caching serializer.
        
        Args:
            base_serializer: The underlying serializer to wrap
            cache_size: Maximum number of cached serializations
        """
        self.base_serializer = base_serializer
        self.cache_size = cache_size
        self._serialize_cache: dict[str, str] = {}
        self._deserialize_cache: dict[str, "DomainDiagram"] = {}
    
    def _get_serialize_key(self, diagram: "DomainDiagram", format: str) -> str:
        """Generate cache key for serialization."""
        return f"{diagram.id}_{format}_{len(diagram.nodes)}_{len(diagram.arrows)}"
    
    def _get_deserialize_key(self, content: str, format: str | None) -> str:
        """Generate cache key for deserialization."""
        # Use hash of content for key
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{content_hash}_{format}"
    
    def serialize_for_storage(self, diagram: "DomainDiagram", format: str) -> str:
        """Serialize with caching."""
        cache_key = self._get_serialize_key(diagram, format)
        
        if cache_key in self._serialize_cache:
            logger.debug(f"Serialization cache hit for {cache_key}")
            return self._serialize_cache[cache_key]
        
        result = self.base_serializer.serialize_for_storage(diagram, format)
        
        # Cache with size limit
        if len(self._serialize_cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO for now)
            first_key = next(iter(self._serialize_cache))
            del self._serialize_cache[first_key]
        
        self._serialize_cache[cache_key] = result
        return result
    
    def deserialize_from_storage(self, content: str, format: str | None = None) -> "DomainDiagram":
        """Deserialize with caching."""
        cache_key = self._get_deserialize_key(content, format)
        
        if cache_key in self._deserialize_cache:
            logger.debug(f"Deserialization cache hit for {cache_key}")
            return self._deserialize_cache[cache_key]
        
        result = self.base_serializer.deserialize_from_storage(content, format)
        
        # Cache with size limit
        if len(self._deserialize_cache) >= self.cache_size:
            first_key = next(iter(self._deserialize_cache))
            del self._deserialize_cache[first_key]
        
        self._deserialize_cache[cache_key] = result
        return result