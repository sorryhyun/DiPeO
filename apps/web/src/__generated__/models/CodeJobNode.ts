// Auto-generated TypeScript model for code_job node
import { z } from 'zod';

export interface CodeJobNodeData {
  language: 'python' | 'typescript' | 'bash' | 'shell';
  filePath?: string;
  code?: string;
  functionName?: string;
  timeout?: number;
}

// Zod schema for validation
export const CodeJobNodeDataSchema = z.object({
  language: z.enum(["python", "typescript", "bash", "shell"]),
  filePath: z.string().optional(),
  code: z.string().optional(),
  functionName: z.string().optional(),
  timeout: z.number().optional(),
});