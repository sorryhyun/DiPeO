// Auto-generated TypeScript model for user_response node
import { z } from 'zod';

export interface UserResponseNodeData {
  prompt: string;
  timeout?: number | undefined;
}

// Zod schema for validation
export const UserResponseNodeDataSchema = z.object({
  prompt: z.string().describe("Question to ask the user"),
  timeout: z.number().optional().describe("Response timeout in seconds"),
});
