import contextlib
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
from dipeo.diagram_generated.unified_nodes.json_schema_validator_node import (
    JsonSchemaValidatorNode,
    NodeType,
)
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass


@register_handler
@requires_services(filesystem_adapter=FILESYSTEM_ADAPTER)
class JsonSchemaValidatorNodeHandler(TypedNodeHandler[JsonSchemaValidatorNode]):
    """Handler for JSON Schema validation.

    Now uses envelope-based communication for clean input/output interfaces.
    """

    NODE_TYPE = NodeType.JSON_SCHEMA_VALIDATOR

    def __init__(self):
        super().__init__()
        self._validator = None

    @property
    def node_class(self) -> type[JsonSchemaValidatorNode]:
        return JsonSchemaValidatorNode

    @property
    def node_type(self) -> str:
        return NodeType.JSON_SCHEMA_VALIDATOR.value

    @property
    def schema(self) -> type[BaseModel]:
        return JsonSchemaValidatorNode

    @property
    def description(self) -> str:
        return "Validates JSON data against a JSON Schema specification"

    def validate(self, request: ExecutionRequest[JsonSchemaValidatorNode]) -> str | None:
        node = request.node
        if not node.schema_path and not node.json_schema:
            return "Either schema_path or json_schema must be provided"

        return None

    async def pre_execute(
        self, request: ExecutionRequest[JsonSchemaValidatorNode]
    ) -> Envelope | None:
        node = request.node
        services = request.services

        request.set_handler_state("strict_mode", node.strict_mode or False)
        request.set_handler_state("error_on_extra", node.error_on_extra or False)
        request.set_handler_state("schema_path", node.schema_path)
        request.set_handler_state("debug", False)

        filesystem_adapter = request.get_optional_service(FILESYSTEM_ADAPTER)
        if not filesystem_adapter:
            return EnvelopeFactory.create(
                body={
                    "error": "Filesystem adapter is required for JSON schema validation",
                    "type": "RuntimeError",
                },
                produced_by=str(node.id),
            )

        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[JsonSchemaValidatorNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelope inputs to data for validation.

        Phase 5: Now consumes tokens from incoming edges when available.
        """
        envelope_inputs = self.get_effective_inputs(request, inputs)

        node = request.node
        services = request.services
        filesystem_adapter = request.get_required_service(FILESYSTEM_ADAPTER)

        request.set_handler_state("envelope_inputs", envelope_inputs)

        if node.data_path:
            data_path = Path(node.data_path)
            if not data_path.is_absolute():
                base_dir = os.getenv("DIPEO_BASE_DIR", os.getcwd())
                data_path = Path(base_dir) / node.data_path

            if not filesystem_adapter.exists(data_path):
                raise ValueError(f"Data file not found: {node.data_path}")

            with filesystem_adapter.open(data_path, "rb") as f:
                data_to_validate = json.loads(f.read().decode("utf-8"))
        else:
            if not envelope_inputs:
                raise ValueError("No input data provided and no data_path specified")

            if len(envelope_inputs) == 1:
                envelope = next(iter(envelope_inputs.values()))
                try:
                    data_to_validate = envelope.as_json()
                except ValueError:
                    data_to_validate = envelope.as_text()
                    if (
                        isinstance(data_to_validate, str)
                        and data_to_validate.strip()
                        and data_to_validate.strip()[0] in "{["
                    ):
                        with contextlib.suppress(json.JSONDecodeError):
                            data_to_validate = json.loads(data_to_validate)
            else:
                data_to_validate = {}
                for key, envelope in envelope_inputs.items():
                    try:
                        data_to_validate[key] = envelope.as_json()
                    except ValueError:
                        value = envelope.as_text()
                        if isinstance(value, str) and value.strip() and value.strip()[0] in "{[":
                            try:
                                data_to_validate[key] = json.loads(value)
                            except json.JSONDecodeError:
                                data_to_validate[key] = value
                        else:
                            data_to_validate[key] = value

        return {"data": data_to_validate}

    async def run(
        self, inputs: dict[str, Any], request: ExecutionRequest[JsonSchemaValidatorNode]
    ) -> Any:
        node = request.node
        services = request.services
        filesystem_adapter = self._filesystem_adapter

        if node.json_schema:
            schema = node.json_schema
        else:
            schema_path = Path(node.schema_path)
            if not schema_path.is_absolute():
                base_dir = os.getenv("DIPEO_BASE_DIR", os.getcwd())
                schema_path = Path(base_dir) / node.schema_path

            if not filesystem_adapter.exists(schema_path):
                raise ValueError(f"Schema file not found: {node.schema_path}")

            with filesystem_adapter.open(schema_path, "rb") as f:
                schema = json.loads(f.read().decode("utf-8"))

        data_to_validate = inputs["data"]

        validation_result = await self._validate_data(
            data_to_validate,
            schema,
            strict_mode=request.get_handler_state("strict_mode"),
            error_on_extra=request.get_handler_state("error_on_extra"),
        )

        if validation_result["valid"]:
            debug = request.get_handler_state("debug")
            schema_path = request.get_handler_state("schema_path")
            if debug:
                print(f"[JsonSchemaValidatorNode] ✓ Validation successful for node {node.id}")
                if node.data_path:
                    print(f"[JsonSchemaValidatorNode]   - Data file: {node.data_path}")
                if schema_path:
                    print(f"[JsonSchemaValidatorNode]   - Schema file: {schema_path}")

            return {
                "data": data_to_validate,
                "validation_result": validation_result,
                "schema_path": request.get_handler_state("schema_path"),
                "data_path": node.data_path,
            }
        else:
            debug = request.get_handler_state("debug")
            schema_path = request.get_handler_state("schema_path")
            if debug:
                print(f"[JsonSchemaValidatorNode] ✗ Validation FAILED for node {node.id}")
                if node.data_path:
                    print(f"[JsonSchemaValidatorNode]   - Data file: {node.data_path}")
                if schema_path:
                    print(f"[JsonSchemaValidatorNode]   - Schema file: {schema_path}")
                print(
                    f"[JsonSchemaValidatorNode]   - Errors found: {len(validation_result['errors'])}"
                )
                for i, error in enumerate(validation_result["errors"][:3]):
                    print(f"[JsonSchemaValidatorNode]     {i+1}. {error}")
                if len(validation_result["errors"]) > 3:
                    print(
                        f"[JsonSchemaValidatorNode]     ... and {len(validation_result['errors']) - 3} more errors"
                    )

            error_message = f"Validation failed: {'; '.join(validation_result['errors'])}"
            raise ValueError(error_message)

    def serialize_output(
        self, result: Any, request: ExecutionRequest[JsonSchemaValidatorNode]
    ) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""

        data = result["data"]

        output_envelope = EnvelopeFactory.create(
            body=data if isinstance(data, dict) else {"default": data},
            produced_by=node.id,
            trace_id=trace_id,
        ).with_meta(
            strict_mode=request.get_handler_state("strict_mode"),
            message="Validation successful",
            schema_path=result.get("schema_path"),
            data_path=result.get("data_path"),
        )

        return output_envelope

    async def _validate_data(
        self, data: Any, schema: dict, strict_mode: bool = False, error_on_extra: bool = False
    ) -> dict[str, Any]:
        try:
            import jsonschema
            from jsonschema import Draft7Validator, validators

            errors = []

            if error_on_extra:
                schema = self._add_no_additional_properties(schema.copy())
            validator_class = validators.validator_for(schema)
            validator = validator_class(schema)

            if strict_mode:
                errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
                if errors:
                    return {
                        "valid": False,
                        "errors": [
                            f"{'.'.join(str(p) for p in error.path)}: {error.message}"
                            if error.path
                            else error.message
                            for error in errors
                        ],
                    }
            else:
                try:
                    validator.validate(data)
                except jsonschema.ValidationError as e:
                    error_path = ".".join(str(p) for p in e.path) if e.path else "root"
                    return {"valid": False, "errors": [f"{error_path}: {e.message}"]}

            return {"valid": True, "errors": []}

        except ImportError as e:
            raise ImportError(
                "jsonschema is not installed. Install it with: pip install jsonschema"
            ) from e

    def _add_no_additional_properties(self, schema: dict) -> dict:
        if isinstance(schema, dict):
            if schema.get("type") == "object" and "additionalProperties" not in schema:
                schema["additionalProperties"] = False

            for key, value in schema.items():
                if key in ["properties", "patternProperties", "definitions"]:
                    if isinstance(value, dict):
                        for prop_key, prop_schema in value.items():
                            schema[key][prop_key] = self._add_no_additional_properties(prop_schema)
                elif key in ["items", "additionalItems", "contains"]:
                    schema[key] = self._add_no_additional_properties(value)
                elif key in ["allOf", "anyOf", "oneOf"] and isinstance(value, list):
                    schema[key] = [self._add_no_additional_properties(s) for s in value]

        return schema

    def post_execute(
        self, request: ExecutionRequest[JsonSchemaValidatorNode], output: Envelope
    ) -> Envelope:
        """Phase 5: Now emits output as tokens to trigger downstream nodes."""
        self.emit_token_outputs(request, output)

        debug = request.get_handler_state("debug")
        strict_mode = request.get_handler_state("strict_mode")
        if debug:
            if not output.has_error():
                print(
                    f"[JsonSchemaValidatorNode] Validation complete - Valid: True, Strict: {strict_mode}"
                )
            else:
                try:
                    metadata = output.get_metadata_dict()
                    errors = metadata.get("errors", [])
                    if errors:
                        print(f"[JsonSchemaValidatorNode] Validation errors: {len(errors)}")
                        for error in errors[:3]:
                            print(f"  - {error}")
                        if len(errors) > 3:
                            print(f"  ... and {len(errors) - 3} more errors")
                except Exception:
                    pass

        return output
