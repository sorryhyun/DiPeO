// Auto-generated TypeScript model for user_response node
import { z } from 'zod';

export interface UserResponseNodeData {
  prompt: string;
}

// Zod schema for validation
export const UserResponseNodeDataSchema = z.object({
  prompt: z.string().describe("Question to ask the user"),
});
