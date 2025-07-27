/**
 * Template job node data interface
 */

import { BaseNodeData } from '../diagram';

export interface TemplateJobNodeData extends BaseNodeData {
  template_path?: string;  // Path to template file
  template_content?: string;  // Inline template content
  output_path?: string;  // Where to write the rendered output
  variables?: Record<string, any>;  // Variables to pass to the template
  engine?: 'internal' | 'jinja2' | 'handlebars';  // Template engine (default: internal)
}