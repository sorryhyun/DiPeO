# Domain service for generalized memory transformation across node types

from typing import Dict, Any, List, Optional, Protocol
import logging

from dipeo.models import ForgettingMode

log = logging.getLogger(__name__)


class MemoryStrategy(Protocol):
    # Protocol for memory transformation strategies
    
    def apply(
        self,
        data: Any,
        execution_count: int,
        memory_config: Dict[str, Any],
    ) -> Any:
        # Apply memory transformation to data
        ...


class MemoryTransformer:
    # Service for applying memory transformations to node inputs
    
    def __init__(self):
        self._strategies: Dict[ForgettingMode, MemoryStrategy] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        self._strategies[ForgettingMode.no_forget] = NoForgetStrategy()
        self._strategies[ForgettingMode.on_every_turn] = OnEveryTurnStrategy()
        self._strategies[ForgettingMode.upon_request] = UponRequestStrategy()
    
    def register_strategy(self, mode: ForgettingMode, strategy: MemoryStrategy):
        self._strategies[mode] = strategy
    
    def transform_input(
        self,
        input_data: Dict[str, Any],
        node_type: str,
        execution_count: int,
        memory_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Transform input data based on memory configuration
        if not memory_config:
            return input_data
        
        forget_mode = ForgettingMode(memory_config.get("forget_mode", "no_forget"))
        
        # Check if we should apply forgetting
        if not self._should_apply_forgetting(forget_mode, execution_count):
            return input_data
        
        log.debug(f"Applying {forget_mode.value} memory transformation for {node_type} (exec #{execution_count})")
        
        # Apply transformation to each input that has memory hints
        transformed_inputs = {}
        
        for key, value in input_data.items():
            if isinstance(value, dict) and value.get("memory_hints", {}).get("should_apply"):
                # This input came through an arrow and needs memory transformation
                actual_value = value.get("value")
                
                if forget_mode in self._strategies:
                    transformed_value = self._strategies[forget_mode].apply(
                        actual_value, execution_count, memory_config
                    )
                    
                    # Preserve arrow metadata but update the value
                    transformed_inputs[key] = {
                        **value,
                        "value": transformed_value,
                        "memory_applied": True,
                    }
                else:
                    transformed_inputs[key] = value
            else:
                # No memory transformation needed
                transformed_inputs[key] = value
        
        return transformed_inputs
    
    def _should_apply_forgetting(
        self,
        forget_mode: ForgettingMode,
        execution_count: int,
    ) -> bool:
        if forget_mode == ForgettingMode.no_forget:
            return False
        elif forget_mode == ForgettingMode.on_every_turn:
            return execution_count > 0
        elif forget_mode == ForgettingMode.upon_request:
            # This would be triggered by explicit request
            return False
        return False
    
    def extract_clean_value(self, wrapped_value: Any) -> Any:
        if isinstance(wrapped_value, dict) and "value" in wrapped_value:
            return wrapped_value["value"]
        return wrapped_value


class NoForgetStrategy:
    # Strategy for no forgetting - pass through unchanged
    
    def apply(
        self,
        data: Any,
        execution_count: int,
        memory_config: Dict[str, Any],
    ) -> Any:
        return data


class OnEveryTurnStrategy:
    # Strategy for forgetting on every turn
    
    def apply(
        self,
        data: Any,
        execution_count: int,
        memory_config: Dict[str, Any],
    ) -> Any:
        # For conversation data, keep only the last message
        if isinstance(data, dict) and "messages" in data:
            messages = data["messages"]
            if isinstance(messages, list) and messages:
                # Keep system messages and the last user message
                system_messages = [
                    msg for msg in messages 
                    if isinstance(msg, dict) and msg.get("role") == "system"
                ]
                user_messages = [
                    msg for msg in messages 
                    if isinstance(msg, dict) and msg.get("role") == "user"
                ]
                
                if user_messages:
                    return {
                        **data,
                        "messages": system_messages + [user_messages[-1]]
                    }
        
        # For other data types, return as is
        return data


class UponRequestStrategy:
    # Strategy for forgetting upon request
    
    def apply(
        self,
        data: Any,
        execution_count: int,
        memory_config: Dict[str, Any],
    ) -> Any:
        # Check if there's an explicit forget request
        if memory_config.get("forget_requested", False):
            # For conversation data, clear history
            if isinstance(data, dict) and "messages" in data:
                return {**data, "messages": []}
            # For other data, return empty
            return None
        
        # No forget requested, return as is
        return data


def unwrap_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    # Utility to unwrap processed inputs for node handlers
    clean_inputs = {}
    
    for key, value in inputs.items():
        if isinstance(value, dict) and "value" in value and "arrow_metadata" in value:
            # This is a wrapped input from arrow processing
            clean_inputs[key] = value["value"]
        else:
            # Regular input
            clean_inputs[key] = value
    
    return clean_inputs