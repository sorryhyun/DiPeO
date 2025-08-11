import os
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Any

from pydantic import BaseModel
from dipeo.domain.ports.storage import FileSystemPort

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.diagram_generated.generated_nodes import JsonSchemaValidatorNode, NodeType
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.json_schema_validator_model import JsonSchemaValidatorNodeData

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext


@register_handler
class JsonSchemaValidatorNodeHandler(TypedNodeHandler[JsonSchemaValidatorNode]):
    
    def __init__(self, filesystem_adapter: Optional[FileSystemPort] = None):
        self._validator = None
        self.filesystem_adapter = filesystem_adapter
    
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
        node = request.node
        if not node.schema_path and not node.json_schema:
            return "Either schema_path or json_schema must be provided"
        
        if node.schema_path:
            schema_path = Path(node.schema_path)
            if not schema_path.is_absolute():
                base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                schema_path = Path(base_dir) / node.schema_path
            
            # Actual file existence check will happen in execute_request()
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[JsonSchemaValidatorNode]) -> NodeOutputProtocol:
        node = request.node
        inputs = request.inputs
        services = request.services
        
        filesystem_adapter = self.filesystem_adapter or services.get("filesystem_adapter")
        if not filesystem_adapter:
            return ErrorOutput(
                value="Filesystem adapter is required for JSON schema validation",
                node_id=node.id,
                error_type="ServiceError"
            )
        
        request.add_metadata("strict_mode", node.strict_mode or False)
        request.add_metadata("error_on_extra", node.error_on_extra or False)
        if node.schema_path:
            request.add_metadata("schema_path", node.schema_path)
        
        try:
            if node.json_schema:
                schema = node.json_schema
            else:
                schema_path = Path(node.schema_path)
                if not schema_path.is_absolute():
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    schema_path = Path(base_dir) / node.schema_path
                
                if not filesystem_adapter.exists(schema_path):
                    return ErrorOutput(
                        value=f"Schema file not found: {node.schema_path}",
                        node_id=node.id,
                        error_type="FileNotFoundError"
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
                    return ErrorOutput(
                        value=f"Data file not found: {node.data_path}",
                        node_id=node.id,
                        error_type="FileNotFoundError"
                    )
                
                with filesystem_adapter.open(data_path, 'rb') as f:
                    data_to_validate = json.loads(f.read().decode('utf-8'))
            else:
                # Use input data
                if not inputs:
                    return ErrorOutput(
                        value="No input data provided and no data_path specified",
                        node_id=node.id,
                        error_type="NoDataError"
                    )
                
                # If there's only one input, use it directly
                if len(inputs) == 1:
                    input_value = list(inputs.values())[0]
                    # Try to parse JSON strings
                    if isinstance(input_value, str) and input_value.strip() and input_value.strip()[0] in '{[':
                        try:
                            data_to_validate = json.loads(input_value)
                        except json.JSONDecodeError:
                            data_to_validate = input_value
                    else:
                        data_to_validate = input_value
                else:
                    # Multiple inputs, use them as object
                    data_to_validate = {}
                    for key, value in inputs.items():
                        # Try to parse JSON strings
                        if isinstance(value, str) and value.strip() and value.strip()[0] in '{[':
                            try:
                                data_to_validate[key] = json.loads(value)
                            except json.JSONDecodeError:
                                data_to_validate[key] = value
                        else:
                            data_to_validate[key] = value
            
            # Perform validation
            validation_result = await self._validate_data(
                data_to_validate, 
                schema, 
                strict_mode=node.strict_mode or False,
                error_on_extra=node.error_on_extra or False
            )
            
            if validation_result["valid"]:
                # Log success
                if request.metadata.get("debug"):
                    print(f"[JsonSchemaValidatorNode] ✓ Validation successful for node {node.id}")
                    if node.data_path:
                        print(f"[JsonSchemaValidatorNode]   - Data file: {node.data_path}")
                    if node.schema_path:
                        print(f"[JsonSchemaValidatorNode]   - Schema file: {node.schema_path}")
                
                return DataOutput(
                    value={"default": data_to_validate},
                    node_id=node.id,
                    metadata=json.dumps({
                        "strict_mode": node.strict_mode or False,
                        "message": "Validation successful",
                        "schema_path": node.schema_path,
                        "data_path": node.data_path
                    })
                )
            else:
                # Log failure
                if request.metadata.get("debug"):
                    print(f"[JsonSchemaValidatorNode] ✗ Validation FAILED for node {node.id}")
                    if node.data_path:
                        print(f"[JsonSchemaValidatorNode]   - Data file: {node.data_path}")
                    if node.schema_path:
                        print(f"[JsonSchemaValidatorNode]   - Schema file: {node.schema_path}")
                    print(f"[JsonSchemaValidatorNode]   - Errors found: {len(validation_result['errors'])}")
                    for i, error in enumerate(validation_result['errors'][:3]):
                        print(f"[JsonSchemaValidatorNode]     {i+1}. {error}")
                    if len(validation_result['errors']) > 3:
                        print(f"[JsonSchemaValidatorNode]     ... and {len(validation_result['errors']) - 3} more errors")
                
                # Return validation errors as ErrorOutput
                error_message = f"Validation failed: {'; '.join(validation_result['errors'])}"
                return ErrorOutput(
                    value=error_message,
                    node_id=node.id,
                    error_type="ValidationError",
                    metadata=json.dumps({
                        "errors": validation_result["errors"],
                        "strict_mode": node.strict_mode or False,
                        "validation_passed": False
                    })
                )
        
        except Exception as e:
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__
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
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        if request.metadata.get("debug"):
            success = output.metadata.get("success", False)
            strict_mode = request.metadata.get("strict_mode", False)
            print(f"[JsonSchemaValidatorNode] Validation complete - Valid: {success}, Strict: {strict_mode}")
            if not success and isinstance(output, ErrorOutput):
                errors = output.metadata.get("errors", [])
                if errors:
                    print(f"[JsonSchemaValidatorNode] Validation errors: {len(errors)}")
                    for error in errors[:3]:  # Show first 3 errors
                        print(f"  - {error}")
                    if len(errors) > 3:
                        print(f"  ... and {len(errors) - 3} more errors")
        
        return output