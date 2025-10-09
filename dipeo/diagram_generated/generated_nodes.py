"""
Compatibility shim for generated_nodes.py
Re-exports from individual files for backward compatibility.
Generated at: 2025-10-09T15:58:08.061981
"""

# Re-export all node classes from individual files

from .unified_nodes.api_job_node import ApiJobNode

from .unified_nodes.code_job_node import CodeJobNode

from .unified_nodes.condition_node import ConditionNode

from .unified_nodes.db_node import DbNode as DBNode

from .unified_nodes.diff_patch_node import DiffPatchNode

from .unified_nodes.endpoint_node import EndpointNode

from .unified_nodes.hook_node import HookNode

from .unified_nodes.integrated_api_node import IntegratedApiNode

from .unified_nodes.ir_builder_node import IrBuilderNode

from .unified_nodes.json_schema_validator_node import JsonSchemaValidatorNode

from .unified_nodes.person_job_node import PersonJobNode

from .unified_nodes.start_node import StartNode

from .unified_nodes.sub_diagram_node import SubDiagramNode

from .unified_nodes.template_job_node import TemplateJobNode

from .unified_nodes.typescript_ast_node import TypescriptAstNode

from .unified_nodes.user_response_node import UserResponseNode


# Re-export NodeType and other enums
from .enums import NodeType, DBBlockSubType

# Re-export base types from domain_models
from .domain_models import (
    NodeID,
    Vec2,
    HandleID,
    DomainNode,
    DomainArrow,
    DomainHandle,
)

from typing import Dict, Any, Optional, Union

