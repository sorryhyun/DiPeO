"""Node Type Registry for runtime validation and input type resolution.

This registry provides essential runtime validation that cannot be enforced by Python's
type system or GraphQL schemas. It serves as a centralized authority for:

1. **Business Rule Validation**: Enforces domain-specific rules that go beyond type checking
   - Example: "Only one START node allowed per diagram" (cannot be type-checked)
   - Example: Operator validation for CONDITION nodes (runtime value constraints)

2. **Input Type Resolution**: Maps NodeType enums to their corresponding GraphQL input types
   - Dynamically resolves CreateXxxInput and UpdateXxxInput classes
   - Bridges the gap between generated Strawberry types and runtime execution

3. **Field-Level Validation**: Validates required fields and value constraints
   - Required field presence (beyond GraphQL non-null enforcement)
   - Enum value validation (e.g., valid operators for conditions)
   - Format validation (e.g., language codes for CODE_JOB nodes)

Why NodeTypeRegistry Exists:
----------------------------
While TypeScript specs and generated Strawberry types provide compile-time safety,
certain business rules can only be validated at runtime:

- **Cardinality rules**: "Only one X per Y" (e.g., one START node per diagram)
- **Value constraints**: Allowed operators, languages, formats
- **Cross-field validation**: Dependencies between optional fields
- **Dynamic type resolution**: Runtime mapping from enum to input class

Relationship to Generated Code:
-------------------------------
- Generated types (dipeo/diagram_generated/graphql/): Provide type safety
- NodeTypeRegistry: Adds runtime validation and business rules on top
- Both work together: Types prevent invalid structure, Registry prevents invalid semantics

Example:
--------
    # Type system allows this (structurally valid)
    condition_node = ConditionNode(operator="INVALID_OP")

    # NodeTypeRegistry prevents this (semantically invalid)
    is_valid, error = NodeTypeRegistry.validate_node_data(
        NodeTypeGraphQL.CONDITION,
        {"operator": "INVALID_OP"}
    )
    # Returns: (False, "Invalid operator: INVALID_OP")
"""

from typing import Any

from dipeo.diagram_generated.graphql import node_mutations as nm
from dipeo.diagram_generated.graphql.enums import NodeTypeGraphQL


def _pascal_from_enum(node_type: NodeTypeGraphQL) -> str:
    """Convert node type enum to Pascal case.

    Examples:
        "code_job" -> "CodeJob"
        "json_schema_validator" -> "JsonSchemaValidator"
    """
    return "".join(part.title() for part in node_type.value.split("_"))


def get_input_types(node_type: NodeTypeGraphQL) -> tuple[type | None, type | None]:
    """Get the create and update input types for a node type.

    Args:
        node_type: The node type enum

    Returns:
        Tuple of (CreateInput, UpdateInput) classes, or None if not found
    """
    base = _pascal_from_enum(node_type)
    create = getattr(nm, f"Create{base}Input", None)
    update = getattr(nm, f"Update{base}Input", None)
    return create, update


