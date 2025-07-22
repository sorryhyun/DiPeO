// Generated from specification: typescript_ast
import { BaseNodeData } from './BaseNode';

export interface TypescriptAstNodeData extends BaseNodeData {
  source: string;
  extractPatterns?: any[];
  includeJSDoc?: boolean;
  parseMode?: 'module' | 'script';
}