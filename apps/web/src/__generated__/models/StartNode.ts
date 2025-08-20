// Auto-generated TypeScript model for start node
import { z } from 'zod';

export interface StartNodeData {
  trigger_mode: 'none' | 'manual' | 'hook';
  custom_data?: string;
  output_data_structure?: Record<string, any>;
  hook_event?: string;
  hook_filters?: Record<string, any>;
}

// Zod schema for validation
export const StartNodeDataSchema = z.object({
  trigger_mode: z.enum(["none", "manual", "hook"]),
  custom_data: z.string().optional(),
  output_data_structure: z.record(z.any()).optional(),
  hook_event: z.string().optional(),
  hook_filters: z.record(z.any()).optional(),
});