
import { BaseNodeData, PersonID, MemorySettings } from '../diagram';
import { MemoryProfile, ToolSelection } from '../enums';

export interface PersonJobNodeData extends BaseNodeData {
  person?: PersonID;
  first_only_prompt: string;
  default_prompt?: string;
  max_iteration: number;
  memory_profile?: MemoryProfile;
  memory_settings?: MemorySettings | null;
  tools?: ToolSelection;
}