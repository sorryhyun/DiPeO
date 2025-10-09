// Auto-generated TypeScript model for code_job node
import { z } from 'zod';
import { SupportedLanguage } from '@dipeo/models';

export interface CodeJobNodeData {
  language: SupportedLanguage;
  code?: string | undefined;
  function_name?: string | undefined;
}

// Zod schema for validation
export const CodeJobNodeDataSchema = z.object({
  language: z.any().describe("Programming language"),
  code: z.string().optional().describe("Inline code to execute (alternative to file_path)"),
  function_name: z.string().optional().describe("Function to execute"),
});
