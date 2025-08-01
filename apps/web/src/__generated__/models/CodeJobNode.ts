







// Auto-generated TypeScript model for code_job node
import { z } from 'zod';

export interface CodeJobNodeData {
  language: 'python' | 'typescript' | 'bash' | 'shell';
  filePath: string;
  functionName?: string;
  timeout?: number;
}

// Zod schema for validation
export const CodeJobNodeDataSchema = z.object({
  language: z.any(),
  filePath: z.string(),
  functionName: z.string().optional(),
  timeout: z.number().optional(),
});