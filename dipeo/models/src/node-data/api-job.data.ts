
import { BaseNodeData } from '../diagram';
import { HttpMethod, AuthType } from '../enums';

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