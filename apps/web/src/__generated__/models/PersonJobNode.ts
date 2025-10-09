// Auto-generated TypeScript model for person_job node
import { z } from 'zod';

export interface PersonJobNodeData {
  tools?: string | undefined;
}

// Zod schema for validation
export const PersonJobNodeDataSchema = z.object({
  tools: z.string().optional().describe("Tools available to the AI agent"),
});
