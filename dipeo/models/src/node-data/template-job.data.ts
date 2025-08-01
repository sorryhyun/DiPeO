
import { BaseNodeData } from '../diagram';

export interface TemplateJobNodeData extends BaseNodeData {
  template_path?: string;
  template_content?: string;
  output_path?: string;
  variables?: Record<string, any>;
  engine?: 'internal' | 'jinja2' | 'handlebars';
}