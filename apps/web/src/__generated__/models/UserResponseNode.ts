// Auto-generated TypeScript model for user_response node
import { z } from 'zod';

export interface UserResponseNodeData {
  prompt: string;
  timeout?: number | undefined;
}

// Zod schema for validation
export const UserResponseNodeDataSchema = z.object({
  prompt: z.string().describe("Question to ask the user"),
  timeout: z.number().min(0).max(3600).optional().describe("Response timeout in seconds"),
});
