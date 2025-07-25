// Auto-generated TypeScript model for hook node
import { z } from 'zod';


export interface HookNodeData {

  hook_type: 'shell' | 'http' | 'python' | 'file';

  command?: string;

  url?: string;

  timeout?: number;

  retry_count?: number;

}

// Zod schema for validation
export const HookNodeDataSchema = z.object({

  hook_type: z.enum(["shell", "http", "python", "file"]),

  command: z.string().optional(),

  url: z.string().regex(/^https?:\/\//).optional(),

  timeout: z.number().min(1).max(300).optional(),

  retry_count: z.number().min(0).max(5).optional(),

});