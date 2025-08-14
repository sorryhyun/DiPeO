import os
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Any

from pydantic import BaseModel
from dipeo.domain.ports.storage import FileSystemPort

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
from dipeo.diagram_generated.generated_nodes import JsonSchemaValidatorNode, NodeType
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.json_schema_validator_model import JsonSchemaValidatorNodeData

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext


@register_handler
class JsonSchemaValidatorNodeHandler(TypedNodeHandler[JsonSchemaValidatorNode]):
    """Handler for JSON Schema validation.
    
    Now uses envelope-based communication for clean input/output interfaces.
    """
    
    # Enable envelope mode
    _expects_envelopes = True
    
    def __init__(self, filesystem_adapter: Optional[FileSystemPort] = None):
        super().__init__()
        self._validator = None
        self.filesystem_adapter = filesystem_adapter
        # Instance variables for passing data between methods
        self._current_strict_mode = None
        self._current_error_on_extra = None
        self._current_schema_path = None
        self._current_debug = None
    
    @property
    def node_class(self) -> type[JsonSchemaValidatorNode]:
        return JsonSchemaValidatorNode
    
    @property
    def node_type(self) -> str:
        return NodeType.JSON_SCHEMA_VALIDATOR.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return JsonSchemaValidatorNodeData
    
    @property
    def requires_services(self) -> list[str]:
        return ["filesystem_adapter"]
    
    @property
    def description(self) -> str:
        return "Validates JSON data against a JSON Schema specification"
    
    def validate(self, request: ExecutionRequest[JsonSchemaValidatorNode]) -> Optional[str]:
        """Static validation - structural checks only"""
        node = request.node
        if not node.schema_path and not node.json_schema:
            return "Either schema_path or json_schema must be provided"
        
        return None
    
    async def pre_execute(self, request: ExecutionRequest[JsonSchemaValidatorNode]) -> Optional[Envelope]:
        """Runtime validation and setup"""
        node = request.node
        services = request.services
        
        # Extract configuration
        self._current_strict_mode = node.strict_mode or False
        self._current_error_on_extra = node.error_on_extra or False
        self._current_schema_path = node.schema_path
        self._current_debug = False  # Will be set based on context if needed
        
        # Check filesystem adapter availability
        filesystem_adapter = self.filesystem_adapter or services.resolve(FILESYSTEM_ADAPTER)
        if not filesystem_adapter:
            return EnvelopeFactory.error(
                "Filesystem adapter is required for JSON schema validation",
                error_type="RuntimeError",
                produced_by=str(node.id)
            )
        
        return None
    
    async def execute_with_envelopes(
        self, 
        request: ExecutionRequest[JsonSchemaValidatorNode],
        inputs: dict[str, Envelope]
    ) -> Envelope:
        """Execute JSON schema validation with envelope inputs."""
        node = request.node
        services = request.services
        trace_id = request.execution_id or ""
        
        filesystem_adapter = self.filesystem_adapter or services.resolve(FILESYSTEM_ADAPTER)
        
        try:
            if node.json_schema:
                schema = node.json_schema
            else:
                schema_path = Path(node.schema_path)
                if not schema_path.is_absolute():
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    schema_path = Path(base_dir) / node.schema_path
                
                if not filesystem_adapter.exists(schema_path):
                    return EnvelopeFactory.error(
                        f"Schema file not found: {node.schema_path}",
                        error_type="ValueError",
                        produced_by=str(node.id)
                    )
                
                with filesystem_adapter.open(schema_path, 'rb') as f:
                    schema = json.loads(f.read().decode('utf-8'))
            
            # Get data to validate
            data_to_validate = None
            
            # Check if data_path is provided
            if node.data_path:
                data_path = Path(node.data_path)
                if not data_path.is_absolute():
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    data_path = Path(base_dir) / node.data_path
                
                if not filesystem_adapter.exists(data_path):
                    return EnvelopeFactory.error(
                        f"Data file not found: {node.data_path}",
                        error_type="ValueError",
                        produced_by=str(node.id)
                    )
                
                with filesystem_adapter.open(data_path, 'rb') as f:
                    data_to_validate = json.loads(f.read().decode('utf-8'))
            else:
                # Use input data from envelopes
                if not inputs:
                    return EnvelopeFactory.error(
                        "No input data provided and no data_path specified",
                        error_type="ValueError",
                        produced_by=str(node.id)
                    )
                
                # Convert envelope inputs to data
                if len(inputs) == 1:
                    # Single input - use it directly
                    envelope = list(inputs.values())[0]
                    try:
                        data_to_validate = self.reader.as_json(envelope)
                    except ValueError:
                        # Fall back to text
                        data_to_validate = self.reader.as_text(envelope)
                        # Try to parse if it looks like JSON
                        if isinstance(data_to_validate, str) and data_to_validate.strip() and data_to_validate.strip()[0] in '{[':
                            try:
                                data_to_validate = json.loads(data_to_validate)
                            except json.JSONDecodeError:
                                pass
                else:
                    # Multiple inputs - create object from them
                    data_to_validate = {}
                    for key, envelope in inputs.items():
                        try:
                            data_to_validate[key] = self.reader.as_json(envelope)
                        except ValueError:
                            value = self.reader.as_text(envelope)
                            # Try to parse JSON strings
                            if isinstance(value, str) and value.strip() and value.strip()[0] in '{[':
                                try:
                                    data_to_validate[key] = json.loads(value)
                                except json.JSONDecodeError:
                                    data_to_validate[key] = value
                            else:
                                data_to_validate[key] = value
            
            # Perform validation using instance variables
            validation_result = await self._validate_data(
                data_to_validate, 
                schema, 
                strict_mode=self._current_strict_mode,
                error_on_extra=self._current_error_on_extra
            )
            
            if validation_result["valid"]:
                # Log success
                if self._current_debug:
                    print(f"[JsonSchemaValidatorNode] ✓ Validation successful for node {node.id}")
                    if node.data_path:
                        print(f"[JsonSchemaValidatorNode]   - Data file: {node.data_path}")
                    if self._current_schema_path:
                        print(f"[JsonSchemaValidatorNode]   - Schema file: {self._current_schema_path}")
                
                # Create success envelope
                output_envelope = EnvelopeFactory.json(
                    data_to_validate if isinstance(data_to_validate, dict) else {"default": data_to_validate},
                    produced_by=node.id,
                    trace_id=trace_id
                ).with_meta(
                    strict_mode=self._current_strict_mode,
                    message="Validation successful",
                    schema_path=self._current_schema_path,
                    data_path=node.data_path
                )
                
                return output_envelope
            else:
                # Log failure
                if self._current_debug:
                    print(f"[JsonSchemaValidatorNode] ✗ Validation FAILED for node {node.id}")
                    if node.data_path:
                        print(f"[JsonSchemaValidatorNode]   - Data file: {node.data_path}")
                    if self._current_schema_path:
                        print(f"[JsonSchemaValidatorNode]   - Schema file: {self._current_schema_path}")
                    print(f"[JsonSchemaValidatorNode]   - Errors found: {len(validation_result['errors'])}")
                    for i, error in enumerate(validation_result['errors'][:3]):
                        print(f"[JsonSchemaValidatorNode]     {i+1}. {error}")
                    if len(validation_result['errors']) > 3:
                        print(f"[JsonSchemaValidatorNode]     ... and {len(validation_result['errors']) - 3} more errors")
                
                # Return validation errors as error envelope
                error_message = f"Validation failed: {'; '.join(validation_result['errors'])}"
                return EnvelopeFactory.error(
                    error_message,
                    error_type="ValueError",
                    produced_by=str(node.id)
                )
        
        except Exception as e:
            return EnvelopeFactory.error(
                str(e),
                error_type=e.__class__.__name__,
                produced_by=str(node.id)
            )
    
    async def _validate_data(self, data: Any, schema: dict, strict_mode: bool = False, error_on_extra: bool = False) -> dict[str, Any]:
        try:
            import jsonschema
            from jsonschema import validators, Draft7Validator
            
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
                        "errors": [f"{'.'.join(str(p) for p in error.path)}: {error.message}" if error.path else error.message 
                                  for error in errors]
                    }
            else:
                try:
                    validator.validate(data)
                except jsonschema.ValidationError as e:
                    error_path = '.'.join(str(p) for p in e.path) if e.path else "root"
                    return {
                        "valid": False,
                        "errors": [f"{error_path}: {e.message}"]
                    }
            
            return {"valid": True, "errors": []}
            
        except ImportError:
            raise ImportError("jsonschema is not installed. Install it with: pip install jsonschema")
    
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
                elif key in ["allOf", "anyOf", "oneOf"]:
                    if isinstance(value, list):
                        schema[key] = [self._add_no_additional_properties(s) for s in value]
        
        return schema
    
    def post_execute(
        self,
        request: ExecutionRequest[JsonSchemaValidatorNode],
        output: Envelope
    ) -> Envelope:
        # Debug logging without using request.metadata
        if self._current_debug:
            if not output.has_error():
                print(f"[JsonSchemaValidatorNode] Validation complete - Valid: True, Strict: {self._current_strict_mode}")
            else:
                # Try to get errors from metadata
                try:
                    metadata = output.get_metadata_dict()
                    errors = metadata.get("errors", [])
                    if errors:
                        print(f"[JsonSchemaValidatorNode] Validation errors: {len(errors)}")
                        for error in errors[:3]:  # Show first 3 errors
                            print(f"  - {error}")
                        if len(errors) > 3:
                            print(f"  ... and {len(errors) - 3} more errors")
                except:
                    pass
        
        return output