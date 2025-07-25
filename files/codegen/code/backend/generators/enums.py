"""Pure generator for enum definitions."""
from typing import Dict, Any, List
from files.codegen.code.shared.template_env import create_template_env
import json
import os


def generate_enums(template_content: str) -> str:
    """
    Pure function: Generate enum definitions.
    
    Args:
        template_content: Jinja2 template content
        
    Returns:
        Generated Python enum code
    """
    env = create_template_env()
    
    # Define all enums with their values
    enums = [
        {
            'name': 'NodeType',
            'description': 'Types of nodes available in DiPeO diagrams',
            'values': [
                {'name': 'start', 'value': 'start'},
                {'name': 'person_job', 'value': 'person_job'},
                {'name': 'condition', 'value': 'condition'},
                {'name': 'code_job', 'value': 'code_job'},
                {'name': 'api_job', 'value': 'api_job'},
                {'name': 'endpoint', 'value': 'endpoint'},
                {'name': 'db', 'value': 'db'},
                {'name': 'user_response', 'value': 'user_response'},
                {'name': 'notion', 'value': 'notion'},
                {'name': 'person_batch_job', 'value': 'person_batch_job'},
                {'name': 'hook', 'value': 'hook'},
                {'name': 'template_job', 'value': 'template_job'},
                {'name': 'json_schema_validator', 'value': 'json_schema_validator'},
                {'name': 'typescript_ast', 'value': 'typescript_ast'},
                {'name': 'sub_diagram', 'value': 'sub_diagram'},
            ]
        },
        {
            'name': 'HandleDirection',
            'description': 'Direction of node handles',
            'values': [
                {'name': 'input', 'value': 'input'},
                {'name': 'output', 'value': 'output'},
            ]
        },
        {
            'name': 'HandleLabel',
            'description': 'Labels for node handles',
            'values': [
                {'name': 'default', 'value': 'default'},
                {'name': 'first', 'value': 'first'},
                {'name': 'condtrue', 'value': 'condtrue'},
                {'name': 'condfalse', 'value': 'condfalse'},
                {'name': 'success', 'value': 'success'},
                {'name': 'error', 'value': 'error'},
                {'name': 'results', 'value': 'results'},
            ]
        },
        {
            'name': 'DataType',
            'description': 'Data types for node inputs/outputs',
            'values': [
                {'name': 'any', 'value': 'any'},
                {'name': 'string', 'value': 'string'},
                {'name': 'number', 'value': 'number'},
                {'name': 'boolean', 'value': 'boolean'},
                {'name': 'object', 'value': 'object'},
                {'name': 'array', 'value': 'array'},
            ]
        },
        {
            'name': 'ForgettingMode',
            'description': 'Memory forgetting modes',
            'values': [
                {'name': 'no_forget', 'value': 'no_forget'},
                {'name': 'on_every_turn', 'value': 'on_every_turn'},
                {'name': 'upon_request', 'value': 'upon_request'},
            ]
        },
        {
            'name': 'MemoryView',
            'description': 'Different views of conversation memory',
            'values': [
                {'name': 'all_involved', 'value': 'all_involved'},
                {'name': 'sent_by_me', 'value': 'sent_by_me'},
                {'name': 'sent_to_me', 'value': 'sent_to_me'},
                {'name': 'system_and_me', 'value': 'system_and_me'},
                {'name': 'conversation_pairs', 'value': 'conversation_pairs'},
                {'name': 'all_messages', 'value': 'all_messages'},
            ]
        },
        {
            'name': 'DiagramFormat',
            'description': 'Diagram file formats',
            'values': [
                {'name': 'native', 'value': 'native'},
                {'name': 'light', 'value': 'light'},
                {'name': 'readable', 'value': 'readable'},
            ]
        },
        {
            'name': 'DBBlockSubType',
            'description': 'Sub-types for DB blocks',
            'values': [
                {'name': 'fixed_prompt', 'value': 'fixed_prompt'},
                {'name': 'file', 'value': 'file'},
                {'name': 'code', 'value': 'code'},
                {'name': 'api_tool', 'value': 'api_tool'},
            ]
        },
        {
            'name': 'ContentType',
            'description': 'Types of content',
            'values': [
                {'name': 'raw_text', 'value': 'raw_text'},
                {'name': 'conversation_state', 'value': 'conversation_state'},
                {'name': 'object', 'value': 'object'},
            ]
        },
        {
            'name': 'SupportedLanguage',
            'description': 'Supported programming languages',
            'values': [
                {'name': 'python', 'value': 'python'},
                {'name': 'typescript', 'value': 'typescript'},
                {'name': 'bash', 'value': 'bash'},
                {'name': 'shell', 'value': 'shell'},
            ]
        },
        {
            'name': 'HttpMethod',
            'description': 'HTTP request methods',
            'values': [
                {'name': 'GET', 'value': 'GET'},
                {'name': 'POST', 'value': 'POST'},
                {'name': 'PUT', 'value': 'PUT'},
                {'name': 'DELETE', 'value': 'DELETE'},
                {'name': 'PATCH', 'value': 'PATCH'},
            ]
        },
        {
            'name': 'HookType',
            'description': 'Types of hooks',
            'values': [
                {'name': 'shell', 'value': 'shell'},
                {'name': 'webhook', 'value': 'webhook'},
                {'name': 'python', 'value': 'python'},
                {'name': 'file', 'value': 'file'},
            ]
        },
        {
            'name': 'HookTriggerMode',
            'description': 'Hook trigger modes',
            'values': [
                {'name': 'manual', 'value': 'manual'},
                {'name': 'hook', 'value': 'hook'},
            ]
        },
        {
            'name': 'ExecutionStatus',
            'description': 'Execution status values',
            'values': [
                {'name': 'PENDING', 'value': 'PENDING'},
                {'name': 'RUNNING', 'value': 'RUNNING'},
                {'name': 'PAUSED', 'value': 'PAUSED'},
                {'name': 'COMPLETED', 'value': 'COMPLETED'},
                {'name': 'FAILED', 'value': 'FAILED'},
                {'name': 'ABORTED', 'value': 'ABORTED'},
                {'name': 'SKIPPED', 'value': 'SKIPPED'},
            ]
        },
        {
            'name': 'NodeExecutionStatus',
            'description': 'Node execution status values',
            'values': [
                {'name': 'PENDING', 'value': 'PENDING'},
                {'name': 'RUNNING', 'value': 'RUNNING'},
                {'name': 'PAUSED', 'value': 'PAUSED'},
                {'name': 'COMPLETED', 'value': 'COMPLETED'},
                {'name': 'FAILED', 'value': 'FAILED'},
                {'name': 'ABORTED', 'value': 'ABORTED'},
                {'name': 'SKIPPED', 'value': 'SKIPPED'},
                {'name': 'MAXITER_REACHED', 'value': 'MAXITER_REACHED'},
            ]
        },
        {
            'name': 'EventType',
            'description': 'Execution event types',
            'values': [
                {'name': 'EXECUTION_STATUS_CHANGED', 'value': 'EXECUTION_STATUS_CHANGED'},
                {'name': 'NODE_STATUS_CHANGED', 'value': 'NODE_STATUS_CHANGED'},
                {'name': 'NODE_PROGRESS', 'value': 'NODE_PROGRESS'},
                {'name': 'INTERACTIVE_PROMPT', 'value': 'INTERACTIVE_PROMPT'},
                {'name': 'INTERACTIVE_RESPONSE', 'value': 'INTERACTIVE_RESPONSE'},
                {'name': 'EXECUTION_ERROR', 'value': 'EXECUTION_ERROR'},
                {'name': 'EXECUTION_UPDATE', 'value': 'EXECUTION_UPDATE'},
            ]
        },
        {
            'name': 'LLMService',
            'description': 'LLM service providers',
            'values': [
                {'name': 'openai', 'value': 'openai'},
                {'name': 'anthropic', 'value': 'anthropic'},
                {'name': 'google', 'value': 'google'},
                {'name': 'bedrock', 'value': 'bedrock'},
                {'name': 'vertex', 'value': 'vertex'},
                {'name': 'deepseek', 'value': 'deepseek'},
            ]
        },
        {
            'name': 'APIServiceType',
            'description': 'All API service types including LLMs',
            'values': [
                {'name': 'openai', 'value': 'openai'},
                {'name': 'anthropic', 'value': 'anthropic'},
                {'name': 'google', 'value': 'google'},
                {'name': 'gemini', 'value': 'gemini'},
                {'name': 'bedrock', 'value': 'bedrock'},
                {'name': 'vertex', 'value': 'vertex'},
                {'name': 'deepseek', 'value': 'deepseek'},
                {'name': 'notion', 'value': 'notion'},
                {'name': 'google_search', 'value': 'google_search'},
                {'name': 'slack', 'value': 'slack'},
                {'name': 'github', 'value': 'github'},
                {'name': 'jira', 'value': 'jira'},
            ]
        },
        {
            'name': 'NotionOperation',
            'description': 'Notion API operations',
            'values': [
                {'name': 'create_page', 'value': 'create_page'},
                {'name': 'update_page', 'value': 'update_page'},
                {'name': 'read_page', 'value': 'read_page'},
                {'name': 'delete_page', 'value': 'delete_page'},
                {'name': 'create_database', 'value': 'create_database'},
                {'name': 'query_database', 'value': 'query_database'},
                {'name': 'update_database', 'value': 'update_database'},
            ]
        },
        {
            'name': 'ToolType',
            'description': 'Tool types for LLM agents',
            'values': [
                {'name': 'web_search', 'value': 'web_search'},
                {'name': 'web_search_preview', 'value': 'web_search_preview'},
                {'name': 'image_generation', 'value': 'image_generation'},
            ]
        },
    ]
    
    # Render template
    template = env.from_string(template_content)
    return template.render(enums=enums)


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for code_job node.
    
    Args:
        inputs: Dictionary containing:
            - template_content: Template string
            
    Returns:
        Dictionary with:
            - generated_code: The generated enums code
            - filename: Output filename
    """
    template_content = inputs.get('template_content', '')
    
    if not template_content:
        raise ValueError("template_content is required")
    
    generated_code = generate_enums(template_content)
    
    return {
        'generated_code': generated_code,
        'filename': 'enums.py'
    }