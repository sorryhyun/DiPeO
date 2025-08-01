
import { BaseNodeData } from '../diagram';
import { HttpMethod } from '../enums';

export interface ApiJobNodeData extends BaseNodeData {
  url: string;
  method: HttpMethod;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  body?: any;
  timeout?: number;
  auth_type?: 'none' | 'bearer' | 'basic' | 'api_key';
  auth_config?: Record<string, string>;
}