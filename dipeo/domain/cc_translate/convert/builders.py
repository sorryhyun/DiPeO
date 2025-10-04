"""Builder interfaces and factory for node and connection creation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Protocol

from dipeo.domain.cc_translate.models.event import DomainEvent


class NodeType(Enum):
    """Supported node types for diagram building."""

    START = "start"
    USER = "person_job"  # User input node
    ASSISTANT = "person_job"  # AI assistant node
    READ_FILE = "db"  # File read operation
    WRITE_FILE = "db"  # File write operation
    EDIT_FILE = "diff_patch"  # File edit/patch operation
    BASH = "code_job"  # Bash command execution
    TODO = "db"  # TODO list update
    SEARCH = "code_job"  # Search operations
    API_CALL = "api_job"  # Generic API calls


@dataclass
class NodeCreationContext:
    """Context for node creation with validation and metadata."""

    node_type: NodeType
    label: str
    position: dict[str, int]
    props: dict[str, Any]
    metadata: dict[str, Any]
    validation_errors: list[str]

    def is_valid(self) -> bool:
        """Check if the node creation context is valid."""
        return len(self.validation_errors) == 0


class BaseNodeBuilder(ABC):
    """Abstract base class for node builders."""

    @abstractmethod
    def reset(self) -> None:
        """Reset the builder state."""
        pass

    @abstractmethod
    def increment_counter(self) -> int:
        """Increment and return the node counter."""
        pass

    @abstractmethod
    def get_position(self) -> dict[str, int]:
        """Calculate node position based on current state."""
        pass

    @abstractmethod
    def create_node(
        self,
        node_type: NodeType,
        label: str,
        props: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Create a node of the specified type.

        Args:
            node_type: The type of node to create
            label: The label for the node
            props: Node properties
            metadata: Optional metadata for the node

        Returns:
            The created node or None if creation failed
        """
        pass

    @abstractmethod
    def validate_node(self, node: dict[str, Any]) -> list[str]:
        """
        Validate a node structure.

        Args:
            node: The node to validate

        Returns:
            List of validation errors (empty if valid)
        """
        pass


class EventNodeBuilder(Protocol):
    """Protocol for building nodes from domain events."""

    def create_start_node(self, session_id: str, initial_prompt: str) -> dict[str, Any]:
        """Create the start node for the diagram."""
        ...

    def create_user_node(self, content: str) -> dict[str, Any] | None:
        """Create a node for user input."""
        ...

    def create_assistant_node(
        self, content: str, system_messages: list[str] | None = None
    ) -> dict[str, Any]:
        """Create a node for AI assistant response."""
        ...

    def create_tool_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_use_result: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create appropriate node based on tool name."""
        ...

    def get_nodes(self) -> list[dict[str, Any]]:
        """Get all created nodes."""
        ...

    def get_persons(self) -> dict[str, dict[str, Any]]:
        """Get all registered persons."""
        ...


class BaseConnectionBuilder(ABC):
    """Abstract base class for connection builders."""

    @abstractmethod
    def reset(self) -> None:
        """Reset the builder state."""
        pass

    @abstractmethod
    def create_connection(
        self, source_id: str, target_id: str, props: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Create a connection between two nodes.

        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            props: Optional connection properties

        Returns:
            The created connection
        """
        pass

    @abstractmethod
    def validate_connection(self, source_type: str, target_type: str) -> list[str]:
        """
        Validate that a connection between two node types is allowed.

        Args:
            source_type: Type of the source node
            target_type: Type of the target node

        Returns:
            List of validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def get_connections(self) -> list[dict[str, Any]]:
        """Get all created connections."""
        pass


class NodeBuilderValidator:
    """Validator for node creation."""

    REQUIRED_NODE_FIELDS = ["type", "label", "position"]
    REQUIRED_POSITION_FIELDS = ["x", "y"]

    def validate_node_structure(self, node: dict[str, Any]) -> list[str]:
        """
        Validate the basic structure of a node.

        Args:
            node: The node to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_NODE_FIELDS:
            if field not in node:
                errors.append(f"Missing required field: {field}")

        # Validate position structure
        if "position" in node:
            position = node["position"]
            if not isinstance(position, dict):
                errors.append("Position must be a dictionary")
            else:
                for field in self.REQUIRED_POSITION_FIELDS:
                    if field not in position:
                        errors.append(f"Missing position field: {field}")
                    elif not isinstance(position[field], int | float):
                        errors.append(f"Position {field} must be numeric")

        # Validate type
        if "type" in node and not isinstance(node["type"], str):
            errors.append("Node type must be a string")

        # Validate label
        if "label" in node and not isinstance(node["label"], str):
            errors.append("Node label must be a string")

        # Validate props if present
        if "props" in node and not isinstance(node["props"], dict):
            errors.append("Node props must be a dictionary")

        return errors

    def validate_node_type_specific(self, node_type: NodeType, props: dict[str, Any]) -> list[str]:
        """
        Validate node properties based on node type.

        Args:
            node_type: The type of node
            props: The node properties

        Returns:
            List of validation errors
        """
        errors = []

        if node_type == NodeType.START:
            if "trigger_mode" not in props:
                errors.append("Start node requires trigger_mode property")

        elif node_type in [NodeType.USER, NodeType.ASSISTANT]:
            if "person" not in props:
                errors.append(f"{node_type.name} node requires person property")
            if "max_iteration" not in props:
                errors.append(f"{node_type.name} node requires max_iteration property")

        elif node_type in [NodeType.READ_FILE, NodeType.WRITE_FILE]:
            if "operation" not in props:
                errors.append(f"{node_type.name} node requires operation property")
            if "sub_type" not in props:
                errors.append(f"{node_type.name} node requires sub_type property")

        elif node_type == NodeType.EDIT_FILE:
            if "target_path" not in props:
                errors.append("Edit file node requires target_path property")
            if "diff" not in props:
                errors.append("Edit file node requires diff property")

        elif node_type == NodeType.BASH:
            if "language" not in props:
                errors.append("Bash node requires language property")
            if "code" not in props:
                errors.append("Bash node requires code property")

        elif node_type == NodeType.API_CALL:
            if "endpoint" not in props:
                errors.append("API call node requires endpoint property")
            if "method" not in props:
                errors.append("API call node requires method property")

        return errors


