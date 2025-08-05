
import { BaseNodeData } from './base.js';
import { PersonID, MemorySettings } from '../diagram.js';
import { MemoryProfile } from '../enums/memory.js';
import { ToolSelection } from '../enums/integrations.js';

export interface PersonJobNodeData extends BaseNodeData {
  person?: PersonID;
  first_only_prompt: string;
  default_prompt?: string;
  prompt_file?: string;
  max_iteration: number;
  memory_profile?: MemoryProfile;
  memory_settings?: MemorySettings | null;
  tools?: ToolSelection;
  batch?: boolean;
  batch_input_key?: string;
  batch_parallel?: boolean;
  max_concurrent?: number;
}