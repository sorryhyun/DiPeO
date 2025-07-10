"""Extended content type transformation strategies."""

from typing import Any, List, Dict
import json
import logging
import warnings

from dipeo.models import DomainArrow, NodeOutput
from dipeo.utils.template import TemplateProcessor

log = logging.getLogger(__name__)


class JsonTransformationStrategy:
    """Strategy for JSON transformation and formatting."""
    
    def transform(
        self,
        value: Any,
        arrow: DomainArrow,
        source_output: NodeOutput,
        target_node_type: str,
    ) -> Any:
        """Transform value to/from JSON format."""
        arrow_data = arrow.data or {}
        
        # Check if we should parse or stringify
        if arrow_data.get("parse_json", False):
            # Parse JSON string to object
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    log.warning(f"Failed to parse JSON for arrow {arrow.id}")
                    return value
        elif arrow_data.get("stringify_json", False):
            # Convert object to JSON string
            try:
                return json.dumps(value, indent=arrow_data.get("json_indent", 2))
            except TypeError:
                log.warning(f"Failed to stringify JSON for arrow {arrow.id}")
                return str(value)
        
        return value


class TemplateTransformationStrategy:
    """Strategy for template-based transformations."""
    
    def __init__(self):
        """Initialize with new TemplateProcessor."""
        self._processor = TemplateProcessor()
    
    def transform(
        self,
        value: Any,
        arrow: DomainArrow,
        source_output: NodeOutput,
        target_node_type: str,
    ) -> Any:
        """Apply template transformation."""
        arrow_data = arrow.data or {}
        template = arrow_data.get("template")
        
        if not template:
            return value
        
        # Prepare template context
        context = {
            "value": value,
            "source_node_id": source_output.node_id,
            "arrow_label": arrow.label,
            "metadata": source_output.metadata or {},
        }
        
        # Use new processor with single brace support for arrow transformations
        try:
            # First try with double brace syntax
            if "{{" in template:
                result = self._processor.process_simple(template, context)
            else:
                # Use single brace support for backward compatibility
                result = self._processor._process_single_brace_variables(template, context)
            return result
        except Exception as e:
            log.warning(f"Template transformation failed for arrow {arrow.id}: {e}")
            return value


class AggregationStrategy:
    """Strategy for aggregating multiple values."""
    
    def transform(
        self,
        value: Any,
        arrow: DomainArrow,
        source_output: NodeOutput,
        target_node_type: str,
    ) -> Any:
        """Aggregate values based on arrow configuration."""
        arrow_data = arrow.data or {}
        aggregation_type = arrow_data.get("aggregation", "list")
        
        # Ensure value is a list
        if not isinstance(value, list):
            value = [value]
        
        if aggregation_type == "concat":
            # Concatenate strings
            return " ".join(str(v) for v in value)
        elif aggregation_type == "sum":
            # Sum numeric values
            try:
                return sum(float(v) for v in value if isinstance(v, (int, float, str)))
            except (ValueError, TypeError):
                return value
        elif aggregation_type == "count":
            # Count items
            return len(value)
        elif aggregation_type == "first":
            # First item
            return value[0] if value else None
        elif aggregation_type == "last":
            # Last item
            return value[-1] if value else None
        
        # Default: return as list
        return value


class FilterTransformationStrategy:
    """Strategy for filtering data based on conditions."""
    
    def transform(
        self,
        value: Any,
        arrow: DomainArrow,
        source_output: NodeOutput,
        target_node_type: str,
    ) -> Any:
        """Filter data based on arrow configuration."""
        arrow_data = arrow.data or {}
        filter_config = arrow_data.get("filter", {})
        
        if not filter_config:
            return value
        
        # Handle different value types
        if isinstance(value, list):
            return self._filter_list(value, filter_config)
        elif isinstance(value, dict):
            return self._filter_dict(value, filter_config)
        else:
            # For scalar values, check if they pass the filter
            return value if self._check_condition(value, filter_config) else None
    
    def _filter_list(self, items: List[Any], filter_config: Dict[str, Any]) -> List[Any]:
        """Filter list items."""
        filtered = []
        
        for item in items:
            if self._check_condition(item, filter_config):
                filtered.append(item)
        
        return filtered
    
    def _filter_dict(self, data: Dict[str, Any], filter_config: Dict[str, Any]) -> Dict[str, Any]:
        """Filter dictionary keys."""
        include_keys = filter_config.get("include_keys", [])
        exclude_keys = filter_config.get("exclude_keys", [])
        
        if include_keys:
            return {k: v for k, v in data.items() if k in include_keys}
        elif exclude_keys:
            return {k: v for k, v in data.items() if k not in exclude_keys}
        
        return data
    
    def _check_condition(self, value: Any, filter_config: Dict[str, Any]) -> bool:
        """Check if value meets filter condition."""
        condition_type = filter_config.get("type", "equals")
        condition_value = filter_config.get("value")
        
        if condition_type == "equals":
            return value == condition_value
        elif condition_type == "not_equals":
            return value != condition_value
        elif condition_type == "contains":
            return condition_value in str(value)
        elif condition_type == "greater_than":
            try:
                return float(value) > float(condition_value)
            except (ValueError, TypeError):
                return False
        elif condition_type == "less_than":
            try:
                return float(value) < float(condition_value)
            except (ValueError, TypeError):
                return False
        
        return True


class ErrorHandlingStrategy:
    """Strategy for handling errors in data transformation."""
    
    def transform(
        self,
        value: Any,
        arrow: DomainArrow,
        source_output: NodeOutput,
        target_node_type: str,
    ) -> Any:
        """Handle error values with fallback options."""
        arrow_data = arrow.data or {}
        
        # Check if this is an error output
        is_error = (
            isinstance(source_output.metadata, dict) and 
            source_output.metadata.get("error", False)
        )
        
        if is_error:
            # Apply error handling
            error_handling = arrow_data.get("on_error", "pass_through")
            
            if error_handling == "default_value":
                return arrow_data.get("default_value", "")
            elif error_handling == "skip":
                return None
            elif error_handling == "transform":
                # Transform error to specific format
                return {
                    "error": True,
                    "message": str(value),
                    "source": source_output.node_id,
                }
        
        return value