"""
Backend Execution Service - Handles server-only node execution.

This service processes PersonJob, DB, and other server-only nodes that require:
- LLM API calls with secure API key access
- File system operations
- Memory/conversation management
- Cost tracking and usage analytics
"""

import json
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from ..constants import NodeType, LLMService as LLMServiceEnum
from ..exceptions import ValidationError, LLMServiceError, FileOperationError
from .llm_service import LLMService
from .memory_service import MemoryService
from .unified_file_service import UnifiedFileService
from ..utils.base_service import BaseService


class ExecutionService(BaseService):
    """Service for executing server-only diagram nodes."""
    
    def __init__(self, llm_service: LLMService, memory_service: MemoryService, file_service: UnifiedFileService):
        super().__init__()
        self.llm_service = llm_service
        self.memory_service = memory_service
        self.file_service = file_service
        self.execution_cache = {}  # Cache for execution contexts
    
    async def execute_diagram(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a diagram, handling server-only nodes."""
        execution_id = str(uuid.uuid4())
        
        try:
            # Validate diagram structure
            self._validate_diagram(diagram)
            
            # Create execution context
            context = self._create_execution_context(execution_id, diagram)
            
            # Get server-only nodes
            server_nodes = self._filter_server_nodes(diagram.get('nodes', []))
            
            if not server_nodes:
                return {
                    "success": True,
                    "execution_id": execution_id,
                    "context": context,
                    "total_cost": 0,
                    "message": "No server-only nodes to execute"
                }
            
            # Execute nodes
            total_cost = 0
            results = {}
            
            for node in server_nodes:
                try:
                    result = await self._execute_node(node, context, diagram)
                    results[node['id']] = result
                    total_cost += result.get('cost', 0)
                    
                    # Update context with node output
                    context['node_outputs'][node['id']] = result.get('output')
                    
                except Exception as e:
                    error_msg = f"Failed to execute node {node['id']}: {str(e)}"
                    results[node['id']] = {"error": error_msg}
                    context['errors'][node['id']] = error_msg
            
            return {
                "success": True,
                "execution_id": execution_id,
                "context": context,
                "total_cost": total_cost,
                "node_results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "execution_id": execution_id,
                "error": str(e),
                "context": self._create_execution_context(execution_id, diagram)
            }
    
    async def _execute_node(self, node: Dict[str, Any], context: Dict[str, Any], diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single server-only node."""
        node_type = node.get('type')
        node_id = node.get('id')
        
        if node_type == 'personJobNode':
            return await self._execute_person_job_node(node, context, diagram)
        elif node_type == 'personBatchJobNode':
            return await self._execute_person_batch_job_node(node, context, diagram)
        elif node_type == 'dbNode':
            return await self._execute_db_node(node, context, diagram)
        elif node_type == 'endpointNode':
            return await self._execute_endpoint_node(node, context, diagram)
        else:
            raise ValidationError(f"Unsupported server node type: {node_type}")
    
    async def _execute_person_job_node(self, node: Dict[str, Any], context: Dict[str, Any], diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a PersonJob node - LLM interaction with memory."""
        node_data = node.get('data', {})
        person_id = node_data.get('personId')
        
        if not person_id:
            raise ValidationError("PersonJob node missing personId")
        
        # Get person configuration
        person = self._get_person_by_id(diagram, person_id)
        if not person:
            raise ValidationError(f"Person {person_id} not found in diagram")
        
        # Get prompts
        default_prompt = node_data.get('defaultPrompt', '')
        first_only_prompt = node_data.get('firstOnlyPrompt', '')
        
        # Determine which prompt to use based on execution state
        is_first_execution = not context.get('first_only_consumed', {}).get(node['id'], False)
        prompt = first_only_prompt if (first_only_prompt and is_first_execution) else default_prompt
        
        if not prompt:
            raise ValidationError("No prompt available for PersonJob node")
        
        # Get input values and substitute variables
        inputs = self._get_node_inputs(node, context)
        final_prompt = self._substitute_variables(prompt, inputs)
        
        # Get system prompt from person
        system_prompt = person.get('systemPrompt', '')
        
        # Make LLM call
        try:
            service = person.get('service', 'openai')
            model = person.get('modelName') or person.get('model')
            api_key_id = person.get('apiKeyId')
            
            if not api_key_id:
                raise ValidationError(f"Person {person_id} missing API key")
            
            response = await self.llm_service.call_llm(
                service=service,
                api_key_id=api_key_id,
                model=model,
                messages=final_prompt,
                system_prompt=system_prompt
            )
            
            # Handle context cleaning rule
            context_rule = node_data.get('contextCleaningRule', 'no_forget')
            if context_rule == 'on_every_turn':
                # Mark first-only as consumed to prevent reuse
                if 'first_only_consumed' not in context:
                    context['first_only_consumed'] = {}
                context['first_only_consumed'][node['id']] = True
            
            return {
                "output": response["response"],
                "cost": response["cost"],
                "person_id": person_id,
                "service": service,
                "model": model,
                "prompt_used": final_prompt,
                "system_prompt": system_prompt,
                "context_rule": context_rule
            }
            
        except Exception as e:
            raise LLMServiceError(f"LLM call failed for person {person_id}: {str(e)}")
    
    async def _execute_person_batch_job_node(self, node: Dict[str, Any], context: Dict[str, Any], diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a PersonBatchJob node - multiple LLM calls."""
        # Similar to PersonJob but handles batch processing
        # For now, delegate to single PersonJob execution
        return await self._execute_person_job_node(node, context, diagram)
    
    async def _execute_db_node(self, node: Dict[str, Any], context: Dict[str, Any], diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a DB node - file/data source operations."""
        node_data = node.get('data', {})
        sub_type = node_data.get('subType', 'file')
        source_details = node_data.get('sourceDetails', '')
        
        if sub_type == 'file':
            try:
                # Read file content
                content = await self.file_service.read(source_details, format="text")
                return {
                    "output": content,
                    "cost": 0,
                    "source_type": "file",
                    "source_path": source_details
                }
            except Exception as e:
                raise FileOperationError(f"Failed to read file {source_details}: {str(e)}")
        
        elif sub_type == 'fixed_prompt':
            # Return the source details as the output
            return {
                "output": source_details,
                "cost": 0,
                "source_type": "fixed_prompt"
            }
        
        else:
            raise ValidationError(f"Unsupported DB node sub_type: {sub_type}")
    
    async def _execute_endpoint_node(self, node: Dict[str, Any], context: Dict[str, Any], diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Endpoint node - save results to file."""
        node_data = node.get('data', {})
        
        # Get input values
        inputs = self._get_node_inputs(node, context)
        input_content = list(inputs.values())[0] if inputs else ""
        
        # Check if file saving is enabled
        save_to_file = node_data.get('saveToFile', False)
        
        if save_to_file:
            file_path = node_data.get('filePath', '')
            file_format = node_data.get('fileFormat', 'text')
            
            if file_path:
                try:
                    # Save content to file
                    saved_path = await self.file_service.write(
                        file_path, 
                        input_content, 
                        relative_to="base", 
                        format=file_format
                    )
                    
                    return {
                        "output": input_content,
                        "cost": 0,
                        "file_saved": True,
                        "file_path": saved_path,
                        "file_format": file_format
                    }
                except Exception as e:
                    raise FileOperationError(f"Failed to save file {file_path}: {str(e)}")
        
        # No file saving, just pass through the input
        return {
            "output": input_content,
            "cost": 0,
            "file_saved": False
        }
    
    def _validate_diagram(self, diagram: Dict[str, Any]) -> None:
        """Validate diagram structure."""
        if not isinstance(diagram, dict):
            raise ValidationError("Diagram must be a dictionary")
        
        if 'nodes' not in diagram:
            raise ValidationError("Diagram must contain 'nodes'")
        
        if not isinstance(diagram['nodes'], list):
            raise ValidationError("Diagram 'nodes' must be a list")
    
    def _create_execution_context(self, execution_id: str, diagram: Dict[str, Any]) -> Dict[str, Any]:
        """Create execution context for tracking state."""
        return {
            "execution_id": execution_id,
            "node_outputs": {},
            "errors": {},
            "first_only_consumed": {},
            "total_cost": 0,
            "execution_order": []
        }
    
    def _filter_server_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter nodes that require server-side execution."""
        server_node_types = {'personJobNode', 'personBatchJobNode', 'dbNode', 'endpointNode'}
        return [node for node in nodes if node.get('type') in server_node_types]
    
    def _get_person_by_id(self, diagram: Dict[str, Any], person_id: str) -> Optional[Dict[str, Any]]:
        """Get person configuration by ID."""
        persons = diagram.get('persons', [])
        
        # Handle both list and dict format
        if isinstance(persons, list):
            return next((p for p in persons if p.get('id') == person_id), None)
        elif isinstance(persons, dict):
            return persons.get(person_id)
        
        return None
    
    def _get_node_inputs(self, node: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get input values for a node from execution context."""
        # This is a simplified implementation
        # In a full implementation, this would trace arrows and get actual input values
        node_outputs = context.get('node_outputs', {})
        
        # For now, return a simple mapping of available outputs
        return {f"input_{i}": output for i, output in enumerate(node_outputs.values())}
    
    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template string."""
        result = template
        for key, value in variables.items():
            # Handle both {{key}} and {key} patterns
            result = result.replace(f"{{{{{key}}}}}", str(value))
            result = result.replace(f"{{{key}}}", str(value))
        return result