"""
Executors for different node types in the unified execution engine.
"""
from typing import Dict, Optional

from .base_executor import BaseExecutor, ValidationResult, ExecutorResult
from .start_executor import StartExecutor
from .condition_executor import ConditionExecutor
from .job_executor import JobExecutor
from .endpoint_executor import EndpointExecutor
from .person_job_executor import PersonJobExecutor, PersonBatchJobExecutor
from .db_executor import DBExecutor
from .utils import (
    get_input_values,
    substitute_variables,
    validate_required_properties,
    validate_property_types,
    has_incoming_connection,
    has_outgoing_connection,
    get_upstream_nodes,
    get_downstream_nodes,
    check_api_keys,
    validate_required_fields,
    validate_enum_field,
    validate_positive_integer,
    validate_file_path,
    validate_either_required,
    validate_json_field,
    validate_dangerous_code,
    merge_validation_results,
)


def create_executors(llm_service=None, file_service=None) -> Dict[str, BaseExecutor]:
    """
    Create executor instances based on available services.
    
    Args:
        llm_service: LLMService instance for LLM-based executors
        file_service: FileService instance for file operations
        
    Returns:
        Dictionary mapping node types to executor instances
    """
    executors = {
        "start": StartExecutor(),
        "condition": ConditionExecutor(),
        "job": JobExecutor(),
        "endpoint": EndpointExecutor(file_service),
    }
    
    # Add LLM-based executors if service is available
    if llm_service:
        person_job_executor = PersonJobExecutor(llm_service)
        person_batch_job_executor = PersonBatchJobExecutor(llm_service)
        
        executors.update({
            "personjob": person_job_executor,
            "person_job": person_job_executor,
            "personbatchjob": person_batch_job_executor,
            "person_batch_job": person_batch_job_executor,
        })
    
    # Add file-based executors if service is available
    if file_service:
        executors["db"] = DBExecutor(file_service)
    
    return executors


__all__ = [
    "BaseExecutor",
    "ValidationResult",
    "ExecutorResult",
    "StartExecutor",
    "ConditionExecutor",
    "JobExecutor",
    "EndpointExecutor",
    "PersonJobExecutor",
    "PersonBatchJobExecutor",
    "DBExecutor",
    "create_executors",
    # Utility functions
    "get_input_values",
    "substitute_variables",
    "validate_required_properties",
    "validate_property_types",
    "has_incoming_connection",
    "has_outgoing_connection",
    "get_upstream_nodes",
    "get_downstream_nodes",
    "check_api_keys",
    "validate_required_fields",
    "validate_enum_field", 
    "validate_positive_integer",
    "validate_file_path",
    "validate_either_required",
    "validate_json_field",
    "validate_dangerous_code",
    "merge_validation_results",
]