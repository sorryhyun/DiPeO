/**
 * Conversion utilities for DiPeO domain models.
 * Includes domain conversions and GraphQL/store format conversions.
 */

import {
  NodeID,
  ArrowID,
  HandleID,
  PersonID,
  DomainNode,
  DomainArrow,
  DomainHandle,
  DomainPerson,
  DomainDiagram,
  PersonLLMConfig,
} from '../core/diagram.js';
import { NodeType } from '../core/enums/node-types.js';
import { HandleDirection, HandleLabel } from '../core/enums/data-types.js';


export const NODE_TYPE_MAP: Record<string, NodeType> = {
  'code_job': NodeType.CODE_JOB,
  'api_job': NodeType.API_JOB,
  'person_job': NodeType.PERSON_JOB,
  'condition': NodeType.CONDITION,
  'user_response': NodeType.USER_RESPONSE,
  'start': NodeType.START,
  'endpoint': NodeType.ENDPOINT,
  'db': NodeType.DB,
  'hook': NodeType.HOOK,
  'template_job': NodeType.TEMPLATE_JOB,
  'json_schema_validator': NodeType.JSON_SCHEMA_VALIDATOR,
  'typescript_ast': NodeType.TYPESCRIPT_AST,
  'sub_diagram': NodeType.SUB_DIAGRAM,
  'integrated_api': NodeType.INTEGRATED_API,
  'ir_builder': NodeType.IR_BUILDER,
  'diff_patch': NodeType.DIFF_PATCH,
} as const;

export const NODE_TYPE_REVERSE_MAP: Record<NodeType, string> = Object.entries(NODE_TYPE_MAP)
  .reduce((acc, [key, value]) => ({ ...acc, [value]: key }), {} as Record<NodeType, string>);

export function nodeKindToDomainType(kind: string): NodeType {
  const normalizedKind = kind.toLowerCase();
  const domainType = NODE_TYPE_MAP[normalizedKind];
  if (!domainType) {
    throw new Error(`Unknown node kind: ${kind}`);
  }
  return domainType;
}

export function domainTypeToNodeKind(type: NodeType | string): string {
  const normalizedType = typeof type === 'string' ? type.toLowerCase() : type;
  const kind = NODE_TYPE_REVERSE_MAP[normalizedType as NodeType];

  if (!kind) {
    throw new Error(`Unknown node type: ${type}`);
  }
  return kind;
}


export function createHandleId(
  nodeId: NodeID,
  handleLabel: HandleLabel,
  direction: HandleDirection
): HandleID {
  return `${nodeId}_${handleLabel}_${direction}` as HandleID;
}

export function parseHandleId(
  handleId: HandleID
): { node_id: NodeID; handle_label: HandleLabel; direction: HandleDirection } {
  const parts = handleId.split('_');
  if (parts.length < 3) {
    throw new Error(`Invalid handle ID format: ${handleId}`);
  }
  const direction = parts[parts.length - 1] as HandleDirection;
  const handleLabel = parts[parts.length - 2] as HandleLabel;
  const nodeIdParts = parts.slice(0, -2);
  const nodeId = nodeIdParts.join('_');

  if (!nodeId || !handleLabel || !Object.values(HandleDirection).includes(direction)) {
    throw new Error(`Invalid handle ID format: ${handleId}`);
  }
  if (!Object.values(HandleLabel).includes(handleLabel)) {
    throw new Error(`Invalid handle label in handle ID: ${handleId}`);
  }

  return {
    node_id: nodeId as NodeID,
    handle_label: handleLabel,
    direction,
  };
}


export function areHandlesCompatible(
  sourceHandle: DomainHandle,
  targetHandle: DomainHandle
): boolean {
  if (sourceHandle.direction === targetHandle.direction) {
    return false;
  }
  if (sourceHandle.direction !== HandleDirection.OUTPUT) {
    return false;
  }
  if (sourceHandle.data_type === targetHandle.data_type) {
    return true;
  }
  return sourceHandle.data_type === 'any' || targetHandle.data_type === 'any';
}


export function diagramArraysToMaps(diagram: Partial<{
  nodes: DomainNode[];
  arrows: DomainArrow[];
  handles: DomainHandle[];
  persons: DomainPerson[];
}>): {
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  handles: Map<HandleID, DomainHandle>;
  persons: Map<PersonID, DomainPerson>;
} {
  return {
    nodes: new Map(diagram.nodes?.map(n => [n.id, n]) ?? []),
    arrows: new Map(diagram.arrows?.map(a => [a.id, a]) ?? []),
    handles: new Map(diagram.handles?.map(h => [h.id, h]) ?? []),
    persons: new Map(diagram.persons?.map(p => [p.id, p]) ?? []),
  };
}

export function diagramMapsToArrays(diagram: {
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  handles: Map<HandleID, DomainHandle>;
  persons: Map<PersonID, DomainPerson>;
}): {
  nodes: DomainNode[];
  arrows: DomainArrow[];
  handles: DomainHandle[];
  persons: DomainPerson[];
} {
  return {
    nodes: Array.from(diagram.nodes.values()),
    arrows: Array.from(diagram.arrows.values()),
    handles: Array.from(diagram.handles.values()),
    persons: Array.from(diagram.persons.values()),
  };
}


export function convertGraphQLPersonToDomain(graphqlPerson: any): DomainPerson {
  const apiKeyId = graphqlPerson.llm_config?.api_key_id || '';

  return {
    id: graphqlPerson.id as PersonID,
    label: graphqlPerson.label,
    llm_config: {
      service: graphqlPerson.llm_config.service,
      model: graphqlPerson.llm_config.model,
      api_key_id: apiKeyId,
      system_prompt: graphqlPerson.llm_config.system_prompt || null,
    } as PersonLLMConfig,
    type: 'person' as const,
  };
}

export function convertGraphQLDiagramToDomain(diagram: any): Partial<DomainDiagram> {
  const result: Partial<DomainDiagram> = {};

  if (diagram.nodes) {
    result.nodes = diagram.nodes;
  }

  if (diagram.handles) {
    result.handles = diagram.handles;
  }

  if (diagram.arrows) {
    result.arrows = diagram.arrows.map((arrow: any) => ({
      ...arrow,
      content_type: arrow.content_type || arrow.contentType,
      label: arrow.label,
    }));
  }

  if (diagram.persons) {
    result.persons = diagram.persons.map(convertGraphQLPersonToDomain);
  }

  return result;
}
