"""Infrastructure adapter for diagram compilation.

This adapter wraps the existing StandardCompiler and InterfaceBasedDiagramCompiler
to implement the domain DiagramCompiler port.
"""

import logging
from typing import TYPE_CHECKING

from dipeo.domain.diagram.ports import DiagramCompiler

if TYPE_CHECKING:
    from dipeo.diagram_generated import DomainDiagram
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram

logger = logging.getLogger(__name__)


class StandardCompilerAdapter(DiagramCompiler):
    """Adapter that wraps the existing StandardCompiler implementation.
    
    This adapter allows the existing compiler implementations to work
    with the new domain port interface.
    """
    
    def __init__(self, use_interface_based: bool = True):
        """Initialize the compiler adapter.
        
        Args:
            use_interface_based: If True, use InterfaceBasedDiagramCompiler,
                               otherwise use the legacy StandardCompiler
        """
        self.use_interface_based = use_interface_based
        self._compiler = None
        self._initialize_compiler()
    
    def _initialize_compiler(self):
        """Initialize the underlying compiler implementation."""
        # Use the domain compiler directly since the application-level
        # compilers don't exist yet
        from dipeo.domain.diagram.compilation import DomainDiagramCompiler
        
        self._compiler = DomainDiagramCompiler()

    def compile(self, domain_diagram: "DomainDiagram") -> "ExecutableDiagram":
        """Compile domain diagram to executable form.
        
        Args:
            domain_diagram: The diagram to compile
            
        Returns:
            ExecutableDiagram ready for execution
        """
        if not self._compiler:
            raise RuntimeError("Compiler not initialized")
        
        result = self._compiler.compile(domain_diagram)
        return result


class CachingCompilerAdapter(DiagramCompiler):
    """Decorator adapter that adds caching to any DiagramCompiler.
    
    This adapter caches compilation results to avoid recompiling
    the same diagrams multiple times.
    """
    
    def __init__(self, base_compiler: DiagramCompiler, cache_size: int = 100):
        """Initialize the caching adapter.
        
        Args:
            base_compiler: The underlying compiler to wrap
            cache_size: Maximum number of cached compilations
        """
        self.base_compiler = base_compiler
        self.cache_size = cache_size
        self._cache: dict[str, "ExecutableDiagram"] = {}
        self._access_order: list[str] = []
    
    def _get_cache_key(self, domain_diagram: "DomainDiagram") -> str:
        """Generate a cache key for a diagram.
        
        Uses diagram ID and a hash of its structure.
        """
        # Get ID from metadata if available, otherwise use a hash
        diagram_id = domain_diagram.metadata.id if domain_diagram.metadata and hasattr(domain_diagram.metadata, 'id') else "no_id"
        # Simple key based on diagram ID and node count
        # In production, would use a proper hash of the diagram structure
        return f"{diagram_id}_{len(domain_diagram.nodes)}_{len(domain_diagram.arrows)}"
    
    def compile(self, domain_diagram: "DomainDiagram") -> "ExecutableDiagram":
        """Compile with caching.
        
        Args:
            domain_diagram: The diagram to compile
            
        Returns:
            Cached or newly compiled ExecutableDiagram
        """
        cache_key = self._get_cache_key(domain_diagram)
        
        # Check cache
        if cache_key in self._cache:
            diagram_id = domain_diagram.metadata.id if domain_diagram.metadata and hasattr(domain_diagram.metadata, 'id') else "unknown"
            # Update access order for LRU
            self._access_order.remove(cache_key)
            self._access_order.append(cache_key)
            return self._cache[cache_key]
        
        # Compile and cache
        diagram_id = domain_diagram.metadata.id if domain_diagram.metadata and hasattr(domain_diagram.metadata, 'id') else "unknown"
        result = self.base_compiler.compile(domain_diagram)
        
        # Add to cache with LRU eviction
        self._cache[cache_key] = result
        self._access_order.append(cache_key)
        
        # Evict oldest if cache is full
        if len(self._cache) > self.cache_size:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]

        return result


class ValidatingCompilerAdapter(DiagramCompiler):
    """Decorator adapter that adds validation before compilation.
    
    This adapter ensures diagrams are valid before attempting compilation.
    """
    
    def __init__(self, base_compiler: DiagramCompiler):
        """Initialize the validating adapter.
        
        Args:
            base_compiler: The underlying compiler to wrap
        """
        self.base_compiler = base_compiler
    
    def _validate_diagram(self, domain_diagram: "DomainDiagram") -> None:
        """Validate a diagram before compilation.
        
        Raises:
            ValueError: If the diagram is invalid
        """
        # Basic validation
        if not domain_diagram.nodes:
            raise ValueError("Cannot compile empty diagram")
        
        # Check for duplicate node IDs
        node_ids = [node.id for node in domain_diagram.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Diagram contains duplicate node IDs")
        
        # Validate arrows reference existing nodes
        from dipeo.domain.diagram.utils import extract_node_id_from_handle
        
        node_id_set = set(node_ids)
        for arrow in domain_diagram.arrows:
            # Extract node IDs from handle IDs
            source_node_id = extract_node_id_from_handle(arrow.source)
            target_node_id = extract_node_id_from_handle(arrow.target)
            
            # If extraction failed, treat as direct node ID (for backward compatibility)
            if source_node_id is None:
                source_node_id = arrow.source
            if target_node_id is None:
                target_node_id = arrow.target
            
            if source_node_id not in node_id_set:
                raise ValueError(f"Arrow references non-existent source node: {source_node_id} (from handle: {arrow.source})")
            if target_node_id not in node_id_set:
                raise ValueError(f"Arrow references non-existent target node: {target_node_id} (from handle: {arrow.target})")

        # Get diagram identifier for logging
        diagram_id = "unknown"
        if domain_diagram.metadata:
            if hasattr(domain_diagram.metadata, 'id') and domain_diagram.metadata.id:
                diagram_id = domain_diagram.metadata.id
            elif hasattr(domain_diagram.metadata, 'name') and domain_diagram.metadata.name:
                diagram_id = domain_diagram.metadata.name

    def compile(self, domain_diagram: "DomainDiagram") -> "ExecutableDiagram":
        """Compile with validation.
        
        Args:
            domain_diagram: The diagram to compile
            
        Returns:
            ExecutableDiagram if validation passes
            
        Raises:
            ValueError: If validation fails
        """
        self._validate_diagram(domain_diagram)
        return self.base_compiler.compile(domain_diagram)