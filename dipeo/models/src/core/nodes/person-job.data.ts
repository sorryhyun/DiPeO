
import { BaseNodeData } from './base.js';
import { PersonID, MemorySettings } from '../diagram.js';
import { MemoryProfile } from '../enums/memory.js';
import { ToolSelection } from '../enums/integrations.js';

/**
 * Configuration data for PersonJob nodes that execute LLM agents
 */
export interface PersonJobNodeData extends BaseNodeData {
  /** Reference to agent defined in 'persons' section */
  person?: PersonID;
  /** Special prompt for first iteration only, supports {{variable}} syntax */
  first_only_prompt: string;
  /** Prompt template using {{variable}} syntax for subsequent iterations */
  default_prompt?: string;
  /** External prompt file in files/prompts/ (overrides inline prompts) */
  prompt_file?: string;
  /** Maximum conversation turns (default: 1) */
  max_iteration: number;
  /** Memory profile: GOLDFISH (2 msgs), MINIMAL (5), FOCUSED (20), FULL (all) */
  memory_profile?: MemoryProfile;
  /** Advanced memory configuration when memory_profile is CUSTOM */
  memory_settings?: MemorySettings | null;
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