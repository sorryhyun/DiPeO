
import { BaseNodeData } from './base.js';
import { SupportedLanguage } from '../enums/node-specific.js';

export interface CodeJobNodeData extends BaseNodeData {
  language: SupportedLanguage;
  filePath?: string;
  code?: string;
  functionName?: string;
  timeout?: number;
}