class NodeTypeRegistry:
    """Registry for mapping node types to their input classes and validation logic.

    This class provides:
    1. Dynamic resolution of Create/Update input types from NodeType enums
    2. Runtime validation of node data against business rules
    3. Type-safe creation of input objects for GraphQL mutations

    The registry maintains validation rules that cannot be expressed in the type system:
    - Cardinality constraints (e.g., "only one START node per diagram")
    - Value enumerations (e.g., valid operators for CONDITION nodes)
    - Format requirements (e.g., supported languages for CODE_JOB)

    Usage:
        # Validate node data
        is_valid, error = NodeTypeRegistry.validate_node_data(
            NodeTypeGraphQL.CONDITION,
            {"operator": "==", "value_b": "test"}
        )

        # Create input object
        input_obj = NodeTypeRegistry.create_node_input(
            node_type=NodeTypeGraphQL.PERSON_JOB,
            diagram_id="diagram-123",
            position={"x": 100, "y": 200},
            data={"person_id": "person-1", "message": "Hello"}
        )

    Note:
        While VALIDATION_RULES define business constraints, the actual GraphQL input
        types are generated from TypeScript specifications. This registry bridges
        runtime validation with compile-time type safety.
    """

    # Node-specific validation rules
    VALIDATION_RULES: dict[NodeTypeGraphQL, dict[str, Any]] = {
        NodeTypeGraphQL.START: {
            "required_fields": [],
            "allow_multiple": False,  # Only one start node per diagram
        },
        NodeTypeGraphQL.PERSON_JOB: {
            "required_fields": ["person_id", "message"],
            "optional_fields": ["variables", "model", "max_tokens"],
        },
        NodeTypeGraphQL.CONDITION: {
            "required_fields": ["operator"],
            "optional_fields": ["value_b", "combine_operator"],
        },
        NodeTypeGraphQL.API_JOB: {
            "required_fields": ["api_id"],
            "optional_fields": ["parameters", "headers"],
        },
        NodeTypeGraphQL.CODE_JOB: {
            "required_fields": ["code_string"],
            "optional_fields": ["language", "timeout"],
        },
        NodeTypeGraphQL.DB: {
            "required_fields": ["db_id", "operation"],
            "optional_fields": ["query", "data"],
        },
        NodeTypeGraphQL.SUB_DIAGRAM: {
            "required_fields": ["diagram_id"],
            "optional_fields": ["inputs", "mode"],
        },
        NodeTypeGraphQL.TEMPLATE_JOB: {
            "required_fields": ["template"],
            "optional_fields": ["variables"],
        },
        NodeTypeGraphQL.JSON_SCHEMA_VALIDATOR: {
            "required_fields": ["json_schema"],
            "optional_fields": [],
        },
        NodeTypeGraphQL.USER_RESPONSE: {
            "required_fields": ["message"],
            "optional_fields": ["timeout", "validation"],
        },
        NodeTypeGraphQL.ENDPOINT: {
            "required_fields": [],
            "optional_fields": ["response_type"],
        },
        NodeTypeGraphQL.HOOK: {
            "required_fields": ["event_type"],
            "optional_fields": ["conditions"],
        },
        NodeTypeGraphQL.INTEGRATED_API: {
            "required_fields": ["api_id"],
            "optional_fields": ["parameters"],
        },
        NodeTypeGraphQL.TYPESCRIPT_AST: {
            "required_fields": ["ast_operation"],
            "optional_fields": ["ast_config"],
        },
    }

    @classmethod
    def get_create_input_class(cls, node_type: NodeTypeGraphQL) -> type | None:
        """Get the create input class for a specific node type."""
        create_cls, _ = get_input_types(node_type)
        return create_cls

    @classmethod
    def get_update_input_class(cls, node_type: NodeTypeGraphQL) -> type | None:
        """Get the update input class for a specific node type."""
        _, update_cls = get_input_types(node_type)
        return update_cls

    @classmethod
    def validate_node_data(
        cls, node_type: NodeTypeGraphQL, data: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """Validate node data against type-specific rules.

        Args:
            node_type: The type of node to validate
            data: The node data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        rules = cls.VALIDATION_RULES.get(node_type, {})

        # Check required fields
        required_fields = rules.get("required_fields", [])
        for field in required_fields:
            if field not in data or data[field] is None:
                return False, f"Missing required field '{field}' for {node_type.value} node"

        # Validate specific node type constraints
        if node_type == NodeTypeGraphQL.PERSON_JOB:
            if "person_id" in data and not isinstance(data["person_id"], str):
                return (
                    False,
                    f"Field 'person_id' must be a string, got {type(data['person_id']).__name__}",
                )

        elif node_type == NodeTypeGraphQL.CONDITION:
            valid_operators = [
                "==",
                "!=",
                ">",
                "<",
                ">=",
                "<=",
                "in",
                "not_in",
                "contains",
                "not_contains",
            ]
            if "operator" in data and data["operator"] not in valid_operators:
                return False, (
                    f"Invalid operator '{data['operator']}' for CONDITION node. "
                    f"Valid operators: {', '.join(valid_operators)}"
                )

        elif node_type == NodeTypeGraphQL.API_JOB:
            if "api_id" in data and not isinstance(data["api_id"], str):
                return (
                    False,
                    f"Field 'api_id' must be a string, got {type(data['api_id']).__name__}",
                )

        elif node_type == NodeTypeGraphQL.CODE_JOB:
            valid_languages = ["python", "javascript", "typescript", "bash", "sql"]
            if "language" in data and data["language"] not in valid_languages:
                return False, (
                    f"Invalid language '{data['language']}' for CODE_JOB node. "
                    f"Supported languages: {', '.join(valid_languages)}"
                )

        return True, None

    @classmethod
    def create_node_input(
        cls,
        node_type: NodeTypeGraphQL,
        diagram_id: str,
        position: dict[str, float],
        data: dict[str, Any],
    ) -> Any:
        """Create a type-specific node input object.

        Args:
            node_type: The type of node to create
            diagram_id: The diagram ID
            position: Node position with x and y coordinates
            data: Node-specific data

        Returns:
            Type-specific input object
        """
        input_class = cls.get_create_input_class(node_type)
        if not input_class:
            raise ValueError(
                f"No create input class found for node type '{node_type.value}'. "
                f"Ensure the corresponding CreateXxxInput is defined in node_mutations."
            )

        # Validate the data
        is_valid, error = cls.validate_node_data(node_type, data)
        if not is_valid:
            raise ValueError(f"Invalid {node_type.value} node data: {error}")

        # Create the input object
        from dipeo.diagram_generated.graphql.inputs import Vec2Input

        return input_class(
            diagram_id=diagram_id, position=Vec2Input(x=position["x"], y=position["y"]), data=data
        )

    @classmethod
    def update_node_input(
        cls,
        node_type: NodeTypeGraphQL,
        position: dict[str, float] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Create a type-specific node update input object.

        Args:
            node_type: The type of node to update
            position: Optional new position
            data: Optional node-specific data updates

        Returns:
            Type-specific update input object
        """
        input_class = cls.get_update_input_class(node_type)
        if not input_class:
            raise ValueError(
                f"No update input class found for node type '{node_type.value}'. "
                f"Ensure the corresponding UpdateXxxInput is defined in node_mutations."
            )

        # Validate the data if provided
        if data:
            is_valid, error = cls.validate_node_data(node_type, data)
            if not is_valid:
                raise ValueError(f"Invalid {node_type.value} node data: {error}")

        # Create the update input object
        kwargs = {}
        if position:
            from dipeo.diagram_generated.graphql.inputs import Vec2Input

            kwargs["position"] = Vec2Input(x=position["x"], y=position["y"])
        if data is not None:
            kwargs["data"] = data

        return input_class(**kwargs)

    @classmethod
    def get_node_type_from_string(cls, type_string: str) -> NodeTypeGraphQL | None:
        """Convert a string node type to the enum.

        Args:
            type_string: String representation of node type

        Returns:
            NodeTypeGraphQL enum value or None if not found
        """
        try:
            # Convert string to uppercase and replace spaces with underscores
            enum_key = type_string.upper().replace(" ", "_")
            return NodeTypeGraphQL[enum_key]
        except (KeyError, AttributeError):
            # Try direct value match
            for node_type in NodeTypeGraphQL:
                if node_type.value == type_string:
                    return node_type
            return None
