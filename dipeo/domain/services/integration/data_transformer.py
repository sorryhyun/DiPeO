"""Data transformation for integrations.

This module provides backward compatibility by delegating to the utils library.
All pure data transformation functions have been moved to dipeo.utils.transform.
"""

from typing import Any

from dipeo.utils.transform import (
    apply_transformation_chain as _apply_transformation_chain,
)
from dipeo.utils.transform import (
    transform_from_format as _transform_from_format,
)
from dipeo.utils.transform import (
    transform_to_format as _transform_to_format,
)


class DataTransformer:
    """Transforms data between different formats for integrations.
    
    This class now delegates to pure functions in dipeo.utils.transform
    for better separation of concerns and testability.
    """
    
    @staticmethod
    def transform_to_format(
        data: Any,
        format: str,
        options: dict[str, Any] | None = None
    ) -> str | bytes | dict[str, Any]:
        """Transform data to specified format.
        
        Delegates to dipeo.utils.transform.transform_to_format
        """
        return _transform_to_format(data, format, options)
    
    @staticmethod
    def transform_from_format(
        data: str | bytes,
        format: str,
        options: dict[str, Any] | None = None
    ) -> Any:
        """Transform data from specified format.
        
        Delegates to dipeo.utils.transform.transform_from_format
        """
        return _transform_from_format(data, format, options)
    
    @staticmethod
    def apply_transformation_chain(
        data: Any,
        transformations: list[dict[str, Any]]
    ) -> Any:
        """Apply a chain of transformations to data.
        
        Delegates to dipeo.utils.transform.apply_transformation_chain
        """
        return _apply_transformation_chain(data, transformations)