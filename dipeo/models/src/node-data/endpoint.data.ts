/**
 * Endpoint node data interface
 */

import { BaseNodeData } from '../diagram';

export interface EndpointNodeData extends BaseNodeData {
  save_to_file: boolean;
  file_name?: string;
}