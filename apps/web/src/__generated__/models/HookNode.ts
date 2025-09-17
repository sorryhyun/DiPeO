// Auto-generated TypeScript model for hook node
import { z } from 'zod';
import { HookType } from '@dipeo/models';

export interface HookNodeData {
  hook_type: HookType;
  command?: string | undefined;
  url?: string | undefined;
  timeout?: number | undefined;
  retry_count?: number | undefined;
}

// Zod schema for validation
export const HookNodeDataSchema = z.object({
  hook_type: z.any().describe("Type of hook to execute"),
  command: z.string().optional().describe("Shell command to run (for shell hooks)"),
  url: z.string().regex(/^https?:\/\/.+/).optional().describe("Webhook URL (for HTTP hooks)"),
  timeout: z.number().min(1).max(300).optional().describe("Execution timeout in seconds"),
  retry_count: z.number().min(0).max(5).optional().describe("Number of retries on failure"),
});
