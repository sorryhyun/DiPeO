"""Notion operation validation service using unified validation framework."""

from typing import Any

from dipeo.core.base.exceptions import ValidationError
from dipeo.domain.validators.base_validator import BaseValidator, ValidationResult, ValidationWarning
from dipeo.diagram_generated import NotionOperation


class NotionValidator(BaseValidator):
    """Validates Notion API operations using the unified framework."""
    
    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        """Perform Notion operation validation."""
        if isinstance(target, dict):
            self._validate_notion_operation(target, result)
        else:
            result.add_error(ValidationError("Target must be a Notion operation config dict"))
    
    def _validate_notion_operation(self, config: dict[str, Any], result: ValidationResult) -> None:
        """Validate Notion operation configuration."""
        operation = config.get('operation')
        
        if not operation:
            result.add_error(ValidationError("Operation is required"))
            return
        
        # Validate based on operation type
        if operation == NotionOperation.READ_PAGE:
            self._validate_read_page(config, result)
        elif operation == NotionOperation.CREATE_PAGE:
            self._validate_create_page(config, result)
        elif operation == NotionOperation.UPDATE_PAGE:
            self._validate_update_page(config, result)
        elif operation == NotionOperation.QUERY_DATABASE:
            self._validate_query_database(config, result)
        elif operation == NotionOperation.READ_DATABASE:
            self._validate_read_database(config, result)
        else:
            result.add_error(ValidationError(f"Unknown operation: {operation}"))
    
    def _validate_read_page(self, config: dict[str, Any], result: ValidationResult) -> None:
        """Validate READ_PAGE operation."""
        if not config.get('page_id'):
            result.add_error(ValidationError("page_id is required for READ_PAGE operation"))
    
    def _validate_create_page(self, config: dict[str, Any], result: ValidationResult) -> None:
        """Validate CREATE_PAGE operation."""
        # CREATE_PAGE requires parent and properties from inputs, not config
        # So we just add warnings if they're missing in config
        if not config.get('parent') and not config.get('inputs_will_provide_parent'):
            result.add_warning(ValidationWarning("CREATE_PAGE requires 'parent' in inputs"))
        if not config.get('properties') and not config.get('inputs_will_provide_properties'):
            result.add_warning(ValidationWarning("CREATE_PAGE requires 'properties' in inputs"))
    
    def _validate_update_page(self, config: dict[str, Any], result: ValidationResult) -> None:
        """Validate UPDATE_PAGE operation."""
        if not config.get('page_id'):
            result.add_error(ValidationError("page_id is required for UPDATE_PAGE operation"))
        
        # UPDATE_PAGE requires blocks from inputs
        if not config.get('blocks') and not config.get('inputs_will_provide_blocks'):
            result.add_warning(ValidationWarning("UPDATE_PAGE requires 'blocks' in inputs"))
    
    def _validate_query_database(self, config: dict[str, Any], result: ValidationResult) -> None:
        """Validate QUERY_DATABASE operation."""
        if not config.get('database_id'):
            result.add_error(ValidationError("database_id is required for QUERY_DATABASE operation"))
    
    def _validate_read_database(self, config: dict[str, Any], result: ValidationResult) -> None:
        """Validate READ_DATABASE operation."""
        if not config.get('database_id'):
            result.add_error(ValidationError("database_id is required for READ_DATABASE operation"))
    
    def validate_api_key(self, api_key: str) -> ValidationResult:
        """Validate Notion API key format."""
        result = ValidationResult()
        
        if not api_key:
            result.add_error(ValidationError("API key is required"))
        elif not api_key.startswith(('secret_', 'ntn_')):
            result.add_warning(ValidationWarning("API key doesn't match expected Notion format"))
        
        return result
    
    def validate_operation_config(self, operation: NotionOperation, page_id: str = None, 
                                 database_id: str = None, inputs: dict = None) -> ValidationResult:
        """Convenience method to validate operation with all parameters."""
        config = {
            'operation': operation,
            'page_id': page_id,
            'database_id': database_id
        }
        
        # Add flags if inputs will provide required data
        if inputs:
            if 'parent' in inputs:
                config['inputs_will_provide_parent'] = True
            if 'properties' in inputs:
                config['inputs_will_provide_properties'] = True
            if 'blocks' in inputs:
                config['inputs_will_provide_blocks'] = True
        
        return self.validate(config)