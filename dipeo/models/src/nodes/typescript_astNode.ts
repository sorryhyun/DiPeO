// Generated from specification: typescript_ast
import { BaseNodeData } from '../diagram';

export interface TypescriptAstNodeData extends BaseNodeData {
  source: string;
  extractPatterns?: any[];
  includeJSDoc?: boolean;
  parseMode?: 'module' | 'script';
}