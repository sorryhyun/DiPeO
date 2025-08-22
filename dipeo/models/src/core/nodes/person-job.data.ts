
import { BaseNodeData } from './base.js';
import { PersonID } from '../diagram.js';
import { ToolSelection } from '../enums/integrations.js';

/**
 * Configuration data for PersonJob nodes that execute LLM agents
 */
export interface PersonJobNodeData extends BaseNodeData {
  /** Reference to agent defined in 'persons' section */
  person?: PersonID;
  /** Special prompt for first iteration only, supports {{variable}} syntax */
  first_only_prompt: string;
  /** External prompt file for first iteration only (overrides first_only_prompt) */
  first_prompt_file?: string;
  /** Prompt template using {{variable}} syntax for subsequent iterations */
  default_prompt?: string;
  /** External prompt file in files/prompts/ (overrides inline prompts) */
  prompt_file?: string;
  /** Maximum conversation turns (default: 1) */
  max_iteration: number;

  memorize_to: string;
  at_most: number;

  /** LLM tools to enable (web_search_preview, etc.) */
  tools?: ToolSelection;
  /** Pydantic model name for structured output */
  text_format?: string;
  /** External Python file with Pydantic models (overrides text_format) */
  text_format_file?: string;
  /** Enable batch processing for arrays */
  batch?: boolean;
  /** Array variable name for batch processing */
  batch_input_key?: string;
  /** Execute batch items in parallel */
  batch_parallel?: boolean;
  /** Maximum concurrent batch executions */
  max_concurrent?: number;
}