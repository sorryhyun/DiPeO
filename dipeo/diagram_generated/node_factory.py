"""
Node factory for creating executable nodes from data.
Avoid editing THIS FILE DIRECTLY.
Generated at: 2025-09-30T20:02:09.000780

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
            url=data.get('url', None),
            method=data.get('method', None),
            headers=data.get('headers', None),
            params=data.get('params', None),
            body=data.get('body', None),
            timeout=data.get('timeout', None),
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
            language=data.get('language', None),
            file_path=data.get('filePath', None),
            code=data.get('code', None),
            function_name=data.get('functionName', None),
            timeout=data.get('timeout', None),
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
            node_indices=data.get('node_indices', None),
            person=data.get('person', None),
            judge_by=data.get('judge_by', None),
            judge_by_file=data.get('judge_by_file', None),
            memorize_to=data.get('memorize_to', "GOLDFISH"),
            at_most=data.get('at_most', None),
            expose_index_as=data.get('expose_index_as', None),
            skippable=data.get('skippable', False),
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
            sub_type=data.get('sub_type', data.get('subType', None)),
            operation=data.get('operation', None),
            # DB node special handling for backward compatibility
            query=data.get('query', None),
            keys=data.get('keys', None),
            lines=data.get('lines', None),
            # DB node special handling for backward compatibility
            data=data.get('data', None),
            # Serialize JSON field may have camelCase variants
            serialize_json=data.get('serialize_json', data.get('serializeJson', False)),
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
            backup=data.get('backup', True),
            validate_patch=data.get('validate_patch', True),
            backup_dir=data.get('backup_dir', None),
            strip_level=data.get('strip_level', 1),
            fuzz_factor=data.get('fuzz_factor', 2),
            reject_file=data.get('reject_file', None),
            ignore_whitespace=data.get('ignore_whitespace', False),
            create_missing=data.get('create_missing', False),
        )

    elif node_type == NodeType.ENDPOINT:
        return EndpointNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            save_to_file=data.get('save_to_file', None),
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
            url=data.get('url', None),
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
            provider=data.get('provider', None),
            operation=data.get('operation', None),
            resource_id=data.get('resource_id', None),
            config=data.get('config', None),
            timeout=data.get('timeout', None),
            max_retries=data.get('max_retries', None),
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
            cache_enabled=data.get('cache_enabled', None),
            validate_output=data.get('validate_output', None),
        )

    elif node_type == NodeType.JSON_SCHEMA_VALIDATOR:
        return JsonSchemaValidatorNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            schema_path=data.get('schema_path', None),
            json_schema=data.get('json_schema', None),
            data_path=data.get('data_path', None),
            strict_mode=data.get('strict_mode', None),
            error_on_extra=data.get('error_on_extra', None),
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
            custom_data=data.get('custom_data', None),
            output_data_structure=data.get('output_data_structure', None),
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
            wait_for_completion=data.get('wait_for_completion', True),
            isolate_conversation=data.get('isolate_conversation', False),
            ignore_if_sub=data.get('ignoreIfSub', False),
            diagram_format=data.get('diagram_format', None),
            batch=data.get('batch', False),
            batch_input_key=data.get('batch_input_key', None),
            batch_parallel=data.get('batch_parallel', False),
        )

    elif node_type == NodeType.TEMPLATE_JOB:
        return TemplateJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            template_path=data.get('template_path', None),
            template_content=data.get('template_content', None),
            output_path=data.get('output_path', None),
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
            extract_patterns=data.get('extractPatterns', ['interface', 'type', 'enum']),
            include_js_doc=data.get('includeJSDoc', False),
            parse_mode=data.get('parseMode', "module"),
            transform_enums=data.get('transformEnums', False),
            flatten_output=data.get('flattenOutput', False),
            output_format=data.get('outputFormat', "standard"),
            batch=data.get('batch', False),
            batch_input_key=data.get('batchInputKey', "sources"),
        )

    elif node_type == NodeType.USER_RESPONSE:
        return UserResponseNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            prompt=data.get('prompt', None),
            timeout=data.get('timeout', 300),
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
