// Auto-generated TypeScript model for typescript_ast node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface Typescript_astNodeData {
  source: string;
  extractPatterns?: any[];
  includeJSDoc?: boolean;
  parseMode?: any;
}

export interface Typescript_astNode extends BaseNode {
  type: 'typescript_ast';
  data: Typescript_astNodeData;
}

// Zod schema for validation
export const Typescript_astNodeDataSchema = z.object({
  source: stringSchema,  extractPatterns: arraySchema.optional(),  includeJSDoc: booleanSchema.optional(),  parseMode: enumSchema.optional()});

export const Typescript_astNodeSchema = z.object({
  type: z.literal('typescript_ast'),
  data: Typescript_astNodeDataSchema,
});