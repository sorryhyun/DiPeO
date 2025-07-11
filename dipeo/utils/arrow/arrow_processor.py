# Domain service for arrow-based data processing and transformation

from typing import Dict, Any, Optional, Protocol
import logging

from dipeo.models import (
    DomainArrow,
    NodeOutput,
    ContentType,
    ForgettingMode,
    parse_handle_id,
)

log = logging.getLogger(__name__)


class TransformationStrategy(Protocol):
    # Protocol for content type transformation strategies
    
    def transform(
        self,
        value: Any,
        arrow: DomainArrow,
        source_output: NodeOutput,
        target_node_type: str,
    ) -> Any:
        # Transform value based on content type and arrow configuration
        ...


class ArrowProcessor:
    # Service for processing data flow through arrows with transformations
    
    def __init__(self):
        self._transformation_strategies: Dict[ContentType, TransformationStrategy] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        self._transformation_strategies[ContentType.raw_text] = RawTextStrategy()
        self._transformation_strategies[ContentType.conversation_state] = ConversationStateStrategy()
        self._transformation_strategies[ContentType.variable] = VariableStrategy()
    
    def register_strategy(self, content_type: ContentType, strategy: TransformationStrategy):
        self._transformation_strategies[content_type] = strategy
    
    def process_arrow_delivery(
        self,
        arrow: DomainArrow,
        source_output: NodeOutput,
        target_node_type: str,
        memory_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Process data delivery through an arrow with transformations
        # Parse handles to understand the connection
        source_node_id, source_handle, _ = parse_handle_id(arrow.source)
        target_node_id, target_handle, _ = parse_handle_id(arrow.target)
        
        # Extract value from source output
        value = self._extract_value_from_output(
            source_output, source_handle, arrow.label
        )
        
        if value is None:
            log.debug(f"No value found for arrow {arrow.id}")
            return {}
        
        # Apply content type transformation
        content_type = arrow.content_type or ContentType.raw_text
        if content_type in self._transformation_strategies:
            value = self._transformation_strategies[content_type].transform(
                value, arrow, source_output, target_node_type
            )

        # Prepare wrapped output with arrow metadata
        wrapped_output = {
            "value": value,
            "arrow_metadata": {
                "arrow_id": arrow.id,
                "content_type": content_type.value if content_type else "raw_text",
                "label": arrow.label,
                "source_handle": source_handle,
                "target_handle": target_handle,
            },
            "source_metadata": {
                "node_id": source_output.node_id,
                "executed_nodes": source_output.executed_nodes or [],
            }
        }
        
        # Add memory management hints if applicable
        if memory_config and "forget_mode" in memory_config:
            wrapped_output["memory_hints"] = {
                "forget_mode": memory_config["forget_mode"],
                "should_apply": True,
            }
        
        # Use arrow label as key, or target handle as fallback
        input_key = arrow.label or target_handle or "default"
        
        return {input_key: wrapped_output}
    
    def _extract_value_from_output(
        self,
        output: NodeOutput,
        source_handle: str,
        arrow_label: Optional[str],
    ) -> Any:
        # Extract the appropriate value from node output
        if not output or not output.value:
            return None
        
        value_dict = output.value
        if not isinstance(value_dict, dict):
            return value_dict
        
        # Priority: arrow label > source handle > "default"
        if arrow_label and arrow_label in value_dict:
            return value_dict[arrow_label]
        elif source_handle and source_handle in value_dict:
            return value_dict[source_handle]
        elif "default" in value_dict:
            return value_dict["default"]
        
        # If no specific key found, return the whole dict
        return value_dict


class RawTextStrategy:
    # Strategy for raw text content - minimal transformation
    
    def transform(
        self,
        value: Any,
        arrow: DomainArrow,
        source_output: NodeOutput,
        target_node_type: str,
    ) -> Any:
        # For raw text, we just ensure it's stringifiable
        if isinstance(value, (list, dict)):
            return value
        return str(value) if value is not None else ""


class ConversationStateStrategy:
    # Strategy for conversation state content
    
    def transform(
        self,
        value: Any,
        arrow: DomainArrow,
        source_output: NodeOutput,
        target_node_type: str,
    ) -> Any:
        # If it's already a conversation state, return as is
        if isinstance(value, dict) and "messages" in value:
            return value
        
        # If it's a list of messages, wrap it
        if isinstance(value, list):
            return {"messages": value}
        
        # Otherwise, create a new conversation with this value
        return {
            "messages": [
                {"role": "user", "content": str(value)}
            ]
        }


class VariableStrategy:
    # Strategy for variable references
    
    def transform(
        self,
        value: Any,
        arrow: DomainArrow,
        source_output: NodeOutput,
        target_node_type: str,
    ) -> Any:
        # For now, just pass through
        # In future, this could resolve variable references
        return value