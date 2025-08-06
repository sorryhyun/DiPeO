
import { BaseNodeData } from './base.js';
import { NotionOperation } from '../integration.js';

export interface NotionNodeData extends BaseNodeData {
  api_key: string;
  database_id: string;
  operation: NotionOperation;
  page_id?: string;
}