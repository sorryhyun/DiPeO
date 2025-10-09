// Auto-generated TypeScript model for integrated_api node
import { z } from 'zod';

export interface IntegratedApiNodeData {
  provider: string;
  operation: string;
}

// Zod schema for validation
export const IntegratedApiNodeDataSchema = z.object({
  provider: z.string().describe("API provider to connect to"),
  operation: z.string().describe("Operation to perform (provider-specific)"),
});
