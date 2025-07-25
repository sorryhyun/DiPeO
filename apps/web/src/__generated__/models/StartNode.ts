// Auto-generated TypeScript model for start node
import { z } from 'zod';


export interface StartNodeData {

  custom_data: string;

  output_data_structure: Record<string, any>;

  trigger_mode?: 'manual' | 'hook';

  hook_event?: string;

  hook_filters?: Record<string, any>;

}

// Zod schema for validation
export const StartNodeDataSchema = z.object({

  custom_data: z.string(),

  output_data_structure: z.record(z.any()),

  trigger_mode: z.enum(["manual", "hook"]).optional(),

  hook_event: z.string().optional(),

  hook_filters: z.record(z.any()).optional(),

});