"""
Node factory for creating executable nodes from data.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-10-09T15:58:08.061981

"""

from typing import Dict, Any, Optional, Union

from dipeo.diagram_generated.enums import NodeType, DBBlockSubType
from dipeo.diagram_generated.domain_models import NodeID, Vec2

# Import all unified node classes

from dipeo.diagram_generated.unified_nodes.api_job_node import ApiJobNode
from dipeo.diagram_generated.unified_nodes.code_job_node import CodeJobNode
from dipeo.diagram_generated.unified_nodes.condition_node import ConditionNode
from dipeo.diagram_generated.unified_nodes.db_node import DbNode
from dipeo.diagram_generated.unified_nodes.diff_patch_node import DiffPatchNode
from dipeo.diagram_generated.unified_nodes.endpoint_node import EndpointNode
from dipeo.diagram_generated.unified_nodes.hook_node import HookNode
from dipeo.diagram_generated.unified_nodes.integrated_api_node import IntegratedApiNode
from dipeo.diagram_generated.unified_nodes.ir_builder_node import IrBuilderNode
from dipeo.diagram_generated.unified_nodes.json_schema_validator_node import JsonSchemaValidatorNode
from dipeo.diagram_generated.unified_nodes.person_job_node import PersonJobNode
from dipeo.diagram_generated.unified_nodes.start_node import StartNode
from dipeo.diagram_generated.unified_nodes.sub_diagram_node import SubDiagramNode
from dipeo.diagram_generated.unified_nodes.template_job_node import TemplateJobNode
from dipeo.diagram_generated.unified_nodes.typescript_ast_node import TypescriptAstNode
from dipeo.diagram_generated.unified_nodes.user_response_node import UserResponseNode

# Type alias for any executable node
ExecutableNode = Union[
    ApiJobNode, 
    CodeJobNode, 
    ConditionNode, 
    DbNode, 
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
    UserResponseNode
]


