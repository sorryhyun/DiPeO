// Auto-generated TypeScript model for db node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface DbNodeData {
  file?: string;
  collection?: string;
  sub_type: any;
  operation: string;
  query?: string;
  data?: Record<string, any>;
}

export interface DbNode extends BaseNode {
  type: 'db';
  data: DbNodeData;
}

// Zod schema for validation
export const DbNodeDataSchema = z.object({
  file: stringSchema.optional(),  collection: stringSchema.optional(),  sub_type: enumSchema,  operation: stringSchema,  query: stringSchema.optional(),  data: objectSchema.optional()});

export const DbNodeSchema = z.object({
  type: z.literal('db'),
  data: DbNodeDataSchema,
});