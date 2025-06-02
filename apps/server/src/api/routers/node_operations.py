"""
Node Operations API - Specific endpoints for server-only node operations.

These endpoints handle individual node operations that require server-side execution:
- PersonJob LLM calls
- DB file operations  
- File saving operations

The frontend execution engine calls these endpoints when it encounters server-only nodes.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional

from ...services.llm_service import LLMService
from ...services.unified_file_service import UnifiedFileService
from ...services.api_key_service import APIKeyService
from ...utils.dependencies import get_llm_service, get_unified_file_service, get_api_key_service
from ...core import handle_api_errors
from ...exceptions import ValidationError, LLMServiceError, FileOperationError

router = APIRouter(prefix="/api/nodes", tags=["node-operations"])


@router.post("/personjob/execute")
@handle_api_errors
async def execute_person_job(
    payload: Dict[str, Any],
    llm_service: LLMService = Depends(get_llm_service)
):
    """Execute a PersonJob node - make LLM call with person configuration."""
    
    # Extract required fields
    person_config = payload.get('person', {})
    prompt = payload.get('prompt', '')
    inputs = payload.get('inputs', {})
    node_config = payload.get('node_config', {})
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[execute_person_job] Received payload: {payload}")
    logger.info(f"[execute_person_job] Extracted inputs: {inputs}")
    logger.info(f"[execute_person_job] Original prompt: {prompt}")
    
    if not person_config:
        raise ValidationError("Person configuration is required")
    
    if not prompt:
        raise ValidationError("Prompt is required")
    
    # Get person details
    service = person_config.get('service', 'openai')
    model = person_config.get('modelName') or person_config.get('model')
    api_key_id = person_config.get('apiKeyId')
    system_prompt = person_config.get('systemPrompt', '')
    person_id = person_config.get('id')
    
    if not api_key_id:
        raise ValidationError("API key ID is required")
    
    if not model:
        raise ValidationError("Model name is required")
    
    # Substitute variables in prompt
    final_prompt = _substitute_variables(prompt, inputs)
    
    try:
        # Make LLM call
        response = await llm_service.call_llm(
            service=service,
            api_key_id=api_key_id,
            model=model,
            messages=final_prompt,
            system_prompt=system_prompt
        )
        
        return {
            "success": True,
            "output": response["response"],
            "cost": response["cost"],
            "metadata": {
                "person_id": person_id,
                "service": service,
                "model": model,
                "prompt_length": len(final_prompt),
                "system_prompt_length": len(system_prompt)
            }
        }
        
    except Exception as e:
        raise LLMServiceError(f"LLM call failed: {str(e)}")


@router.post("/db/execute")
@handle_api_errors
async def execute_db_node(
    payload: Dict[str, Any],
    file_service: UnifiedFileService = Depends(get_unified_file_service)
):
    """Execute a DB node - read file or return fixed content."""
    
    sub_type = payload.get('sub_type', 'file')
    source_details = payload.get('source_details', '')
    
    if not source_details:
        raise ValidationError("Source details are required")
    
    if sub_type == 'file':
        try:
            # Read file content
            content = file_service.read(source_details, relative_to="base")
            return {
                "success": True,
                "output": content,
                "metadata": {
                    "source_type": "file",
                    "source_path": source_details,
                    "content_length": len(content)
                }
            }
        except Exception as e:
            raise FileOperationError(f"Failed to read file {source_details}: {str(e)}")
    
    elif sub_type == 'fixed_prompt':
        # Return the source details as the output
        return {
            "success": True,
            "output": source_details,
            "metadata": {
                "source_type": "fixed_prompt",
                "content_length": len(source_details)
            }
        }
    
    elif sub_type == 'api_tool':
        # Handle API tool calls (Notion, etc.)
        try:
            # Parse the API configuration
            import json
            api_config = json.loads(source_details) if isinstance(source_details, str) else source_details
            api_type = api_config.get('apiType', '').lower()
            
            if api_type == 'notion':
                # Handle Notion API calls
                return await _execute_notion_api(api_config)
            else:
                raise ValidationError(f"Unsupported API type: {api_type}")
                
        except json.JSONDecodeError:
            raise ValidationError("Invalid API configuration JSON")
        except Exception as e:
            raise ValidationError(f"API call failed: {str(e)}")
    
    else:
        raise ValidationError(f"Unsupported DB node sub_type: {sub_type}")


@router.post("/endpoint/execute")
@handle_api_errors
async def execute_endpoint_node(
    payload: Dict[str, Any],
    file_service: UnifiedFileService = Depends(get_unified_file_service)
):
    """Execute an Endpoint node - save content to file if specified."""
    
    content = payload.get('content', '')
    save_to_file = payload.get('save_to_file', False)
    file_path = payload.get('file_path', '')
    file_format = payload.get('file_format', 'text')
    
    result = {
        "success": True,
        "output": content,
        "file_saved": False
    }
    
    if save_to_file and file_path:
        try:
            # Save content to file
            saved_path = await file_service.write(
                file_path, 
                content, 
                relative_to="base", 
                format=file_format
            )
            
            result.update({
                "file_saved": True,
                "file_path": saved_path,
                "file_format": file_format,
                "metadata": {
                    "content_length": len(content),
                    "saved_at": saved_path
                }
            })
            
        except Exception as e:
            raise FileOperationError(f"Failed to save file {file_path}: {str(e)}")
    
    return result


@router.post("/code/execute")
@handle_api_errors
async def execute_code_node(
    payload: Dict[str, Any]
):
    """Execute a Code node - run Python code safely."""
    
    code = payload.get('code', '')
    inputs = payload.get('inputs', [])
    
    if not code:
        raise ValidationError("Code is required")
    
    try:
        # Create a safe execution environment
        safe_globals = {
            '__builtins__': {
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'bool': bool,
                'min': min,
                'max': max,
                'sum': sum,
                'sorted': sorted,
                'enumerate': enumerate,
                'zip': zip,
                'range': range,
                'print': print,
            },
            'json': __import__('json'),
            'datetime': __import__('datetime'),
            're': __import__('re'),
            'math': __import__('math'),
            'inputs': inputs,
        }
        
        # Execute the code
        local_vars = {}
        exec(code, safe_globals, local_vars)
        
        # Get the return value
        result = local_vars.get('return', '')
        if callable(result):
            result = result()
        
        return {
            "success": True,
            "output": str(result),
            "metadata": {
                "code_length": len(code),
                "inputs_count": len(inputs)
            }
        }
        
    except Exception as e:
        raise ValidationError(f"Code execution failed: {str(e)}")


async def _execute_notion_api(api_config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Notion API calls."""
    action = api_config.get('action', 'search')
    
    if action == 'search':
        query = api_config.get('query', '')
        # Simulate Notion search for now
        return {
            "success": True,
            "output": {
                "results": [
                    {
                        "object": "page",
                        "id": "mock-page-id",
                        "properties": {
                            "title": {
                                "type": "title",
                                "title": [{"text": {"content": f"Mock result for '{query}'"}}]
                            }
                        }
                    }
                ]
            },
            "metadata": {
                "api_type": "notion",
                "action": "search",
                "query": query
            }
        }
    else:
        raise ValidationError(f"Unsupported Notion action: {action}")


def _substitute_variables(template: str, variables: Dict[str, Any]) -> str:
    """Substitute variables in template string."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[_substitute_variables] Starting substitution")
    logger.info(f"[_substitute_variables] Template: {template}")
    logger.info(f"[_substitute_variables] Variables: {variables}")
    
    result = template
    for key, value in variables.items():
        # Handle both {{key}} and {key} patterns
        old_result = result
        result = result.replace(f"{{{{{key}}}}}", str(value))
        result = result.replace(f"{{{key}}}", str(value))
        
        if old_result != result:
            logger.info(f"[_substitute_variables] Replaced '{key}' with '{value}'")
    
    logger.info(f"[_substitute_variables] Final result: {result}")
    return result