def create_executable_node(
    node_type: NodeType,
    node_id: NodeID,
    position: Vec2,
    label: str = "",
    data: Optional[Dict[str, Any]] = None,
    flipped: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> ExecutableNode:
    """Factory function to create typed executable nodes from diagram data."""
    data = data or {}

    # Create the appropriate node based on type

    if node_type == NodeType.API_JOB:
        return ApiJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            url=data.get('url', ""),
            method=data.get('method', "GET"),
            headers=data.get('headers', None),
            params=data.get('params', None),
            body=data.get('body', None),
            auth_type=data.get('auth_type', None),
            auth_config=data.get('auth_config', None),
        )

    elif node_type == NodeType.CODE_JOB:
        return CodeJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            language=data.get('language', "python"),
            code=data.get('code', None),
            # Function name field may have camelCase variants
            function_name=data.get('function_name', data.get('functionName', data.get('function_name', None))),
        )

    elif node_type == NodeType.CONDITION:
        return ConditionNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            condition_type=data.get('condition_type', "custom"),
            expression=data.get('expression', None),
            person=data.get('person', None),
            judge_by=data.get('judge_by', None),
            judge_by_file=data.get('judge_by_file', None),
            memorize_to=data.get('memorize_to', "GOLDFISH"),
            at_most=data.get('at_most', None),
            expose_index_as=data.get('expose_index_as', None),
        )

    elif node_type == NodeType.DB:
        return DbNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            # DB node special handling for backward compatibility
            file=data.get('file', None),
            # DB node special handling for backward compatibility
            collection=data.get('collection', None),
            # Sub type field may have camelCase variants
            sub_type=data.get('sub_type', data.get('subType', "fixed_prompt")),
            operation=data.get('operation', "read"),
            # DB node special handling for backward compatibility
            query=data.get('query', None),
            keys=data.get('keys', None),
            lines=data.get('lines', None),
            # DB node special handling for backward compatibility
            data=data.get('data', None),
            format=data.get('format', "json"),
        )

    elif node_type == NodeType.DIFF_PATCH:
        return DiffPatchNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            target_path=data.get('target_path', None),
            diff=data.get('diff', None),
            format=data.get('format', "unified"),
            apply_mode=data.get('apply_mode', "normal"),
            backup_dir=data.get('backup_dir', None),
            strip_level=data.get('strip_level', 1),
            fuzz_factor=data.get('fuzz_factor', 2),
            reject_file=data.get('reject_file', None),
        )

    elif node_type == NodeType.ENDPOINT:
        return EndpointNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            file_name=data.get('file_name', None),
        )

    elif node_type == NodeType.HOOK:
        return HookNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            hook_type=data.get('hook_type', "shell"),
            command=data.get('command', None),
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
            provider=data.get('provider', "NOTION"),
            operation=data.get('operation', ""),
            resource_id=data.get('resource_id', None),
            config=data.get('config', None),
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
            builder_type=data.get('builder_type', None),
            source_type=data.get('source_type', None),
            config_path=data.get('config_path', None),
            output_format=data.get('output_format', None),
        )

    elif node_type == NodeType.JSON_SCHEMA_VALIDATOR:
        return JsonSchemaValidatorNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            json_schema=data.get('json_schema', None),
            data_path=data.get('data_path', None),
        )

    elif node_type == NodeType.PERSON_JOB:
        return PersonJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            person=data.get('person', None),
            # PersonJob backward compatibility: first_only_prompt could be 'prompt'
            first_only_prompt=data.get('first_only_prompt', data.get('prompt', None)),
            first_prompt_file=data.get('first_prompt_file', None),
            default_prompt=data.get('default_prompt', None),
            prompt_file=data.get('prompt_file', None),
            max_iteration=data.get('max_iteration', 100),
            memorize_to=data.get('memorize_to', None),
            at_most=data.get('at_most', None),
            ignore_person=data.get('ignore_person', None),
            tools=data.get('tools', None),
            text_format=data.get('text_format', None),
            text_format_file=data.get('text_format_file', None),
            resolved_prompt=data.get('resolved_prompt', None),
            resolved_first_prompt=data.get('resolved_first_prompt', None),
            batch=data.get('batch', False),
            batch_input_key=data.get('batch_input_key', "items"),
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
            trigger_mode=data.get('trigger_mode', "none"),
            custom_data=data.get('custom_data', {}),
            output_data_structure=data.get('output_data_structure', {}),
            hook_event=data.get('hook_event', None),
            hook_filters=data.get('hook_filters', None),
        )

    elif node_type == NodeType.SUB_DIAGRAM:
        return SubDiagramNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            diagram_name=data.get('diagram_name', None),
            diagram_data=data.get('diagram_data', None),
            input_mapping=data.get('input_mapping', None),
            output_mapping=data.get('output_mapping', None),
            timeout=data.get('timeout', None),
            diagram_format=data.get('diagram_format', None),
            batch_input_key=data.get('batch_input_key', "items"),
        )

    elif node_type == NodeType.TEMPLATE_JOB:
        return TemplateJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            template_content=data.get('template_content', None),
            variables=data.get('variables', None),
            engine=data.get('engine', "jinja2"),
            preprocessor=data.get('preprocessor', None),
        )

    elif node_type == NodeType.TYPESCRIPT_AST:
        return TypescriptAstNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            source=data.get('source', None),
            extract_patterns=data.get('extract_patterns', ['interface', 'type', 'enum']),
            parse_mode=data.get('parse_mode', "module"),
            output_format=data.get('output_format', "standard"),
            batch_input_key=data.get('batch_input_key', "sources"),
        )

    elif node_type == NodeType.USER_RESPONSE:
        return UserResponseNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            prompt=data.get('prompt', ""),
        )

    else:
        raise ValueError(f"Unknown node type: {node_type}")


# Re-export for backward compatibility
__all__ = [
    'ExecutableNode',
    'create_executable_node',
    'ApiJobNode',
    'CodeJobNode',
    'ConditionNode',
    'DbNode',
    'DiffPatchNode',
    'EndpointNode',
    'HookNode',
    'IntegratedApiNode',
    'IrBuilderNode',
    'JsonSchemaValidatorNode',
    'PersonJobNode',
    'StartNode',
    'SubDiagramNode',
    'TemplateJobNode',
    'TypescriptAstNode',
    'UserResponseNode',
]
