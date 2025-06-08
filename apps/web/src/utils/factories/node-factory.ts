// apps/web/src/utils/factories/node-factory.ts
import { NodeType, DataType } from '@/types/enums';
import { NodeSpecs, HandleNamesOf } from '@/types/node-specs';
import { NodeID, HandleID, nodeId, handleId } from '@/types/branded';
import { Vec2 } from '@/types/primitives';
import { DiagramNode } from '@/types/nodes';
import { InputHandle, OutputHandle } from '@/types/node-base';
import { generateShortId } from '@/utils/id';

/**
 * Generate a unique node ID with proper prefix
 */
function generateNodeId(type: NodeType): NodeID {
  const prefixMap: Record<NodeType, string> = {
    [NodeType.Start]: 'st',
    [NodeType.Condition]: 'cd',
    [NodeType.PersonJob]: 'pj',
    [NodeType.Endpoint]: 'ep',
    [NodeType.DB]: 'db',
    [NodeType.Job]: 'jb',
    [NodeType.UserResponse]: 'ur',
    [NodeType.Notion]: 'nt',
    [NodeType.PersonBatchJob]: 'pb'
  };
  
  const prefix = prefixMap[type] || 'nd';
  return nodeId(`${prefix}-${generateShortId()}`);
}

/**
 * Creates a new node with typed handles based on node specifications
 */
export function createNode<K extends NodeType>(
  type: K,
  data: Omit<Extract<DiagramNode, { type: K }>['data'], 'id' | 'type' | 'label'> & { label?: string },
  position: Vec2 = { x: 0, y: 0 }
): Extract<DiagramNode, { type: K }> {
  const id = generateNodeId(type);
  const spec = NodeSpecs[type];
  
  if (!spec) {
    throw new Error(`No specification found for node type: ${type}`);
  }
  
  // Build node data with defaults
  const nodeData = {
    ...data,
    id: id as string,
    type,
    label: data.label || getDefaultLabel(type)
  } as Extract<DiagramNode, { type: K }>['data'];
  
  // Build input handles based on spec
  const inputs: any = {};
  for (const [handleName, handleSpec] of Object.entries(spec.handles)) {
    if (handleSpec.direction === 'input') {
      const hId = handleId(id, handleName);
      const handle: InputHandle<string> = {
        id: hId,
        kind: 'input',
        name: handleName,
        dataType: handleSpec.dataType,
        position: getDefaultHandlePosition(handleName, 'input', type)
      };
      inputs[handleName] = handle;
    }
  }
  
  // Build output handles based on spec
  const outputs: any = {};
  for (const [handleName, handleSpec] of Object.entries(spec.handles)) {
    if (handleSpec.direction === 'output') {
      const hId = handleId(id, handleName);
      const handle: OutputHandle<string> = {
        id: hId,
        kind: 'output',
        name: handleName,
        dataType: handleSpec.dataType,
        position: getDefaultHandlePosition(handleName, 'output', type)
      };
      outputs[handleName] = handle;
    }
  }
  
  return {
    id,
    type,
    position,
    data: nodeData,
    inputs,
    outputs
  } as Extract<DiagramNode, { type: K }>;
}

/**
 * Get default label for a node type
 */
function getDefaultLabel(type: NodeType): string {
  const labelMap: Record<NodeType, string> = {
    [NodeType.Start]: 'Start',
    [NodeType.Condition]: 'Condition',
    [NodeType.PersonJob]: 'Person Job',
    [NodeType.Endpoint]: 'Endpoint',
    [NodeType.DB]: 'Database',
    [NodeType.Job]: 'Job',
    [NodeType.UserResponse]: 'User Response',
    [NodeType.Notion]: 'Notion',
    [NodeType.PersonBatchJob]: 'Person Batch Job'
  };
  
  return labelMap[type] || 'Node';
}

/**
 * Get default handle position based on handle name and node type
 */
