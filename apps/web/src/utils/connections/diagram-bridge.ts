/**
 * Bridge module to integrate the new typed connection system with the existing diagram store
 * This module provides utilities to work with both the legacy and new type systems
 */

import { Node, Arrow, Handle } from '@/types';
import { DiagramNode } from '@/types/diagram';
import { NodeID, HandleID, ArrowID } from '@/types/branded';
import { NodeType, DataType } from '@/types/enums';
import { InputHandle, OutputHandle } from '@/types/node-base';
import { createHandleId, parseHandleId } from '@/utils/canvas/handle-adapter';

/**
 * Convert a legacy Node to a typed DiagramNode
 * This adds the typed inputs/outputs structure required by the new system
 */
export function legacyNodeToDiagramNode(node: Node): DiagramNode {
  const inputs: Record<string, InputHandle<string>> = {};
  const outputs: Record<string, OutputHandle<string>> = {};

  // Sort handles into inputs and outputs
  node.handles.forEach(handle => {
    const { handleName } = parseHandleId(handle.id);
    
    if (handle.kind === 'target' || handle.kind === 'input') {
      inputs[handleName] = {
        id: handle.id as HandleID,
        kind: 'input',
        name: handleName,
        dataType: mapLegacyDataType(handle.dataType),
        position: handle.position,
        label: handle.label
      };
    } else if (handle.kind === 'source' || handle.kind === 'output') {
      outputs[handleName] = {
        id: handle.id as HandleID,
        kind: 'output',
        name: handleName,
        dataType: mapLegacyDataType(handle.dataType),
        position: handle.position,
        label: handle.label
      };
    }
  });

  return {
    id: node.id as NodeID,
    type: mapLegacyNodeType(node.type),
    position: node.position,
    data: node.data,
    inputs,
    outputs,
    selected: node.selected,
    draggable: node.draggable,
    selectable: node.selectable,
    connectable: node.connectable
  } as DiagramNode;
}

/**
 * Convert a typed DiagramNode back to a legacy Node
 */
export function diagramNodeToLegacyNode(node: DiagramNode): Node {
  const handles: Handle[] = [];

  // Convert inputs to handles
  Object.entries(node.inputs).forEach(([name, input]) => {
    handles.push({
      id: input.id,
      kind: 'target' as const,
      name,
      dataType: reverseMapDataType(input.dataType),
      position: input.position || { x: 0, y: 0 },
      label: input.label
    });
  });

  // Convert outputs to handles
  Object.entries(node.outputs).forEach(([name, output]) => {
    handles.push({
      id: output.id,
      kind: 'source' as const,
      name,
      dataType: reverseMapDataType(output.dataType),
      position: output.position || { x: 0, y: 0 },
      label: output.label
    });
  });

  return {
    id: node.id,
    type: reverseMapNodeType(node.type),
    position: node.position,
    data: node.data,
    handles,
    selected: node.selected,
    draggable: node.draggable,
    selectable: node.selectable,
    connectable: node.connectable
  } as Node;
}

/**
 * Map legacy node type strings to NodeType enum
 */
function mapLegacyNodeType(type: string): NodeType {
  const typeMap: Record<string, NodeType> = {
    'start': NodeType.Start,
    'condition': NodeType.Condition,
    'person_job': NodeType.PersonJob,
    'endpoint': NodeType.Endpoint,
    'db': NodeType.DB,
    'job': NodeType.Job,
    'user_response': NodeType.UserResponse,
    'notion': NodeType.Notion,
    'person_batch_job': NodeType.PersonBatchJob
  };

  return typeMap[type] || NodeType.Start; // Default fallback
}

/**
 * Map NodeType enum back to legacy string
 */
function reverseMapNodeType(type: NodeType): string {
  const reverseMap: Record<NodeType, string> = {
    [NodeType.Start]: 'start',
    [NodeType.Condition]: 'condition',
    [NodeType.PersonJob]: 'person_job',
    [NodeType.Endpoint]: 'endpoint',
    [NodeType.DB]: 'db',
    [NodeType.Job]: 'job',
    [NodeType.UserResponse]: 'user_response',
    [NodeType.Notion]: 'notion',
    [NodeType.PersonBatchJob]: 'person_batch_job'
  };

  return reverseMap[type];
}

/**
 * Map legacy data type strings to DataType enum
 */
function mapLegacyDataType(dataType?: string): DataType {
  if (!dataType) return DataType.Any;

  const typeMap: Record<string, DataType> = {
    'any': DataType.Any,
    'string': DataType.String,
    'number': DataType.Number,
    'boolean': DataType.Boolean,
    'array': DataType.Array,
    'object': DataType.Object,
    'text': DataType.Text,
    'integer': DataType.Integer,
    'float': DataType.Float,
    'json': DataType.JSON
  };

  return typeMap[dataType] || DataType.Any; // Default fallback
}

/**
 * Map DataType enum back to legacy string
 */
function reverseMapDataType(dataType: DataType): string {
  const reverseMap: Record<DataType, string> = {
    [DataType.Any]: 'any',
    [DataType.String]: 'string',
    [DataType.Number]: 'number',
    [DataType.Boolean]: 'boolean',
    [DataType.Array]: 'array',
    [DataType.Object]: 'object',
    [DataType.Text]: 'text',
    [DataType.Integer]: 'integer',
    [DataType.Float]: 'float',
    [DataType.JSON]: 'json'
  };

  return reverseMap[dataType];
}

/**
 * Convert a Map of legacy nodes to a Map of DiagramNodes
 */
export function convertNodeMap(nodes: Map<string, Node>): Map<string, DiagramNode> {
  const diagramNodes = new Map<string, DiagramNode>();
  
  nodes.forEach((node, id) => {
    diagramNodes.set(id, legacyNodeToDiagramNode(node));
  });
  
  return diagramNodes;
}

/**
 * Convert a Map of DiagramNodes back to legacy nodes
 */
export function convertDiagramNodeMap(nodes: Map<string, DiagramNode>): Map<string, Node> {
  const legacyNodes = new Map<string, Node>();
  
  nodes.forEach((node, id) => {
    legacyNodes.set(id, diagramNodeToLegacyNode(node));
  });
  
  return legacyNodes;
}