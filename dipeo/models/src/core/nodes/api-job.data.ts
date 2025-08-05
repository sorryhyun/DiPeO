
import { BaseNodeData } from './base.js';
import { AuthType } from '../enums/integrations.js';
import { HttpMethod } from '../enums/node-specific.js';

export interface ApiJobNodeData extends BaseNodeData {
  url: string;
  method: HttpMethod;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  body?: any;
  timeout?: number;
  auth_type?: AuthType;
  auth_config?: Record<string, string>;
}