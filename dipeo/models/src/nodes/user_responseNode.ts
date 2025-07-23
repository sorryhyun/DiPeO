// Auto-generated TypeScript model for user_response node
import { z } from 'zod';
import { BaseNode } from '../base';

export interface User_responseNodeData {
  prompt: string;
  timeout: number;
}

export interface User_responseNode extends BaseNode {
  type: 'user_response';
  data: User_responseNodeData;
}

// Zod schema for validation
export const User_responseNodeDataSchema = z.object({
  prompt: z.string(),  timeout: z.number()});

export const User_responseNodeSchema = z.object({
  type: z.literal('user_response'),
  data: User_responseNodeDataSchema,
});