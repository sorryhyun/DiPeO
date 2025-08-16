"""Resolution error types for runtime input resolution."""

from typing import Any, Optional
from dipeo.core.base.exceptions import DiPeOError


class ResolutionError(DiPeOError):
    """Base error for input resolution failures."""
    
    def __init__(
        self,
        message: str,
        node_id: Optional[str] = None,
        edge_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(message)
        self.node_id = node_id
        self.edge_id = edge_id
        self.details = details or {}


class InputResolutionError(ResolutionError):
    """Error resolving node inputs."""
    pass


class TransformationError(ResolutionError):
    """Error applying transformation rules."""
    
    def __init__(
        self,
        message: str,
        source_type: Optional[str] = None,
        target_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.source_type = source_type
        self.target_type = target_type
        if source_type:
            self.details["source_type"] = source_type
        if target_type:
            self.details["target_type"] = target_type


class DependencyNotReadyError(ResolutionError):
    """Error when required dependency is not ready."""
    
    def __init__(
        self,
        message: str,
        dependency_node_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.dependency_node_id = dependency_node_id
        if dependency_node_id:
            self.details["dependency_node_id"] = dependency_node_id


class SpreadCollisionError(TransformationError):
    """Error when spread operator causes key collision."""
    
    def __init__(
        self,
        conflicting_keys: list[str],
        node_id: Optional[str] = None,
        edge_id: Optional[str] = None
    ):
        message = f"Spread operation would overwrite existing keys: {conflicting_keys}"
        super().__init__(
            message,
            node_id=node_id,
            edge_id=edge_id
        )
        self.conflicting_keys = conflicting_keys
        self.details["conflicting_keys"] = conflicting_keys