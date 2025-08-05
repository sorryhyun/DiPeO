
import { BaseNodeData } from './base.js';

export interface EndpointNodeData extends BaseNodeData {
  save_to_file: boolean;
  file_name?: string;
}