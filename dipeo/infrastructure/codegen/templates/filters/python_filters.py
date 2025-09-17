"""Python code generation filters.

This module provides filters specifically for Python code generation,
extracted from various backend and type conversion filters.
"""

import re
from typing import Any


class PythonFilters:
    """Python code generation filters."""

    @staticmethod
    def python_default(field: dict[str, Any]) -> str:
        """Get Python default value for a field."""
        field_type = field.get("type", "string")
        is_required = field.get("required", False)

        if "default" in field:
            default_val = field["default"]
            if isinstance(default_val, str):
                return f'"{default_val}"'
            elif isinstance(default_val, bool):
                return "True" if default_val else "False"
            elif default_val is None:
                return "None"
            else:
                return str(default_val)

        if not is_required:
            return "None"

        if field_type in ["object", "dict"]:
            return "field(default_factory=dict)"
        elif field_type in ["array", "list"]:
            return "field(default_factory=list)"
        elif field_type == "string":
            return '""'
        elif field_type == "number":
            return "0"
        elif field_type == "boolean":
            return "False"
        else:
            return "None"

    @staticmethod
    def pythonize_name(name: str) -> str:
        """Convert camelCase/PascalCase to snake_case."""
        if not name:
            return ""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    @classmethod
    def python_class_name(cls, node_type: str) -> str:
        """Generate Python class name from node type."""
        if not node_type:
            return "UnknownNode"
        parts = node_type.split("_")
        return "".join(part.title() for part in parts) + "Node"

    @classmethod
    def handler_class_name(cls, node_type: str) -> str:
        """Generate handler class name from node type."""
        if not node_type:
            return "UnknownNodeHandler"
        parts = node_type.split("_")
        return "".join(part.title() for part in parts) + "NodeHandler"

    @staticmethod
    def get_pydantic_field(field: dict[str, Any]) -> str:
        """Generate Pydantic Field() definition for a field."""
        parts = []

        if not field.get("required", False):
            default_val = field.get("default")
            if default_val is None:
                parts.append("default=None")
            elif isinstance(default_val, str):
                parts.append(f'default="{default_val}"')
            elif isinstance(default_val, list | dict):
                parts.append(f"default_factory=lambda: {default_val!r}")
            else:
                parts.append(f"default={default_val}")

        if desc := field.get("description"):
            parts.append(f'description="{desc}"')

        original_name = field.get("name", "")
        python_name = PythonFilters.pythonize_name(original_name)
        if python_name != original_name:
            parts.append(f'alias="{original_name}"')

        if validation := field.get("validation"):
            if "minLength" in validation:
                parts.append(f'min_length={validation["minLength"]}')
            if "maxLength" in validation:
                parts.append(f'max_length={validation["maxLength"]}')
            if "pattern" in validation:
                parts.append(f'regex=r"{validation["pattern"]}"')
            if "min" in validation:
                parts.append(f'ge={validation["min"]}')
            if "max" in validation:
                parts.append(f'le={validation["max"]}')

        if parts:
            return f'Field({", ".join(parts)})'
        else:
            return "..." if field.get("required", False) else "None"

    @staticmethod
    def needs_field_alias(field: dict[str, Any]) -> bool:
        """Check if field needs an alias (camelCase vs snake_case)."""
        original = str(field.get("name", ""))
        pythonized = PythonFilters.pythonize_name(original)
        return original != pythonized

    @staticmethod
    def calculate_python_imports(spec_data: dict[str, Any]) -> list[str]:
        """Calculate Python imports needed for the model."""
        imports = set()

        imports.add("from typing import Dict, Any, List, Optional, Union")
        imports.add("from pydantic import BaseModel, Field")

        if any(field.get("validation") for field in spec_data.get("fields", [])):
            imports.add("from pydantic import validator")

        types_used = set()
        for field in spec_data.get("fields", []):
            field_type = field.get("type", "string")
            if "List[" in field_type or field_type.endswith("[]"):
                types_used.add("List")
            if "Dict[" in field_type or "Record<" in field_type:
                types_used.add("Dict")
            if field.get("enum") or field_type == "enum":
                imports.add("from enum import Enum")
            if "|" in field_type and "Literal[" in field_type:
                imports.add("from typing import Literal")

        node_type = spec_data.get("nodeType", "")
        if node_type:
            imports.add("from dipeo.diagram_generated.models.base import BaseNodeModel")

        return sorted(list(imports))

    @staticmethod
    def build_validators(spec_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Build validator methods for the model."""
        validators = []

        for field in spec_data.get("fields", []):
            if validation := field.get("validation"):
                field_name = PythonFilters.pythonize_name(field["name"])

                if "custom" in validation:
                    validators.append(
                        {
                            "field": field_name,
                            "name": f"validate_{field_name}",
                            "code": validation["custom"],
                        }
                    )

                elif "pattern" in validation and field.get("type") == "string":
                    validators.append(
                        {
                            "field": field_name,
                            "name": f"validate_{field_name}_pattern",
                            "code": f"""
        import re
        if v and not re.match(r"{validation['pattern']}", v):
            raise ValueError(f"Invalid format for {field_name}")
        return v""",
                        }
                    )

        return validators

    @staticmethod
    def build_model_config(spec_data: dict[str, Any]) -> dict[str, Any]:
        """Build Pydantic model configuration."""
        config = {
            "use_enum_values": True,
            "validate_assignment": True,
            "extra": "forbid",
        }

        if any(PythonFilters.needs_field_alias(f) for f in spec_data.get("fields", [])):
            config["allow_population_by_field_name"] = True

        if custom_config := spec_data.get("modelConfig"):
            config.update(custom_config)

        return config

    @staticmethod
    def generate_enum_classes(spec_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate enum class definitions."""
        enums = []

        for field in spec_data.get("fields", []):
            if field.get("enum") and isinstance(field["enum"], list):
                enum_name = f"{field['name'].title().replace('_', '')}Enum"
                enums.append(
                    {"name": enum_name, "values": field["enum"], "field_name": field["name"]}
                )

        return enums

    @staticmethod
    def spec_to_camel_name(node_type: str) -> str:
        """Convert node type to camelCase spec name."""
        if not node_type:
            return "unknownSpec"
        parts = node_type.split("_")
        if not parts:
            return "unknownSpec"
        camel = parts[0].lower() + "".join(p.title() for p in parts[1:])
        return f"{camel}Spec"

    @staticmethod
    def python_type_with_context(
        field: dict[str, Any], node_type: str, mappings: dict[str, Any] | None = None
    ) -> str:
        """Convert field type to Python type with context awareness."""
        field_name = field.get("name", "")
        field_type = field.get("type", "string")
        is_required = field.get("required", False)
        default_value = field.get("default")

        base_type = None

        context_mappings = {
            "method": "HttpMethod",
            "sub_type": "DBBlockSubType",
            "language": "SupportedLanguage",
            "code_type": "SupportedLanguage",
            "hook_type": "HookType",
            "trigger_mode": "HookTriggerMode",
            "service": "LLMService",
            "diagram_format": "DiagramFormat",
        }

        if field_name in context_mappings:
            base_type = context_mappings[field_name]
        elif mappings and "ts_to_py_type" in mappings and field_type in mappings["ts_to_py_type"]:
            base_type = str(mappings["ts_to_py_type"][field_type])
        elif node_type == "person_job":
            if field_name == "person_id":
                base_type = "PersonID"
            elif field_name == "llm_config":
                base_type = "PersonLLMConfig"
            elif field_name == "memory_settings":
                base_type = "MemorySettings"
            elif field_name == "memory_profile":
                base_type = "str"
            elif field_name == "tools":
                base_type = "List[ToolConfig]"

        if base_type is None:
            if field_name == "maxIteration" or field_name == "max_iteration":
                base_type = "int"
            elif field_type == "object" or field_type == "dict":
                base_type = "Dict[str, Any]"
            elif field_type == "array" or field_type == "list":
                base_type = "List[Any]"
            elif field_type == "string":
                base_type = "str"
            elif field_type == "number":
                if field_name in {
                    "maxIteration",
                    "max_iteration",
                    "sequence",
                    "messageCount",
                    "timeout",
                    "timeoutSeconds",
                    "durationSeconds",
                    "maxTokens",
                    "statusCode",
                    "port",
                    "x",
                    "y",
                    "width",
                    "height",
                }:
                    base_type = "int"
                else:
                    base_type = "float"
            elif field_type == "boolean":
                base_type = "bool"
            elif field_type == "enum":
                values = field.get("values", [])
                if not values and field.get("validation"):
                    values = field.get("validation", {}).get("allowedValues", [])

                if values:
                    quoted_values = ", ".join(f'"{v}"' for v in values)
                    base_type = f"Literal[{quoted_values}]"
                else:
                    base_type = "str"
            elif field_type == "any":
                base_type = "Any"
            else:
                base_type = field_type

        if not is_required:
            if field_type in ["object", "dict", "array", "list"]:
                return f"Optional[{base_type}]"
            if "default" in field and field["default"] is not None:
                return base_type
            return f"Optional[{base_type}]"

        return base_type

    @staticmethod
    def get_field_python_type(field: dict[str, Any], context: dict[str, Any]) -> str:
        """Get Python type for a field with context."""
        node_type = context.get("nodeType", "")
        mappings = context.get("mappings", {})
        return PythonFilters.python_type_with_context(field, node_type, mappings)

    @staticmethod
    def get_static_node_imports(spec_data: dict[str, Any]) -> list[str]:
        """Calculate imports for static node implementation."""
        imports = [
            "from typing import Dict, Any, List, Optional",
            "from dipeo.application.execution.handler_base import TypedNodeHandler",
            "from dipeo.diagram_generated.generated_nodes import *",
            "from dipeo.application.registry.keys import LLM_SERVICE, CODE_EXECUTOR, HTTP_CLIENT, FILESYSTEM_ADAPTER",
            "from dipeo.domain.base.exceptions import ValidationError, ExecutionError",
        ]

        return sorted(list(set(imports)))

    @staticmethod
    def get_execution_logic(node_type: str) -> list[str]:
        """Get main execution logic lines for a node type."""
        logic_map = {
            "person_job": [
                "llm_service = request.services[LLM_SERVICE]",
                "response = await llm_service.generate(",
                "    prompt=node.props.get('default_prompt', ''),",
                "    model=node.props.get('model'),",
                "    temperature=node.props.get('temperature', 0.7)",
                ")",
                "return {'content': response.content}",
            ],
            "code_job": [
                "code_executor = request.services[CODE_EXECUTOR]",
                "result = await code_executor.execute(",
                "    code=node.props.get('code', ''),",
                "    language=node.props.get('code_type', 'python'),",
                "    inputs=inputs",
                ")",
                "return result",
            ],
            "api_job": [
                "http_client = request.services[HTTP_CLIENT]",
                "response = await http_client.request(",
                "    method=node.props.get('method', 'GET'),",
                "    url=node.props.get('url'),",
                "    headers=node.props.get('headers', {}),",
                "    data=node.props.get('body')",
                ")",
                "return {'response': response.json()}",
            ],
            "condition": [
                "condition_type = node.props.get('condition_type')",
                "if condition_type == 'custom':",
                "    expression = node.props.get('expression', 'True')",
                "    result = eval(expression, {'__builtins__': {}}, inputs)",
                "elif condition_type == 'detect_max_iterations':",
                "    result = self._check_max_iterations(context)",
                "else:",
                "    result = True",
                "return {'result': bool(result)}",
            ],
            "template_job": [
                "template_service = request.services.get('template_service')",
                "result = await template_service.render(",
                "    engine=node.props.get('engine', 'jinja2'),",
                "    template_path=node.props.get('template_path'),",
                "    template_content=node.props.get('template_content'),",
                "    context=inputs,",
                "    output_path=node.props.get('output_path')",
                ")",
                "return result",
            ],
        }

        return logic_map.get(
            node_type,
            [
                "# TODO: Implement node-specific logic",
                "return {'result': 'success'}",
            ],
        )

    @staticmethod
    def get_validation_checks(spec_data: dict[str, Any]) -> list[str]:
        """Get validation check lines for required fields."""
        checks = []

        for field in spec_data.get("fields", []):
            if field.get("required"):
                field_name = field["name"]
                checks.append(
                    f"if '{field_name}' not in node.props:\n"
                    f"    raise ValidationError('Missing required field: {field_name}')"
                )

        node_type = spec_data.get("nodeType", "")
        if node_type == "api_job":
            checks.extend(
                [
                    "if not node.props.get('url'):",
                    "    raise ValidationError('API job requires URL')",
                ]
            )
        elif node_type == "code_job":
            checks.extend(
                [
                    "if not node.props.get('code'):",
                    "    raise ValidationError('Code job requires code')",
                ]
            )
        elif node_type == "template_job":
            checks.extend(
                [
                    "if not node.props.get('template_path') and not node.props.get('template_content'):",
                    "    raise ValidationError('Template job requires either template_path or template_content')",
                ]
            )

        return checks

    @classmethod
    def get_all_filters(cls) -> dict:
        """Get all filter methods as a dictionary."""
        return {
            "python_default": cls.python_default,
            "pythonize_name": cls.pythonize_name,
            "python_class_name": cls.python_class_name,
            "handler_class_name": cls.handler_class_name,
            "get_pydantic_field": cls.get_pydantic_field,
            "needs_field_alias": cls.needs_field_alias,
            "calculate_python_imports": cls.calculate_python_imports,
            "build_validators": cls.build_validators,
            "build_model_config": cls.build_model_config,
            "generate_enum_classes": cls.generate_enum_classes,
            "spec_to_camel_name": cls.spec_to_camel_name,
            "python_type_with_context": cls.python_type_with_context,
            "get_field_python_type": cls.get_field_python_type,
            "get_static_node_imports": cls.get_static_node_imports,
            "get_execution_logic": cls.get_execution_logic,
            "get_validation_checks": cls.get_validation_checks,
        }
