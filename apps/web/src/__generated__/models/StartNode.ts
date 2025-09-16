// Auto-generated TypeScript model for start node
import { z } from 'zod';

export interface StartNodeData {
  trigger_mode?: enum | undefined;
  custom_data?: any | undefined;
  output_data_structure?: Record<string, any> | undefined;
  hook_event?: string | undefined;
  hook_filters?: Record<string, any> | undefined;
}

// Zod schema for validation
export const StartNodeDataSchema = z.object({
  trigger_mode: z.any().optional().describe("How this start node is triggered"),
  custom_data: z.any().optional().describe("Custom data to pass when manually triggered"),
  output_data_structure: z.record(z.any()).optional().describe("Expected output data structure"),
  hook_event: z.string().optional().describe("Event name to listen for"),
  hook_filters: z.record(z.any()).optional().describe("Filters to apply to incoming events"),
});
