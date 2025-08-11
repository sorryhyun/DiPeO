
import { BaseNodeData } from './base.js';
import { AuthType } from '../enums/integrations.js';
import { HttpMethod } from '../enums/node-specific.js';
import { JsonValue, JsonDict } from '../types/json.js';

export interface ApiJobNodeData extends BaseNodeData {
  url: string;
  method: HttpMethod;
  headers?: Record<string, string>;
  params?: JsonDict;
  body?: JsonValue;
  timeout?: number;
  auth_type?: AuthType;
  auth_config?: Record<string, string>;
}