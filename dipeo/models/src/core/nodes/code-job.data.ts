
import { BaseNodeData } from './base.js';
import { SupportedLanguage } from '../enums/node-specific.js';

/**
 * Configuration data for CodeJob nodes that execute code
 */
export interface CodeJobNodeData extends BaseNodeData {
  /** Programming language: python, typescript, bash, or shell */
  language: SupportedLanguage;
  /** External code file path (e.g., 'files/code/processor.py') */
  filePath?: string;
  /** Inline code or path to external file */
  code?: string;
  /** Function to call in external file (required with filePath) */
  functionName?: string;
  /** Execution timeout in seconds (default: 60) */
  timeout?: number;
}