/**
 * TypeScript AST node data interface
 */

import { BaseNodeData } from '../diagram';

export interface TypescriptAstNodeData extends BaseNodeData {
  source?: string;  // TypeScript source code to parse
  extractPatterns?: string[];  // Patterns to extract (e.g., 'interface', 'type', 'enum', 'class', 'function', 'const', 'export')
  includeJSDoc?: boolean;  // Include JSDoc comments in the extracted data
  parseMode?: 'module' | 'script';  // TypeScript parsing mode
}