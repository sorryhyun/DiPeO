
import { BaseNodeData } from './base.js';
import { TemplateEngine } from '../enums/node-specific.js';

export interface TemplateJobNodeData extends BaseNodeData {
  template_path?: string;
  template_content?: string;
  output_path?: string;
  variables?: Record<string, any>;
  engine?: TemplateEngine;
}