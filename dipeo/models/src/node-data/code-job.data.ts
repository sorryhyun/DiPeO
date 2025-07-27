/**
 * Code job node data interface
 */

import { BaseNodeData } from '../diagram';
import { SupportedLanguage } from '../enums';

export interface CodeJobNodeData extends BaseNodeData {
  language: SupportedLanguage;
  filePath?: string;  // Path to code file (required if code is not provided)
  code?: string;      // Inline code (required if filePath is not provided)
  functionName?: string;  // Function to call (default: 'main' for Python)
  timeout?: number;  // in seconds
}