"""Data transformation for integrations.

This module provides backward compatibility by delegating to the utils library.
All pure data transformation functions have been moved to dipeo.utils.transform.
"""

from typing import Dict, Any, List, Optional, Union
from dipeo.utils.transform import (
    transform_to_format as _transform_to_format,
    transform_from_format as _transform_from_format,
    apply_transformation_chain as _apply_transformation_chain,
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
        options: Optional[Dict[str, Any]] = None
    ) -> Union[str, bytes, Dict[str, Any]]:
        """Transform data to specified format.
        
        Delegates to dipeo.utils.transform.transform_to_format
        """
        return _transform_to_format(data, format, options)
    
    @staticmethod
    def transform_from_format(
        data: Union[str, bytes],
        format: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Transform data from specified format.
        
        Delegates to dipeo.utils.transform.transform_from_format
        """
        return _transform_from_format(data, format, options)
    
    @staticmethod
    def apply_transformation_chain(
        data: Any,
        transformations: List[Dict[str, Any]]
    ) -> Any:
        """Apply a chain of transformations to data.
        
        Delegates to dipeo.utils.transform.apply_transformation_chain
        """
        return _apply_transformation_chain(data, transformations)