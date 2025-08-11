
import { BaseNodeData } from './base.js';
import { HookTriggerMode } from '../enums/node-specific.js';
import { JsonDict } from '../types/json.js';

export interface StartNodeData extends BaseNodeData {
  trigger_mode: HookTriggerMode;
  custom_data?: Record<string, string | number | boolean>;
  output_data_structure?: Record<string, string>;
  hook_event?: string;
  hook_filters?: JsonDict;
}