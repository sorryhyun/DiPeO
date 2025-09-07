"""
Compatibility shim for generated_unified_nodes.py
Re-exports from individual files for backward compatibility.
This file is part of the Phase 1 refactoring to eliminate monolithic files.
"""

# Re-export all node classes from individual files
from .unified_nodes.api_job_node import ApiJobNode
from .unified_nodes.code_job_node import CodeJobNode
from .unified_nodes.condition_node import ConditionNode
from .unified_nodes.db_node import DbNode as DBNode  # Alias for compatibility
from .unified_nodes.endpoint_node import EndpointNode
from .unified_nodes.hook_node import HookNode
from .unified_nodes.integrated_api_node import IntegratedApiNode
from .unified_nodes.json_schema_validator_node import JsonSchemaValidatorNode
from .unified_nodes.person_job_node import PersonJobNode
from .unified_nodes.start_node import StartNode
from .unified_nodes.sub_diagram_node import SubDiagramNode
from .unified_nodes.template_job_node import TemplateJobNode
from .unified_nodes.typescript_ast_node import TypescriptAstNode
from .unified_nodes.user_response_node import UserResponseNode

# Re-export NodeType and DBBlockSubType enums from enums
from .enums import NodeType, DBBlockSubType

# Re-export base types from domain_models (will be replaced by compatibility shim next)
from .domain_models import (
    NodeID,
    Vec2,
    HandleID,
    DomainNode,
    DomainArrow,
    DomainHandle,
)

# Import typing for the function signature
from typing import Dict, Any, Optional, Union

