"""Node specification extraction and processing module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from dipeo.infrastructure.codegen.ir_builders.core import (
    BaseExtractionStep,
    BuildContext,
    BuildStep,
    StepResult,
    StepType,
)
from dipeo.infrastructure.codegen.ir_builders.utils import (
    TypeConverter,
    camel_to_snake,
    snake_to_pascal,
)


class ExtractNodeSpecsStep(BaseExtractionStep):
    """Step to extract node specifications from TypeScript AST."""

    def __init__(self):
        """Initialize node specs extraction step."""
        super().__init__(name="extract_node_specs", required=True)

    def should_process_file(self, file_path: str, file_data: dict[str, Any]) -> bool:
        """Filter to only process node spec files.

        Args:
            file_path: Path to the AST file
            file_data: AST data for the file

        Returns:
            True if file is a node spec file
        """
        return file_path.endswith(".spec.ts.json")

    def extract_from_file(
        self,
        file_path: str,
        file_data: dict[str, Any],
        type_converter: TypeConverter,
        context: BuildContext,
    ) -> Optional[dict[str, Any]]:
        """Extract node specification from a single AST file.

        Args:
            file_path: Path to the AST file
            file_data: AST data for the file
            type_converter: Type converter instance

        Returns:
            Node specification if found, None otherwise
        """
        # Extract node type from filename
        base_name = Path(file_path).stem.replace(".spec.ts", "")
        node_type = base_name.replace("-", "_")
        node_name = snake_to_pascal(node_type)

        # Look for specification constants
        for const in file_data.get("constants", []):
            const_name = const.get("name", "")
            if const_name.endswith("Spec") or const_name.endswith("Specification"):
                spec_value = const.get("value", {})
                if not isinstance(spec_value, dict):
                    continue

                return self._build_node_spec(node_type, node_name, spec_value, type_converter)

        return None

    def _build_node_spec(
        self,
        node_type: str,
        node_name: str,
        spec_value: dict[str, Any],
        type_converter: TypeConverter,
    ) -> dict[str, Any]:
        """Build node specification from spec value.

        Args:
            node_type: Node type identifier
            node_name: Node class name
            spec_value: Specification value from AST
            type_converter: Type converter instance

        Returns:
            Node specification dictionary
        """
        fields = self._process_fields(spec_value.get("fields", []), node_type, type_converter)
        handler_metadata = spec_value.get("handlerMetadata", {})
        camel_case_name = self._to_camel_case(node_type)

        spec_details = {
            "nodeType": spec_value.get("nodeType", f"NodeType.{node_type.upper()}"),
            "displayName": spec_value.get("displayName", node_name),
            "category": spec_value.get("category", ""),
            "description": spec_value.get("description", ""),
            "icon": spec_value.get("icon", ""),
            "color": spec_value.get("color", ""),
            "fields": fields,
            "handles": spec_value.get("handles", {}),
            "outputs": spec_value.get("outputs", {}),
            "execution": spec_value.get("execution", {}),
            "primaryDisplayField": spec_value.get("primaryDisplayField", ""),
            "defaults": spec_value.get("defaults", {}),
            "handlerMetadata": handler_metadata,
        }

        return {
            "node_type": node_type,
            "node_name": node_name,
            "name": camel_case_name,
            "display_name": spec_details["displayName"],
            "category": spec_details["category"],
            "description": spec_details["description"],
            "fields": fields,
            "icon": spec_details["icon"],
            "color": spec_details["color"],
            "handler_metadata": handler_metadata,
            "spec": spec_details,
            "raw_spec": spec_value,
        }

    def _process_fields(
        self, fields: list[dict[str, Any]], node_type: str, type_converter: TypeConverter
    ) -> list[dict[str, Any]]:
        """Process and normalize field definitions.

        Args:
            fields: Raw field definitions
            node_type: Node type for context
            type_converter: Type converter instance

        Returns:
            Processed field definitions
        """
        processed = []
        for field in fields:
            processed_field = self._process_field(field, node_type, type_converter)
            if processed_field and processed_field.get("name"):
                processed.append(processed_field)
        return processed

    def _process_field(
        self, field: dict[str, Any], node_type: str, type_converter: TypeConverter
    ) -> dict[str, Any]:
        """Normalize a single field definition.

        Args:
            field: Raw field definition
            node_type: Node type for context
            type_converter: Type converter instance

        Returns:
            Normalized field definition
        """
        raw_type = field.get("type", "string")
        if isinstance(raw_type, dict):
            field_type = raw_type.get("name") or raw_type.get("text") or "any"
        else:
            field_type = str(raw_type)

        field_name = field.get("name", "")
        validation = field.get("validation", {}) or {}
        enum_values = field.get("enumValues") or validation.get("allowedValues", []) or []

        python_type, graphql_type, is_object_type = self._map_field_types(
            field_type, field_name, node_type, enum_values, type_converter
        )

        is_enum = bool(enum_values) or field_type == "enum"

        return {
            "name": field_name,
            "type": field_type,
            "python_type": python_type,
            "graphql_type": graphql_type,
            "required": field.get("required", False),
            "description": field.get("description", ""),
            "validation": validation,
            "uiConfig": field.get("uiConfig", {}),
            "default": field.get("defaultValue"),
            "is_object_type": is_object_type,
            "is_dict_type": is_object_type,
            "is_enum": is_enum,
            "enum_values": enum_values,
        }

    def _map_field_types(
        self,
        field_type: str,
        field_name: str,
        node_type: str,
        enum_values: list[Any],
        type_converter: TypeConverter,
    ) -> tuple[str, str, bool]:
        """Determine Python and GraphQL types along with object flag.

        Args:
            field_type: TypeScript field type
            field_name: Field name
            node_type: Node type for context
            enum_values: Enum values if applicable
            type_converter: Type converter instance

        Returns:
            Tuple of (python_type, graphql_type, is_object_type)
        """
        normalized = field_type.lower()
        is_object_type = False

        if normalized in {"string", "text"}:
            return "str", "String", is_object_type
        if normalized == "number":
            return "int", "Int", is_object_type
        if normalized == "boolean":
            return "bool", "Boolean", is_object_type
        if normalized in {"object", "dict"}:
            is_object_type = True
            return "Dict[str, Any]", "JSON", is_object_type
        if normalized in {"array", "list"}:
            return "List[Any]", "[JSON]", is_object_type
        if normalized == "enum" or enum_values:
            enum_type_name = (
                f"{self._to_camel_case(node_type)}{field_name.title().replace(' ', '')}Enum"
            )
            return enum_type_name, enum_type_name, is_object_type

        # Fallback to type converter
        python_type = type_converter.ts_to_python(field_type)
        graphql_type = type_converter.ts_to_graphql(field_type)

        return python_type or field_type, graphql_type or field_type, is_object_type

    def get_metadata(self, extracted_data: list[Any]) -> dict[str, Any]:
        """Generate metadata for extraction result.

        Args:
            extracted_data: Extracted node specifications

        Returns:
            Metadata dictionary
        """
        return {"node_count": len(extracted_data)}

    def _to_camel_case(self, node_type: str) -> str:
        """Convert node type to camel case.

        Args:
            node_type: Node type in snake_case

        Returns:
            Camel case version
        """
        pascal = snake_to_pascal(node_type)
        if not pascal:
            return node_type
        return pascal[0].lower() + pascal[1:]


class BuildNodeFactoryStep(BuildStep):
    """Step to build factory data for node creation."""

    def __init__(self):
        """Initialize factory builder step."""
        super().__init__(name="build_node_factory", step_type=StepType.TRANSFORM, required=True)
        self.add_dependency("extract_node_specs")

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Build factory data from node specifications.

        Args:
            context: Build context
            input_data: Dictionary with node specs from extraction step

        Returns:
            StepResult with factory data
        """
        # Handle input from dependencies
        if isinstance(input_data, dict) and "extract_node_specs" in input_data:
            node_specs = input_data["extract_node_specs"]
        elif isinstance(input_data, list):
            node_specs = input_data
        else:
            return StepResult(success=False, error="Expected node specifications as input")

        factory_data = self._build_factory_data(node_specs)

        return StepResult(
            success=True,
            data=factory_data,
            metadata={
                "node_count": len(node_specs),
                "category_count": len(factory_data["categories"]),
            },
        )

    def _build_factory_data(self, node_specs: list[dict[str, Any]]) -> dict[str, Any]:
        """Build factory data for node creation from specs.

        Args:
            node_specs: List of node specifications

        Returns:
            Factory data dictionary
        """
        factory_data = {
            "imports": [],
            "factory_cases": [],
            "categories": [],
            "mappings": {},
        }

        seen_categories = set()

        for spec in node_specs:
            node_type = spec.get("node_type", "")
            node_name = spec.get("node_name", "")
            category = spec.get("category", "")

            if not node_type or not node_name:
                continue

            # Build import statement
            module_name = f"unified_nodes.{camel_to_snake(node_name)}_node"
            class_name = f"{node_name}Node"
            alias = "DBNode" if node_type == "db" else None
            factory_data["imports"].append(
                {
                    "module": module_name,
                    "class": class_name,
                    "alias": alias,
                }
            )

            factory_data["mappings"][node_type] = {
                "class_name": class_name,
                "display_name": spec.get("display_name", node_name),
                "category": category,
            }

            field_mappings = self._build_field_mappings(spec.get("fields", []))

            factory_data["factory_cases"].append(
                {
                    "node_type": f"NodeType.{node_type.upper()}",
                    "class_name": alias or class_name,
                    "field_mappings": field_mappings,
                }
            )

            if category and category not in seen_categories:
                seen_categories.add(category)
                factory_data["categories"].append(category)

        return factory_data

    def _build_field_mappings(self, fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Build field mappings for factory case.

        Args:
            fields: Field definitions

        Returns:
            Field mapping list
        """
        field_mappings = []
        for field in fields:
            field_name = field.get("name")
            if not field_name:
                continue

            # Special case handlers
            if field_name == "file_path":
                getter = "data.get('filePath', data.get('file_path', ''))"
            elif field_name == "function_name":
                getter = "data.get('functionName', data.get('function_name', ''))"
            elif field_name == "condition_type":
                getter = "data.get('condition_type')"
            elif field_name == "expression":
                getter = "data.get('expression', data.get('condition', ''))"
            else:
                default_val = field.get("default")
                if default_val is not None:
                    if isinstance(default_val, str):
                        getter = f"data.get('{field_name}', '{default_val}')"
                    else:
                        getter = f"data.get('{field_name}', {default_val})"
                else:
                    getter = f"data.get('{field_name}')"

            field_mappings.append(
                {
                    "node_field": field_name,
                    "getter_expression": getter,
                }
            )

        return field_mappings


class BuildCategoryMetadataStep(BuildStep):
    """Step to build category metadata from node specifications."""

    def __init__(self):
        """Initialize category metadata builder step."""
        super().__init__(
            name="build_category_metadata", step_type=StepType.TRANSFORM, required=False
        )
        self.add_dependency("extract_node_specs")

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Build category metadata from node specifications.

        Args:
            context: Build context
            input_data: Dictionary with node specs from extraction step

        Returns:
            StepResult with category metadata
        """
        # Handle input from dependencies
        if isinstance(input_data, dict) and "extract_node_specs" in input_data:
            node_specs = input_data["extract_node_specs"]
        elif isinstance(input_data, list):
            node_specs = input_data
        else:
            return StepResult(success=False, error="Expected node specifications as input")

        categories = self._extract_categories(node_specs)

        return StepResult(
            success=True,
            data={"categories": categories},
            metadata={"category_count": len(categories)},
        )

    def _extract_categories(self, node_specs: list[dict[str, Any]]) -> list[str]:
        """Extract unique categories from node specifications.

        Args:
            node_specs: List of node specifications

        Returns:
            List of unique categories
        """
        categories = set()
        for spec in node_specs:
            category = spec.get("category", "")
            if category:
                categories.add(category)
        return sorted(list(categories))