class ConnectionBuilderValidator:
    """Validator for connection creation."""

    # Define allowed connections between node types
    ALLOWED_CONNECTIONS = {
        "start": ["person_job", "db", "code_job", "api_job", "diff_patch"],
        "person_job": ["person_job", "db", "code_job", "api_job", "diff_patch"],
        "db": ["person_job", "db", "code_job", "api_job", "diff_patch"],
        "code_job": ["person_job", "db", "code_job", "api_job", "diff_patch"],
        "api_job": ["person_job", "db", "code_job", "api_job", "diff_patch"],
        "diff_patch": ["person_job", "db", "code_job", "api_job", "diff_patch"],
    }

    def validate_connection_structure(self, connection: dict[str, Any]) -> list[str]:
        """
        Validate the basic structure of a connection.

        Args:
            connection: The connection to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Check required fields
        if "source" not in connection:
            errors.append("Missing required field: source")
        if "target" not in connection:
            errors.append("Missing required field: target")

        # Validate source and target are strings
        if "source" in connection and not isinstance(connection["source"], str):
            errors.append("Connection source must be a string")
        if "target" in connection and not isinstance(connection["target"], str):
            errors.append("Connection target must be a string")

        return errors

    def validate_connection_types(self, source_type: str, target_type: str) -> list[str]:
        """
        Validate that a connection between two node types is allowed.

        Args:
            source_type: Type of the source node
            target_type: Type of the target node

        Returns:
            List of validation errors
        """
        errors = []

        if source_type not in self.ALLOWED_CONNECTIONS:
            errors.append(f"Unknown source node type: {source_type}")
        elif target_type not in self.ALLOWED_CONNECTIONS.get(source_type, []):
            errors.append(f"Connection not allowed from {source_type} to {target_type}")

        return errors


class NodeFactory:
    """Factory for creating nodes based on type."""

    def __init__(self, builder: EventNodeBuilder):
        """
        Initialize the factory with a builder.

        Args:
            builder: The node builder to use
        """
        self.builder = builder
        self.validator = NodeBuilderValidator()

    def create_node_from_event(self, event: DomainEvent) -> dict[str, Any] | None:
        """
        Create a node from a domain event.

        Args:
            event: The domain event to process

        Returns:
            The created node or None if not applicable
        """
        if event.type == "user_message":
            return self.builder.create_user_node(event.data.get("content", ""))

        elif event.type == "assistant_message":
            return self.builder.create_assistant_node(
                event.data.get("content", ""),
                event.data.get("system_messages"),
            )

        elif event.type == "tool_use":
            return self.builder.create_tool_node(
                event.data.get("tool_name", ""),
                event.data.get("tool_input", {}),
                event.data.get("tool_use_result"),
            )

        return None

    def validate_and_create(
        self,
        node_type: NodeType,
        label: str,
        props: dict[str, Any],
        position: dict[str, int] | None = None,
    ) -> NodeCreationContext:
        """
        Validate and create a node with full context.

        Args:
            node_type: The type of node to create
            label: The node label
            props: Node properties
            position: Optional position override

        Returns:
            NodeCreationContext with the result and any errors
        """
        errors = []

        # Validate type-specific requirements
        errors.extend(self.validator.validate_node_type_specific(node_type, props))

        # Create context
        context = NodeCreationContext(
            node_type=node_type,
            label=label,
            position=position or self.builder.get_position(),
            props=props,
            metadata={},
            validation_errors=errors,
        )

        return context
