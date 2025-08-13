
import { BaseNodeData } from './base.js';

export interface TypescriptAstNodeData extends BaseNodeData {
  source?: string;
  extractPatterns?: string[];
  includeJSDoc?: boolean;
  parseMode?: 'module' | 'script';
  batch?: boolean;
  sources?: Record<string, string>;
  batchInputKey?: string;
}