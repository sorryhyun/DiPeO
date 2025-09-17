// Auto-generated TypeScript model for code_job node
import { z } from 'zod';
import { SupportedLanguage } from '@dipeo/models';

export interface CodeJobNodeData {
  language: SupportedLanguage;
  filePath?: string | undefined;
  code?: string | undefined;
  functionName?: string | undefined;
  timeout?: number | undefined;
}

// Zod schema for validation
export const CodeJobNodeDataSchema = z.object({
  language: z.any().describe("Programming language"),
  filePath: z.string().optional().describe("Path to code file"),
  code: z.string().optional().describe("Inline code to execute (alternative to filePath)"),
  functionName: z.string().optional().describe("Function to execute"),
  timeout: z.number().optional().describe("Execution timeout in seconds"),
});
