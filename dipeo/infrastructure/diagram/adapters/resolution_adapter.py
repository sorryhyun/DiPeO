"""Infrastructure adapters for input resolution system.

These adapters wrap the existing resolution implementations to work with
the new domain ports.
"""

import logging
from typing import Any, TYPE_CHECKING

from dipeo.domain.diagram.resolution.interfaces import (
    CompileTimeResolver,
    RuntimeInputResolver,
    TransformationEngine,
    Connection,
    TransformRules,
)

if TYPE_CHECKING:
    from dipeo.diagram_generated import DomainArrow, DomainNode, NodeID
    from dipeo.diagram_generated.enums import NodeType

logger = logging.getLogger(__name__)


class StandardCompileTimeResolverAdapter(CompileTimeResolver):
    """Adapter for the standard compile-time resolver.
    
    NOTE: This adapter appears to have been incorrectly using StandardRuntimeResolver
    for compile-time resolution. This needs architectural review.
    """
    
    def __init__(self):
        """Initialize the adapter."""
        # This adapter was incorrectly using runtime resolver for compile-time
        # Needs architectural review
        pass

    def resolve_connections(
        self,
        arrows: list["DomainArrow"],
        nodes: list["DomainNode"]
    ) -> list[Connection]:
        """Resolve arrows to concrete connections between nodes.
        
        Args:
            arrows: List of domain arrows
            nodes: List of domain nodes
            
        Returns:
            List of resolved connections
        """
        # This adapter was incorrectly using runtime resolver for compile-time
        # Needs proper implementation or removal
        raise NotImplementedError(
            "StandardCompileTimeResolverAdapter needs proper implementation - "
            "was incorrectly using runtime resolver for compile-time resolution"
        )
    
    def determine_transformation_rules(
        self,
        connection: Connection,
        source_node_type: "NodeType",
        target_node_type: "NodeType",
        nodes_by_id: dict["NodeID", "DomainNode"]
    ) -> TransformRules:
        """Determine transformation rules for a connection.
        
        Args:
            connection: The resolved connection
            source_node_type: Type of source node
            target_node_type: Type of target node
            nodes_by_id: Mapping of node IDs to nodes
            
        Returns:
            Transformation rules to apply
        """
        # This adapter was incorrectly using runtime resolver for compile-time
        # Needs proper implementation or removal
        raise NotImplementedError(
            "StandardCompileTimeResolverAdapter needs proper implementation - "
            "was incorrectly using runtime resolver for compile-time resolution"
        )


class StandardRuntimeResolverAdapter(RuntimeInputResolver):
    """Adapter for the standard runtime input resolver.
    
    Now directly uses domain resolution instead of wrapping StandardRuntimeResolver.
    """
    
    def __init__(self):
        """Initialize the adapter."""
        # No longer need to create a resolver - we'll use domain resolution directly
        pass

    async def resolve_input_value(
        self,
        target_node_id: "NodeID",
        target_input: str,
        node_outputs: dict["NodeID", Any],
        transformation_rules: TransformRules | None = None
    ) -> Any:
        """Resolve the actual value for a node's input at runtime.
        
        NOTE: This adapter method signature doesn't match how domain resolution works.
        Domain resolution resolves ALL inputs for a node at once, not individual inputs.
        This adapter would need significant refactoring to work properly.
        
        Args:
            target_node_id: ID of the target node
            target_input: Name of the input to resolve
            node_outputs: Outputs from executed nodes
            transformation_rules: Optional transformation rules
            
        Returns:
            The resolved input value
        """
        # This interface doesn't match domain resolution which resolves all inputs at once
        # For now, we'll raise NotImplementedError to indicate this needs architectural changes
        raise NotImplementedError(
            "StandardRuntimeResolverAdapter needs refactoring - domain resolution "
            "resolves all inputs at once, not individual inputs"
        )


