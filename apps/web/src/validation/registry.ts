import { z } from 'zod';
import * as schemas from './schemas';
import { NodeType } from '@/types/enums';

/**
 * Registry of all node schemas by type
 */
export const NodeSchemas = {
  start: schemas.StartNodeSchema,
  condition: schemas.ConditionNodeSchema,
  person_job: schemas.PersonJobNodeSchema,
  endpoint: schemas.EndpointNodeSchema,
  db: schemas.DBNodeSchema,
  job: schemas.JobNodeSchema,
  user_response: schemas.UserResponseNodeSchema,
  notion: schemas.NotionNodeSchema,
  person_batch_job: schemas.PersonBatchJobNodeSchema
} as const satisfies Record<NodeType, z.ZodSchema>;

/**
 * Node data schemas by type
 */
export const NodeDataSchemas = {
  start: schemas.StartNodeDataSchema,
  condition: schemas.ConditionNodeDataSchema,
  person_job: schemas.PersonJobNodeDataSchema,
  endpoint: schemas.EndpointNodeDataSchema,
  db: schemas.DBNodeDataSchema,
  job: schemas.JobNodeDataSchema,
  user_response: schemas.UserResponseNodeDataSchema,
  notion: schemas.NotionNodeDataSchema,
  person_batch_job: schemas.PersonBatchJobNodeDataSchema
} as const satisfies Record<NodeType, z.ZodSchema>;

/**
 * Diagram metadata schema
 */
export const DiagramMetadataSchema = z.object({
  id: z.string().optional(),
  name: z.string().optional(),
  description: z.string().optional(),
  version: z.string(),
  created: z.string(),
  modified: z.string(),
  author: z.string().optional(),
  tags: z.array(z.string()).optional()
});

/**
 * Complete diagram schema
 */
export const DiagramSchema = z.object({
  nodes: z.record(schemas.NodeIDSchema, schemas.DiagramNodeSchema),
  handles: z.record(schemas.HandleIDSchema, schemas.DomainHandleSchema),
  arrows: z.record(schemas.ArrowIDSchema, schemas.DomainArrowSchema),
  persons: z.record(schemas.PersonIDSchema, schemas.DomainPersonSchema),
  metadata: DiagramMetadataSchema.optional()
});

export type ValidatedDiagram = z.infer<typeof DiagramSchema>;

/**
 * Parse and validate a node by type
 */
export function parseNode(data: unknown): schemas.ValidatedNode {
  const nodeType = (data as any).type;
  
  if (!nodeType || !(nodeType in NodeSchemas)) {
    throw new Error(`Unknown node type: ${nodeType}`);
  }
  
  const schema = NodeSchemas[nodeType as NodeType];
  return schema.parse(data) as schemas.ValidatedNode;
}

/**
 * Parse and validate node data by type
 */
export function parseNodeData(type: NodeType, data: unknown): unknown {
  const schema = NodeDataSchemas[type];
  return schema.parse(data);
}

/**
 * Validate a complete diagram
 */
export function parseDiagram(data: unknown): ValidatedDiagram {
  return DiagramSchema.parse(data);
}

/**
 * Safe parse with error details
 */
export function safeParseDiagram(data: unknown): {
  success: boolean;
  data?: ValidatedDiagram;
  error?: z.ZodError;
} {
  const result = DiagramSchema.safeParse(data);
  
  if (result.success) {
    return { success: true, data: result.data };
  } else {
    return { success: false, error: result.error };
  }
}