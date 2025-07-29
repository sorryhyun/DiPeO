/**
 * Person job node data interface
 */

import { BaseNodeData, PersonID, MemorySettings } from '../diagram';
import { MemoryProfile, ToolSelection } from '../enums';

export interface PersonJobNodeData extends BaseNodeData {
  person?: PersonID;
  first_only_prompt: string;
  default_prompt?: string;
  max_iteration: number;
  memory_profile?: MemoryProfile;  // Memory profile selection
  memory_settings?: MemorySettings | null;  // Used when memory_profile is CUSTOM
  tools?: ToolSelection;  // Tool selection
}