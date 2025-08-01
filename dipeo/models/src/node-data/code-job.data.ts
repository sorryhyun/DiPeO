
import { BaseNodeData } from '../diagram';
import { SupportedLanguage } from '../enums';

export interface CodeJobNodeData extends BaseNodeData {
  language: SupportedLanguage;
  filePath?: string;
  code?: string;
  functionName?: string;
  timeout?: number;
}