# Create the create_executable_node function
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

    # Create the appropriate node based on type
    if node_type == NodeType.API_JOB:
        return ApiJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            url=data.get('url'),
            method=data.get('method'),
            headers=data.get('headers'),
            body=data.get('body'),
            api_key_id=data.get('api_key_id'),
            timeout=data.get('timeout', 30),
            retry_count=data.get('retry_count', 3),
            retry_delay=data.get('retry_delay', 1),
        )

    elif node_type == NodeType.CODE_JOB:
        return CodeJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            language=data.get('language'),
            code=data.get('code', ''),
            file_path=data.get('filePath', data.get('file_path', '')),
            function_name=data.get('functionName', data.get('function_name', '')),
            timeout=data.get('timeout', 0),
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
            node_indices=data.get('node_indices', []),
            person=data.get('person', ''),
            judge_by=data.get('judge_by', ''),
            judge_by_file=data.get('judge_by_file', ''),
            memorize_to=data.get('memorize_to', ''),
            at_most=data.get('at_most', 0),
            expose_index_as=data.get('expose_index_as', ''),
            skippable=data.get('skippable', False),
        )

    elif node_type == NodeType.DB:
        # Handle source_details if it exists (backward compatibility)
        source_details = data.get('source_details', {})
        if isinstance(source_details, dict):
            file_val = source_details.get('file', data.get('file', ''))
            collection_val = source_details.get('collection', data.get('collection', ''))
            query_val = source_details.get('query', data.get('query', ''))
            data_val = source_details.get('data', data.get('data', {}))
        else:
            file_val = data.get('file', '')
            collection_val = data.get('collection', '')
            query_val = data.get('query', '')
            data_val = data.get('data', {})

        return DBNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            operation=data.get('operation', ''),
            sub_type=data.get('sub_type', data.get('subType', DBBlockSubType.FILE)),
            file=file_val,
            collection=collection_val,
            query=query_val,
            data=data_val,
            serialize_json=data.get('serialize_json', data.get('serializeJson', False)),
            format=data.get('format', ''),
        )

    elif node_type == NodeType.ENDPOINT:
        return EndpointNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            save_to_file=data.get('save_to_file', False),
            file_name=data.get('filename', data.get('file_name', '')),
        )

    elif node_type == NodeType.HOOK:
        return HookNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            hook_type=data.get('hook_type'),
            hook_name=data.get('hook_name'),
            trigger_on=data.get('trigger_on'),
            condition=data.get('condition'),
        )

    elif node_type == NodeType.INTEGRATED_API:
        return IntegratedApiNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            provider=data.get('provider'),
            action=data.get('action'),
            config=data.get('config'),
            use_hooks=data.get('use_hooks', False),
        )

    elif node_type == NodeType.JSON_SCHEMA_VALIDATOR:
        return JsonSchemaValidatorNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            schema=data.get('schema'),
            raise_on_invalid=data.get('raise_on_invalid', False),
            mode=data.get('mode', 'validate'),
        )

    elif node_type == NodeType.PERSON_JOB:
        return PersonJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            person=data.get('person', ''),
            first_only_prompt=data.get('first_only_prompt', data.get('prompt', '')),
            default_prompt=data.get('default_prompt', ''),
            max_iteration=data.get('max_iteration', 100),
            memorize_to=data.get('memorize_to', ''),
            at_most=data.get('at_most', 0),
            tools=data.get('tools', 'none'),
            text_format=data.get('text_format', ''),
            resolved_prompt=data.get('resolved_prompt', ''),
            resolved_first_prompt=data.get('resolved_first_prompt', ''),
        )

    elif node_type == NodeType.START:
        return StartNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            trigger_mode=data.get('trigger_mode', 'none'),
            custom_data=data.get('custom_data'),
            output_data_structure=data.get('output_data_structure'),
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
            diagram_name=data.get('diagram_name', ''),
            diagram_data=data.get('diagram_data', {}),
            input_mapping=data.get('input_mapping', {}),
            output_mapping=data.get('output_mapping', {}),
            timeout=data.get('timeout', 0),
            wait_for_completion=data.get('wait_for_completion', False),
            isolate_conversation=data.get('isolate_conversation', False),
            ignore_if_sub=data.get('ignoreIfSub', data.get('ignore_if_sub', False)),
            diagram_format=data.get('diagram_format'),
            batch=data.get('batch', False),
            batch_input_key=data.get('batch_input_key', ''),
            batch_parallel=data.get('batch_parallel', False),
        )

    elif node_type == NodeType.TEMPLATE_JOB:
        return TemplateJobNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            engine=data.get('engine', 'jinja2'),
            template_content=data.get('template', data.get('template_content', '')),
            template_path=data.get('template_path', data.get('templatePath', '')),
            output_path=data.get('output_path', data.get('outputPath', '')),
            variables=data.get('variables', {}),
            # preprocessor field removed - not in generated node class yet
            # foreach field removed - not in TypeScript spec
        )

    elif node_type == NodeType.TYPESCRIPT_AST:
        return TypescriptAstNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            source=data.get('source', data.get('filePath', '')),
            batch=data.get('batch', False),
            batch_input_key=data.get('batchInputKey', data.get('batch_input_key', 'sources')),
            extract_patterns=data.get('extractPatterns', data.get('extract_patterns', [])),
            include_js_doc=data.get('includeJSDoc', data.get('include_js_doc', False)),
            parse_mode=data.get('parseMode', data.get('parse_mode', 'module')),
            transform_enums=data.get('transformEnums', data.get('transform_enums', False)),
            flatten_output=data.get('flattenOutput', data.get('flatten_output', False)),
            output_format=data.get('outputFormat', data.get('output_format')),
        )

    elif node_type == NodeType.USER_RESPONSE:
        return UserResponseNode(
            id=node_id,
            position=position,
            label=label,
            flipped=flipped,
            metadata=metadata,
            join_policy=data.get('join_policy'),
            join_k=data.get('join_k'),
            prompt=data.get('prompt'),
            timeout=data.get('timeout', 300),
        )

    else:
        raise ValueError(f"Unknown node type: {node_type}")

# Union type for all executable node types
ExecutableNode = Union[
    ApiJobNode,
    CodeJobNode,
    ConditionNode,
    DBNode,
    EndpointNode,
    HookNode,
    IntegratedApiNode,
    JsonSchemaValidatorNode,
    PersonJobNode,
    StartNode,
    SubDiagramNode,
    TemplateJobNode,
    TypescriptAstNode,
    UserResponseNode,
]

# Re-export all for backward compatibility
__all__ = [
    # Node classes
    'ApiJobNode',
    'CodeJobNode',
    'ConditionNode',
    'DBNode',
    'EndpointNode',
    'HookNode',
    'IntegratedApiNode',
    'JsonSchemaValidatorNode',
    'PersonJobNode',
    'StartNode',
    'SubDiagramNode',
    'TemplateJobNode',
    'TypescriptAstNode',
    'UserResponseNode',
    # Enum and types
    'NodeType',
    'NodeID',
    'Vec2',
    'HandleID',
    'DomainNode',
    'DomainArrow',
    'DomainHandle',
    # Factory function
    'create_executable_node',
    # Union type
    'ExecutableNode',
]