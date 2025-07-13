"""Rich domain entity for Node with business behavior."""

from typing import Any, Optional, Dict

from dipeo.core import ValidationError
from dipeo.models import (
    DomainNode,
    NodeType,
    NodeID,
    HandleID,
    HandleDirection,
    HandleLabel,
    DomainHandle,
)


class Node:
    """Rich domain entity for Node with business behavior."""
    
    def __init__(self, domain_node: DomainNode):
        """Initialize with a domain node model."""
        self._data = domain_node
    
    @property
    def id(self) -> NodeID:
        """Get node ID."""
        return self._data.id
    
    @property
    def type(self) -> NodeType:
        """Get node type."""
        return self._data.type
    
    @property
    def label(self) -> str:
        """Get node label."""
        return self._data.label or ""
    
    @property
    def position(self) -> Dict[str, float]:
        """Get node position."""
        if self._data.position:
            return {"x": self._data.position.x, "y": self._data.position.y}
        return {"x": 0, "y": 0}
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get node data."""
        return self._data.data or {}
    
    def get_data_value(self, key: str, default: Any = None) -> Any:
        """Get a value from node data."""
        return self.data.get(key, default)
    
    def set_data_value(self, key: str, value: Any) -> None:
        """Set a value in node data."""
        if self._data.data is None:
            self._data.data = {}
        self._data.data[key] = value
    
    def update_data(self, updates: Dict[str, Any]) -> None:
        """Update multiple data values."""
        if self._data.data is None:
            self._data.data = {}
        self._data.data.update(updates)
    
    def validate_required_fields(self) -> None:
        """Validate that node has all required fields for its type."""
        required_fields = self._get_required_fields()
        missing_fields = []
        
        for field in required_fields:
            if field not in self.data or self.data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(
                f"Node '{self.id}' of type '{self.type.value}' is missing required fields: {missing_fields}"
            )
    
    def _get_required_fields(self) -> list[str]:
        """Get required fields based on node type."""
        # Define required fields for each node type
        required_by_type = {
            NodeType.person_job: ["person_id", "prompt"],
            NodeType.code_job: ["code", "language"],
            NodeType.api_job: ["url", "method"],
            NodeType.condition: ["expression"],
            NodeType.db: ["db_name", "operation"],
            NodeType.user_response: ["question"],
            NodeType.notion: ["operation"],
            NodeType.person_batch_job: ["person_id", "batch_data"],
            NodeType.hook: ["hook_type", "config"],
        }
        
        return required_by_type.get(self.type, [])
    
    def get_handle_ids(self, direction: Optional[HandleDirection] = None) -> list[HandleID]:
        """Get handle IDs for this node, optionally filtered by direction."""
        handles = []
        
        # Standard handles based on node type
        if self.type == NodeType.start:
            handles.append(self._create_handle_id(HandleLabel.default, HandleDirection.output))
        elif self.type == NodeType.endpoint:
            handles.append(self._create_handle_id(HandleLabel.default, HandleDirection.input))
        elif self.type == NodeType.condition:
            handles.extend([
                self._create_handle_id(HandleLabel.default, HandleDirection.input),
                self._create_handle_id(HandleLabel.condtrue, HandleDirection.output),
                self._create_handle_id(HandleLabel.condfalse, HandleDirection.output),
            ])
        else:
            # Most nodes have default input and output
            handles.extend([
                self._create_handle_id(HandleLabel.default, HandleDirection.input),
                self._create_handle_id(HandleLabel.default, HandleDirection.output),
            ])
        
        # Filter by direction if specified
        if direction:
            handles = [h for h in handles if self._get_handle_direction(h) == direction]
        
        return handles
    
    def _create_handle_id(self, label: HandleLabel, direction: HandleDirection) -> HandleID:
        """Create a handle ID from label and direction."""
        return HandleID(f"{self.id}_{label.value}_{direction.value}")
    
    def _get_handle_direction(self, handle_id: HandleID) -> HandleDirection:
        """Extract direction from handle ID."""
        parts = handle_id.split("_")
        if len(parts) >= 3:
            try:
                return HandleDirection(parts[-1])
            except ValueError:
                pass
        return HandleDirection.input  # Default
    
    def is_executable(self) -> bool:
        """Check if node has all required data to be executed."""
        try:
            self.validate_required_fields()
            return True
        except ValidationError:
            return False
    
    def is_start_node(self) -> bool:
        """Check if this is a start node."""
        return self.type == NodeType.start
    
    def is_endpoint_node(self) -> bool:
        """Check if this is an endpoint node."""
        return self.type == NodeType.endpoint
    
    def is_condition_node(self) -> bool:
        """Check if this is a condition node."""
        return self.type == NodeType.condition
    
    def requires_person(self) -> bool:
        """Check if this node requires a person (LLM) configuration."""
        return self.type in [NodeType.person_job, NodeType.person_batch_job]
    
    def requires_api_key(self) -> bool:
        """Check if this node requires an API key."""
        api_requiring_types = [
            NodeType.person_job,
            NodeType.person_batch_job,
            NodeType.api_job,
            NodeType.notion,
        ]
        return self.type in api_requiring_types
    
    def get_memory_scope(self) -> Optional[str]:
        """Get the memory scope for this node if it has one."""
        return self.get_data_value("memory_scope")
    
    def get_person_id(self) -> Optional[str]:
        """Get the person ID if this is a person-related node."""
        if self.requires_person():
            return self.get_data_value("person_id")
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return self._data.model_dump(exclude_none=True)
    
    def clone(self) -> 'Node':
        """Create a deep copy of this node."""
        import copy
        cloned_data = copy.deepcopy(self._data)
        return Node(cloned_data)