def create_executable_node(
    node_type: NodeType,
    node_id: NodeID,
    position: Vec2,
    label: str = "",
    data: Optional[Dict[str, Any]] = None,
    flipped: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> 'ExecutableNode':
    """Factory function to create typed executable nodes from diagram data."""
    data = data or {}

    
    if node_type == NodeType.API_JOB:
        return ApiJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            url=data.get('url', ''),
            
            method=data.get('method', 'GET'),
            
            headers=data.get('headers'),
            
            params=data.get('params'),
            
            body=data.get('body'),
            
            auth_type=data.get('auth_type'),
            
            auth_config=data.get('auth_config'),
            
        )
    
    elif node_type == NodeType.CODE_JOB:
        return CodeJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            file_path=data.get('file_path', ''),
            language=data.get('language', 'python'),
            
            code=data.get('code'),
            
            function_name=data.get('functionName', data.get('function_name', '')),
            
        )
    
    elif node_type == NodeType.CONDITION:
        return ConditionNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            condition_type=data.get('condition_type'),
            
            expression=data.get('expression', data.get('condition', '')),
            
            person=data.get('person'),
            
            judge_by=data.get('judge_by'),
            
            judge_by_file=data.get('judge_by_file'),
            
            memorize_to=data.get('memorize_to', 'GOLDFISH'),
            
            at_most=data.get('at_most'),
            
            expose_index_as=data.get('expose_index_as'),
            
        )
    
    elif node_type == NodeType.DB:
        return DBNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            file=data.get('file'),
            
            collection=data.get('collection'),
            
            sub_type=data.get('sub_type', 'fixed_prompt'),
            
            operation=data.get('operation', 'read'),
            
            query=data.get('query'),
            
            keys=data.get('keys'),
            
            lines=data.get('lines'),
            
            data=data.get('data'),
            
            format=data.get('format', 'json'),
            
        )
    
    elif node_type == NodeType.DIFF_PATCH:
        return DiffPatchNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            target_path=data.get('target_path'),
            
            diff=data.get('diff'),
            
            format=data.get('format', 'unified'),
            
            apply_mode=data.get('apply_mode', 'normal'),
            
            backup_dir=data.get('backup_dir'),
            
            strip_level=data.get('strip_level', 1),
            
            fuzz_factor=data.get('fuzz_factor', 2),
            
            reject_file=data.get('reject_file'),
            
        )
    
    elif node_type == NodeType.ENDPOINT:
        return EndpointNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            file_name=data.get('file_name'),
            
        )
    
    elif node_type == NodeType.HOOK:
        return HookNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            hook_type=data.get('hook_type', 'shell'),
            
            command=data.get('command'),
            
            timeout=data.get('timeout', 60),
            
            retry_count=data.get('retry_count', 0),
            
        )
    
    elif node_type == NodeType.INTEGRATED_API:
        return IntegratedApiNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            provider=data.get('provider', 'NOTION'),
            
            operation=data.get('operation', ''),
            
            resource_id=data.get('resource_id'),
            
            config=data.get('config'),
            
            timeout=data.get('timeout', 30),
            
            max_retries=data.get('max_retries', 3),
            
        )
    
    elif node_type == NodeType.IR_BUILDER:
        return IrBuilderNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            builder_type=data.get('builder_type'),
            
            source_type=data.get('source_type'),
            
            config_path=data.get('config_path'),
            
            output_format=data.get('output_format'),
            
        )
    
    elif node_type == NodeType.JSON_SCHEMA_VALIDATOR:
        return JsonSchemaValidatorNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            json_schema=data.get('json_schema'),
            
            data_path=data.get('data_path'),
            
        )
    
    elif node_type == NodeType.PERSON_JOB:
        return PersonJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            person=data.get('person'),
            
            first_only_prompt=data.get('first_only_prompt'),
            
            first_prompt_file=data.get('first_prompt_file'),
            
            default_prompt=data.get('default_prompt'),
            
            prompt_file=data.get('prompt_file'),
            
            max_iteration=data.get('max_iteration', 100),
            
            memorize_to=data.get('memorize_to'),
            
            at_most=data.get('at_most'),
            
            ignore_person=data.get('ignore_person'),
            
            tools=data.get('tools'),
            
            text_format=data.get('text_format'),
            
            text_format_file=data.get('text_format_file'),
            
            resolved_prompt=data.get('resolved_prompt'),
            
            resolved_first_prompt=data.get('resolved_first_prompt'),
            
            batch=data.get('batch', False),
            
            batch_input_key=data.get('batch_input_key', 'items'),
            
            batch_parallel=data.get('batch_parallel', True),
            
            max_concurrent=data.get('max_concurrent', 10),
            
        )
    
    elif node_type == NodeType.START:
        return StartNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            trigger_mode=data.get('trigger_mode', 'none'),
            
            custom_data=data.get('custom_data', {}),
            
            output_data_structure=data.get('output_data_structure', {}),
            
            hook_event=data.get('hook_event'),
            
            hook_filters=data.get('hook_filters'),
            
        )
    
    elif node_type == NodeType.SUB_DIAGRAM:
        return SubDiagramNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            diagram_name=data.get('diagram_name'),
            
            diagram_data=data.get('diagram_data'),
            
            input_mapping=data.get('input_mapping'),
            
            output_mapping=data.get('output_mapping'),
            
            timeout=data.get('timeout'),
            ignore_if_sub=data.get('ignore_if_sub', False),
            diagram_format=data.get('diagram_format'),
            
            batch=data.get('batch', False),
            
            batch_input_key=data.get('batch_input_key', 'items'),
            
            batch_parallel=data.get('batch_parallel', True),
            
        )
    
    elif node_type == NodeType.TEMPLATE_JOB:
        return TemplateJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,

            template_path=data.get('template_path'),

            template_content=data.get('template_content'),

            output_path=data.get('output_path'),

            variables=data.get('variables'),

            engine=data.get('engine', 'jinja2'),

            preprocessor=data.get('preprocessor'),

        )
    
    elif node_type == NodeType.TYPESCRIPT_AST:
        return TypescriptAstNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,

            source=data.get('source'),

            extract_patterns=data.get('extract_patterns', ['interface', 'type', 'enum']),

            parse_mode=data.get('parse_mode', 'module'),

            include_jsdoc=data.get('include_jsdoc', False),

            output_format=data.get('output_format', 'standard'),

            batch=data.get('batch', False),

            batch_input_key=data.get('batch_input_key', 'sources'),

        )
    
    elif node_type == NodeType.USER_RESPONSE:
        return UserResponseNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            
            prompt=data.get('prompt', ''),
            
        )
    
    else:
        raise ValueError(f"Unknown node type: {node_type}")

# Union type for all executable node types

ExecutableNode = Union[
    
    ApiJobNode,
    
    CodeJobNode,
    
    ConditionNode,
    
    DBNode,
    
    DiffPatchNode,
    
    EndpointNode,
    
    HookNode,
    
    IntegratedApiNode,
    
    IrBuilderNode,
    
    JsonSchemaValidatorNode,
    
    PersonJobNode,
    
    StartNode,
    
    SubDiagramNode,
    
    TemplateJobNode,
    
    TypescriptAstNode,
    
    UserResponseNode,
    
]


# Additional exports for backward compatibility
__all__ = [
    
    "ApiJobNode",
    
    "CodeJobNode",
    
    "ConditionNode",
    
    "DBNode",
    
    "DiffPatchNode",
    
    "EndpointNode",
    
    "HookNode",
    
    "IntegratedApiNode",
    
    "IrBuilderNode",
    
    "JsonSchemaValidatorNode",
    
    "PersonJobNode",
    
    "StartNode",
    
    "SubDiagramNode",
    
    "TemplateJobNode",
    
    "TypescriptAstNode",
    
    "UserResponseNode",
    
    "NodeType",
    "DBBlockSubType",
    "create_executable_node",
    "ExecutableNode",
]
