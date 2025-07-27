/**
 * Person job node data interface
 */

import { BaseNodeData, PersonID, MemorySettings, ToolConfig } from '../diagram';

export interface PersonJobNodeData extends BaseNodeData {
  person?: PersonID;
  first_only_prompt: string;
  default_prompt?: string;
  max_iteration: number;
  memory_settings?: MemorySettings | null;  // New unified memory configuration
  tools?: ToolConfig[] | null;
}