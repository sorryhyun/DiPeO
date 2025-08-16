
import { BaseNodeData } from './base.js';
import { TemplateEngine } from '../enums/node-specific.js';
import { JsonDict } from '../types/json.js';

export interface TemplateJobNodeData extends BaseNodeData {
  template_path?: string;
  template_content?: string;
  /** Single-file path; can contain template expressions */
  output_path?: string;
  /** Simple key→value map passed to template; string values are resolved */
  variables?: JsonDict;
  engine?: TemplateEngine;

  /** Render a template for each item and write many files */
  foreach?: {
    /** Array or dotted-path string to an array in inputs */
    items: unknown[] | string;
    /** Variable name to expose each item under in the template (default: "item") */
    as?: string;
    /** File path template, e.g. "dipeo/diagram_generated_staged/models/{{ item.nodeTypeSnake }}.py" */
    output_path: string;
    /** Optional: limit, parallel write hint (ignored in v1) */
    limit?: number;
  };

  /** Optional Python preprocessor that returns extra context for the template */
  preprocessor?: {
    module: string;         // e.g. "projects.codegen.code.shared.context_builders"
    function: string;       // e.g. "build_context_from_ast"
    args?: JsonDict;        // passed through as kwargs
  };
}