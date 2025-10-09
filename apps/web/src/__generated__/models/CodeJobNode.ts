// Auto-generated TypeScript model for code_job node
import { z } from 'zod';
import { SupportedLanguage } from '@dipeo/models';

export interface CodeJobNodeData {
  language: SupportedLanguage;
  file_path?: string | undefined;
  code?: string | undefined;
  function_name?: string | undefined;
  timeout?: number | undefined;
}

// Zod schema for validation
export const CodeJobNodeDataSchema = z.object({
  language: z.any().describe("Programming language"),
  file_path: z.string().optional().describe("Path to code file"),
  code: z.string().optional().describe("Inline code to execute (alternative to file_path)"),
  function_name: z.string().optional().describe("Function to execute"),
  timeout: z.number().optional().describe("Execution timeout in seconds"),
});
