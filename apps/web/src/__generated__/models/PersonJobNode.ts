// Auto-generated TypeScript model for person_job node
import { z } from 'zod';
import { PersonID } from '@dipeo/models';
import { PersonID } from '@dipeo/models';

export interface PersonJobNodeData {
  person?: PersonID | undefined;
  first_only_prompt?: string | undefined;
  first_prompt_file?: string | undefined;
  default_prompt?: string | undefined;
  prompt_file?: string | undefined;
  max_iteration: number;
  memorize_to?: string | undefined;
  at_most?: number | undefined;
  ignore_person?: string | undefined;
  tools?: string | undefined;
  text_format?: string | undefined;
  text_format_file?: string | undefined;
  resolved_prompt?: string | undefined;
  resolved_first_prompt?: string | undefined;
  batch?: boolean | undefined;
  batch_input_key?: string | undefined;
  batch_parallel?: boolean | undefined;
  max_concurrent?: number | undefined;
}

// Zod schema for validation
export const PersonJobNodeDataSchema = z.object({
  person: z.any().optional().describe("AI person to use for this task"),
  first_only_prompt: z.string().optional().describe("Prompt used only on first execution"),
  first_prompt_file: z.string().optional().describe("Path to prompt file in /files/prompts/"),
  default_prompt: z.string().optional().describe("Prompt template"),
  prompt_file: z.string().optional().describe("Path to prompt file in /files/prompts/"),
  max_iteration: z.number().min(1).describe("Maximum execution iterations"),
  memorize_to: z.string().optional().describe("Criteria used to select helpful messages for this task. Empty = memorize all. Special: 'GOLDFISH' for goldfish mode. Comma-separated for multiple criteria."),
  at_most: z.number().min(1).max(500).optional().describe("Select at most N messages to keep (system messages may be preserved in addition)."),
  ignore_person: z.string().optional().describe("Comma-separated list of person IDs whose messages should be excluded from memory selection."),
  tools: z.string().optional().describe("Tools available to the AI agent"),
  text_format: z.string().optional().describe("JSON schema or response format for structured outputs"),
  text_format_file: z.string().optional().describe("Path to Python file containing Pydantic models for structured outputs"),
  resolved_prompt: z.string().optional().describe("Pre-resolved prompt content from compile-time"),
  resolved_first_prompt: z.string().optional().describe("Pre-resolved first prompt content from compile-time"),
  batch: z.boolean().optional().describe("Enable batch mode for processing multiple items"),
  batch_input_key: z.string().optional().describe("Key containing the array to iterate over in batch mode"),
  batch_parallel: z.boolean().optional().describe("Execute batch items in parallel"),
  max_concurrent: z.number().min(1).max(100).optional().describe("Maximum concurrent executions in batch mode"),
});
