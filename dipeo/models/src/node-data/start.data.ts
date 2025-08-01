
import { BaseNodeData } from '../diagram';
import { HookTriggerMode } from '../enums';

export interface StartNodeData extends BaseNodeData {
  trigger_mode: HookTriggerMode;
  custom_data?: Record<string, string | number | boolean>;
  output_data_structure?: Record<string, string>;
  hook_event?: string;
  hook_filters?: Record<string, any>;
}