class StandardTransformationEngineAdapter(TransformationEngine):
    """Adapter for the standard transformation engine.
    
    Wraps the existing transformation engine to implement
    the domain TransformationEngine interface.
    """
    
    def __init__(self):
        """Initialize the adapter."""
        self._engine = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the underlying engine."""
        from dipeo.domain.diagram.resolution.transformation_engine import (
            StandardTransformationEngine
        )
        self._engine = StandardTransformationEngine()

    def transform(
        self,
        value: Any,
        rules: TransformRules,
        source_content_type: str | None = None,
        target_content_type: str | None = None
    ) -> Any:
        """Apply transformation rules to a value.
        
        Args:
            value: The value to transform
            rules: Transformation rules to apply
            source_content_type: Optional source content type
            target_content_type: Optional target content type
            
        Returns:
            The transformed value
        """
        if not self._engine:
            raise RuntimeError("Engine not initialized")
        
        return self._engine.transform(
            value, rules, source_content_type, target_content_type
        )


class CompositeResolverAdapter(CompileTimeResolver):
    """Composite resolver that tries multiple resolvers in sequence.
    
    This allows fallback behavior and gradual migration between
    different resolver implementations.
    """
    
    def __init__(self, resolvers: list[CompileTimeResolver]):
        """Initialize with a list of resolvers to try.
        
        Args:
            resolvers: List of resolvers to try in order
        """
        if not resolvers:
            raise ValueError("At least one resolver required")
        self.resolvers = resolvers

    def resolve_connections(
        self,
        arrows: list["DomainArrow"],
        nodes: list["DomainNode"]
    ) -> list[Connection]:
        """Try each resolver until one succeeds.
        
        Args:
            arrows: List of domain arrows
            nodes: List of domain nodes
            
        Returns:
            List of resolved connections from the first successful resolver
        """
        last_error = None
        for i, resolver in enumerate(self.resolvers):
            try:
                return resolver.resolve_connections(arrows, nodes)
            except Exception as e:
                logger.warning(f"Resolver {i+1} failed: {e}")
                last_error = e
        
        # All resolvers failed
        raise RuntimeError(f"All resolvers failed. Last error: {last_error}")
    
    def determine_transformation_rules(
        self,
        connection: Connection,
        source_node_type: "NodeType",
        target_node_type: "NodeType",
        nodes_by_id: dict["NodeID", "DomainNode"]
    ) -> TransformRules:
        """Try each resolver for transformation rules.
        
        Merges rules from all successful resolvers.
        
        Args:
            connection: The resolved connection
            source_node_type: Type of source node
            target_node_type: Type of target node
            nodes_by_id: Mapping of node IDs to nodes
            
        Returns:
            Merged transformation rules from all resolvers
        """
        merged_rules = TransformRules()
        
        for resolver in self.resolvers:
            try:
                rules = resolver.determine_transformation_rules(
                    connection, source_node_type, target_node_type, nodes_by_id
                )
                merged_rules = merged_rules.merge_with(rules)
            except Exception as e:
                logger.debug(f"Resolver failed for transformation rules: {e}")
        
        return merged_rules


class CachingRuntimeResolverAdapter(RuntimeInputResolver):
    """Decorator that adds caching to runtime resolution.
    
    This can help avoid redundant resolution of the same inputs.
    """
    
    def __init__(self, base_resolver: RuntimeInputResolver):
        """Initialize with a base resolver to wrap.
        
        Args:
            base_resolver: The resolver to add caching to
        """
        self.base_resolver = base_resolver
        self._cache: dict[str, Any] = {}
    
    def _get_cache_key(
        self,
        target_node_id: "NodeID",
        target_input: str,
        node_outputs_hash: str
    ) -> str:
        """Generate a cache key for resolution."""
        return f"{target_node_id}:{target_input}:{node_outputs_hash}"
    
    def _hash_outputs(self, node_outputs: dict["NodeID", Any]) -> str:
        """Generate a hash of node outputs for cache key."""
        # Simple hash based on output keys
        # In production would need more sophisticated hashing
        return str(hash(tuple(sorted(node_outputs.keys()))))
    
    async def resolve_input_value(
        self,
        target_node_id: "NodeID",
        target_input: str,
        node_outputs: dict["NodeID", Any],
        transformation_rules: TransformRules | None = None
    ) -> Any:
        """Resolve with caching.
        
        Args:
            target_node_id: ID of the target node
            target_input: Name of the input to resolve
            node_outputs: Outputs from executed nodes
            transformation_rules: Optional transformation rules
            
        Returns:
            Cached or newly resolved input value
        """
        outputs_hash = self._hash_outputs(node_outputs)
        cache_key = self._get_cache_key(target_node_id, target_input, outputs_hash)
        
        if cache_key in self._cache:
            logger.debug(f"Cache hit for input resolution: {cache_key}")
            return self._cache[cache_key]
        
        result = await self.base_resolver.resolve_input_value(
            target_node_id, target_input, node_outputs, transformation_rules
        )
        
        self._cache[cache_key] = result
        return result