function getDefaultHandlePosition(
  handleName: string,
  direction: 'input' | 'output',
  nodeType: NodeType
): Vec2 {
  // Special positions for specific node types
  if (nodeType === NodeType.Condition) {
    if (direction === 'output') {
      return handleName === 'true' ? { x: 1, y: 0.3 } : { x: 1, y: 0.7 };
    }
  }
  
  if (nodeType === NodeType.PersonJob && direction === 'input') {
    return handleName === 'first' ? { x: 0, y: 0.3 } : { x: 0, y: 0.7 };
  }
  
  // Default positions
  return direction === 'input' ? { x: 0, y: 0.5 } : { x: 1, y: 0.5 };
}

/**
 * Create a start node
 */
export function createStartNode(
  output: string,
  position?: Vec2,
  label?: string
) {
  return createNode(NodeType.Start, { output, label }, position);
}

/**
 * Create a condition node
 */
export function createConditionNode(
  condition: string,
  conditionType: 'simple' | 'complex' | 'detect_max_iterations' = 'simple',
  position?: Vec2,
  label?: string
) {
  return createNode(NodeType.Condition, { condition, conditionType, label }, position);
}

/**
 * Create a person job node
 */
export function createPersonJobNode(
  personId: string,
  prompts: {
    firstOnlyPrompt: string;
    defaultPrompt: string;
  },
  options?: {
    maxIteration?: number;
    contextCleaningRule?: 'no_forget' | 'on_every_turn' | 'upon_request';
    position?: Vec2;
    label?: string;
  }
) {
  return createNode(NodeType.PersonJob, {
    personId: personId as any, // Will be properly typed as PersonID
    firstOnlyPrompt: prompts.firstOnlyPrompt,
    defaultPrompt: prompts.defaultPrompt,
    maxIteration: options?.maxIteration || 1,
    contextCleaningRule: options?.contextCleaningRule || 'no_forget',
    label: options?.label
  }, options?.position);
}

/**
 * Create an endpoint node
 */
export function createEndpointNode(
  action: 'save' | 'output',
  filename?: string,
  position?: Vec2,
  label?: string
) {
  return createNode(NodeType.Endpoint, { action, filename, label }, position);
}

/**
 * Create a database node
 */
export function createDBNode(
  operation: 'read' | 'write' | 'query',
  path: string,
  format: 'json' | 'csv' | 'text' = 'json',
  position?: Vec2,
  label?: string
) {
  return createNode(NodeType.DB, { operation, path, format, label }, position);
}

/**
 * Create a job node
 */
export function createJobNode(
  subType: 'python' | 'javascript' | 'bash',
  code: string,
  position?: Vec2,
  label?: string
) {
  return createNode(NodeType.Job, { subType, code, label }, position);
}

/**
 * Create a user response node
 */
export function createUserResponseNode(
  promptMessage: string,
  timeoutSeconds: number = 30,
  position?: Vec2,
  label?: string
) {
  return createNode(NodeType.UserResponse, { promptMessage, timeoutSeconds, label }, position);
}

/**
 * Create a notion node
 */
export function createNotionNode(
  operation: 'read_page' | 'list_blocks' | 'append_blocks' | 'update_block' | 
             'query_database' | 'create_page' | 'extract_text',
  apiKeyId: string,
  ids?: {
    pageId?: string;
    blockId?: string;
    databaseId?: string;
  },
  position?: Vec2,
  label?: string
) {
  return createNode(NodeType.Notion, {
    operation,
    apiKeyId,
    ...ids,
    label
  }, position);
}

/**
 * Create a person batch job node
 */
export function createPersonBatchJobNode(
  personId: string,
  prompt: string,
  batchSize: number = 10,
  position?: Vec2,
  label?: string
) {
  return createNode(NodeType.PersonBatchJob, {
    personId: personId as any, // Will be properly typed as PersonID
    prompt,
    batchSize,
    label
  }, position);
}