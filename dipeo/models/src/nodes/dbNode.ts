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
  file: z.string().optional(),  collection: z.string().optional(),  sub_type: z.any(),  operation: z.string(),  query: z.string().optional(),  data: z.record(z.any()).optional()});

export const DbNodeSchema = z.object({
  type: z.literal('db'),
  data: DbNodeDataSchema,
});