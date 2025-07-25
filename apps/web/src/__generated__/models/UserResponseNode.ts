// Auto-generated TypeScript model for user_response node
import { z } from 'zod';

export interface UserResponseNodeData {
  prompt: string;
  timeout: number;
}

// Zod schema for validation
export const UserResponseNodeDataSchema = z.object({
  prompt: z.string(),
  timeout: z.number(),
});