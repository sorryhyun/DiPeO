
import { BaseNodeData } from '../diagram';
import { TemplateEngine } from '../enums';

export interface TemplateJobNodeData extends BaseNodeData {
  template_path?: string;
  template_content?: string;
  output_path?: string;
  variables?: Record<string, any>;
  engine?: TemplateEngine;
}