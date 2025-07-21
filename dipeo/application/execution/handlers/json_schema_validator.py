import os
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.core.static.generated_nodes import JsonSchemaValidatorNode
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol
from dipeo.models import JsonSchemaValidatorNodeData, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class JsonSchemaValidatorNodeHandler(TypedNodeHandler[JsonSchemaValidatorNode]):
    
    def __init__(self):
        self._validator = None  # Lazy load jsonschema
    
    @property
    def node_class(self) -> type[JsonSchemaValidatorNode]:
        return JsonSchemaValidatorNode
    
    @property
    def node_type(self) -> str:
        return NodeType.json_schema_validator.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return JsonSchemaValidatorNodeData
    
    @property
    def requires_services(self) -> list[str]:
        return []
    
    @property
    def description(self) -> str:
        return "Validates JSON data against a JSON Schema specification"
    
    def validate(self, request: ExecutionRequest[JsonSchemaValidatorNode]) -> Optional[str]:
        """Validate the JSON schema validator configuration."""
        node = request.node
        
        # Must have either schema_path or schema
        if not node.schema_path and not node.schema:
            return "Either schema_path or schema must be provided"
        
        # If schema_path is provided, validate it exists
        if node.schema_path:
            schema_path = Path(node.schema_path)
            if not schema_path.is_absolute():
                base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                schema_path = Path(base_dir) / node.schema_path
            
            if not schema_path.exists():
                return f"Schema file not found: {node.schema_path}"
            
            if not schema_path.is_file():
                return f"Schema path is not a file: {node.schema_path}"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[JsonSchemaValidatorNode]) -> NodeOutputProtocol:
        """Execute the JSON schema validation."""
        node = request.node
        inputs = request.inputs
        
        # Store execution metadata
        request.add_metadata("strict_mode", node.strict_mode or False)
        request.add_metadata("error_on_extra", node.error_on_extra or False)
        if node.schema_path:
            request.add_metadata("schema_path", node.schema_path)
        
        try:
            # Get schema
            if node.schema:
                schema = node.schema
            else:
                # Load from file
                schema_path = Path(node.schema_path)
                if not schema_path.is_absolute():
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    schema_path = Path(base_dir) / node.schema_path
                
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
            
            # Get data to validate
            data_to_validate = None
            
            # Check if data_path is provided
            if node.data_path:
                data_path = Path(node.data_path)
                if not data_path.is_absolute():
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    data_path = Path(base_dir) / node.data_path
                
                if not data_path.exists():
                    return ErrorOutput(
                        value=f"Data file not found: {node.data_path}",
                        node_id=node.id,
                        error_type="FileNotFoundError"
                    )
                
                with open(data_path, 'r', encoding='utf-8') as f:
                    data_to_validate = json.load(f)
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
                    value={
                        "default": {
                            "valid": True,
                            "data": data_to_validate,
                            "message": "Validation successful",
                            "schema_path": node.schema_path,
                            "data_path": node.data_path
                        }
                    },
                    node_id=node.id,
                    metadata={
                        "success": True,
                        "strict_mode": node.strict_mode or False,
                        "validation_passed": True
                    }
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
                    metadata={
                        "errors": validation_result["errors"],
                        "strict_mode": node.strict_mode or False,
                        "validation_passed": False
                    }
                )
        
        except Exception as e:
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__
            )
    
    async def _validate_data(self, data: Any, schema: dict, strict_mode: bool = False, error_on_extra: bool = False) -> dict[str, Any]:
        """Validate data against schema using jsonschema library."""
        try:
            import jsonschema
            from jsonschema import validators, Draft7Validator
            
            errors = []
            
            # Configure validator based on options
            if error_on_extra:
                # Add additionalProperties: false to all objects in schema if not specified
                schema = self._add_no_additional_properties(schema.copy())
            
            # Create validator
            validator_class = validators.validator_for(schema)
            validator = validator_class(schema)
            
            # Validate
            if strict_mode:
                # In strict mode, collect all errors
                errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
                if errors:
                    return {
                        "valid": False,
                        "errors": [f"{'.'.join(str(p) for p in error.path)}: {error.message}" if error.path else error.message 
                                  for error in errors]
                    }
            else:
                # In normal mode, just check if valid
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
        """Recursively add additionalProperties: false to all objects in schema."""
        if isinstance(schema, dict):
            if schema.get("type") == "object" and "additionalProperties" not in schema:
                schema["additionalProperties"] = False
            
            # Recurse into nested schemas
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
        """Post-execution hook to log validation details."""
        # Log execution details if in debug mode
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