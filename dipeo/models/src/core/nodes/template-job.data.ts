
import { BaseNodeData } from './base.js';
import { TemplateEngine } from '../enums/node-specific.js';
import { JsonDict } from '../types/json.js';

export interface TemplateJobNodeData extends BaseNodeData {
  template_path?: string;
  template_content?: string;
  output_path?: string;
  variables?: JsonDict;
  engine?: TemplateEngine;
}